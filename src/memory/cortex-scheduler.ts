/**
 * @exstacyagency/agentopia
 * src/memory/cortex-scheduler.ts
 *
 * Cross-session Cortex scheduling layer. Wraps CortexExtractor and drives
 * execution on each cron cycle. Manages per-user run state: prevents
 * overlapping runs, tracks last-run timestamps, exposes status for the
 * Cortex tab UI.
 *
 * Registration with CronScheduler:
 *   cortexScheduler.register(cronScheduler);
 *
 * CronScheduler then calls the registered "cortex_cycle" handler.
 * Default cadence pulled from PlatformConfig.cron.
 *
 * Depends on: cortex-extractor, cron-scheduler, prisma, types/index.ts
 */

import { EventEmitter }  from "events";
import { prisma }         from "../lib/prisma.js";
import {
  CortexExtractor,
  type CortexRunResult,
  type CortexExtractorConfig,
  type GatewayClientLike,
} from "./cortex-extractor.js";
import type { CronScheduler } from "../orchestration/cron-scheduler.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CortexSchedulerConfig {
  extractorConfig: CortexExtractorConfig;
  /** How many users may run concurrently. Default: 3 */
  maxConcurrent?:  number;
  /** Min interval before re-running same user (ms). Default: 6h */
  minIntervalMs?:  number;
  /** Factory: returns per-slot gateway clients for a userId */
  gatewayFactory:  (userId: string) => Map<string, GatewayClientLike>;
  /** Registered memory domains for extraction context */
  domains:         string[];
}

interface UserRunState {
  inProgress: boolean;
  lastRunAt:  Date | null;
  lastResult: CortexRunResult | null;
}

export interface UserCortexStatus {
  userId:         string;
  lastRunAt:      Date | null;
  lastResult:     CortexRunResult | null;
  inProgress:     boolean;
  totalMemories?: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_MAX_CONCURRENT = 3;
const DEFAULT_MIN_INTERVAL   = 6 * 60 * 60 * 1_000; // 6 hours

// ---------------------------------------------------------------------------
// CortexScheduler
// ---------------------------------------------------------------------------

export class CortexScheduler extends EventEmitter {
  private extractor:      CortexExtractor;
  private maxConcurrent:  number;
  private minIntervalMs:  number;
  private gatewayFactory: CortexSchedulerConfig["gatewayFactory"];
  private domains:        string[];

  /** userId → run state */
  private runState   = new Map<string, UserRunState>();
  private activeRuns = 0;

  constructor(config: CortexSchedulerConfig) {
    super();
    this.extractor      = new CortexExtractor(config.extractorConfig);
    this.maxConcurrent  = config.maxConcurrent ?? DEFAULT_MAX_CONCURRENT;
    this.minIntervalMs  = config.minIntervalMs ?? DEFAULT_MIN_INTERVAL;
    this.gatewayFactory = config.gatewayFactory;
    this.domains        = config.domains;
  }

  // ── CronScheduler integration ─────────────────────────────────────────

  /**
   * Register the cortex_cycle handler with an existing CronScheduler.
   * CronScheduler drives cadence — no internal timer needed here.
   */
  register(cron: CronScheduler): void {
    cron.registerHandler("cortex_cycle", async () => {
      await this.tick();
    });
  }

  /**
   * One tick: load eligible users and dispatch up to maxConcurrent runs.
   * Called by CronScheduler on each cortex_cycle invocation.
   */
  async tick(): Promise<void> {
    const eligible = await this._getEligibleUsers();
    const slots    = Math.max(0, this.maxConcurrent - this.activeRuns);
    const batch    = eligible.slice(0, slots);

    for (const userId of batch) {
      this._runUser(userId).catch((err) => this.emit("error", userId, err));
    }
  }

  // ── Manual trigger (settings/cortex UI) ──────────────────────────────

  /**
   * Force an immediate run for a specific user, bypassing min-interval.
   */
  async runNow(userId: string): Promise<CortexRunResult> {
    const state = this._stateFor(userId);
    if (state.inProgress) {
      throw new Error(`Cortex run already in progress for user ${userId}`);
    }
    return this._runUser(userId);
  }

  // ── Status (Cortex tab UI) ────────────────────────────────────────────

  async getStatus(userId: string): Promise<UserCortexStatus> {
    const state = this._stateFor(userId);

    const totalMemories = await prisma.memoryRecord.count({
      where: { userId, archived: false },
    });

    return {
      userId,
      lastRunAt:   state.lastRunAt,
      lastResult:  state.lastResult,
      inProgress:  state.inProgress,
      totalMemories,
    };
  }

  // ── Internal ──────────────────────────────────────────────────────────

  private async _runUser(userId: string): Promise<CortexRunResult> {
    const state = this._stateFor(userId);
    state.inProgress = true;
    this.activeRuns++;
    this.emit("start", userId);

    try {
      const clients = this.gatewayFactory(userId);
      const result  = await this.extractor.run(userId, clients, this.domains);

      state.lastRunAt  = new Date();
      state.lastResult = result;

      await this._persistLastRun(userId, state.lastRunAt, result);

      this.emit("complete", userId, result);
      return result;

    } catch (err) {
      this.emit("error", userId, err);
      throw err;

    } finally {
      state.inProgress = false;
      this.activeRuns  = Math.max(0, this.activeRuns - 1);
    }
  }

  private async _getEligibleUsers(): Promise<string[]> {
    const users = await prisma.memoryRecord.findMany({
      where:    { archived: false },
      select:   { userId: true },
      distinct: ["userId"],
    }) as Array<{ userId: string }>;

    const eligible: string[] = [];

    for (const { userId } of users) {
      const state = this._stateFor(userId);
      if (state.inProgress) continue;

      const lastRun = state.lastRunAt?.getTime() ?? 0;
      if (Date.now() - lastRun < this.minIntervalMs) continue;

      eligible.push(userId);
    }

    return eligible;
  }

  private async _persistLastRun(
    userId: string,
    runAt:  Date,
    result: CortexRunResult,
  ): Promise<void> {
    try {
      await prisma.$executeRawUnsafe(
        `INSERT INTO "CortexRunLog"
           ("userId", "runAt", "memoriesCreated", "edgesWritten", "patternsFound", "durationMs")
         VALUES ($1, $2, $3, $4, $5, $6)
         ON CONFLICT ("userId") DO UPDATE SET
           "runAt"           = EXCLUDED."runAt",
           "memoriesCreated" = EXCLUDED."memoriesCreated",
           "edgesWritten"    = EXCLUDED."edgesWritten",
           "patternsFound"   = EXCLUDED."patternsFound",
           "durationMs"      = EXCLUDED."durationMs"`,
        userId,
        runAt,
        result.memoriesCreated,
        result.edgesWritten,
        result.patternsFound,
        result.durationMs,
      );
    } catch {
      // CortexRunLog may not exist until migration — non-fatal
    }
  }

  private _stateFor(userId: string): UserRunState {
    if (!this.runState.has(userId)) {
      this.runState.set(userId, { inProgress: false, lastRunAt: null, lastResult: null });
    }
    return this.runState.get(userId)!;
  }
}

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

let _instance: CortexScheduler | null = null;

export function initCortexScheduler(config: CortexSchedulerConfig): CortexScheduler {
  _instance = new CortexScheduler(config);
  return _instance;
}

export function getCortexScheduler(): CortexScheduler {
  if (!_instance) throw new Error("CortexScheduler not initialised — call initCortexScheduler first");
  return _instance;
}
