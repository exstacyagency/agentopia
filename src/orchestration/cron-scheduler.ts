/**
 * @exstacyagency/agentopia
 * src/orchestration/cron-scheduler.ts
 *
 * Scheduled job runner. Executes platform maintenance jobs on fixed
 * intervals: memory decay, archive sweep, hard-delete, container
 * heartbeat checks, and job-runner timeout enforcement.
 *
 * Features:
 *   - Per-job circuit breaker (opens after N consecutive failures)
 *   - Active-hours window guard (skips heavy jobs outside allowed hours)
 *   - CronJob table persistence (last run, next run, status, error)
 *   - Graceful shutdown — drains in-flight jobs before exit
 *
 * Depends on: lib/prisma.ts, memory/memory-store.ts, orchestration/job-runner.ts
 */

import { randomUUID }              from "crypto";
import { prisma }                  from "../lib/prisma.js";
import { applyDecay, archiveSweep, hardDeleteExpiredArchives } from "../memory/memory-store.js";
import { getJobRunner }            from "./job-runner.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type CronJobStatus = "idle" | "running" | "failed" | "disabled";

export interface CronJobDefinition {
  /** Unique stable identifier — persisted to cron_jobs table */
  id:              string;
  /** Human label for logs / admin UI */
  name:            string;
  /** Interval in milliseconds */
  intervalMs:      number;
  /** Job handler. Must resolve or throw — never hang. */
  handler:         () => Promise<void>;
  /** If true, job is skipped outside activeHoursUtc window */
  respectActiveHours: boolean;
  /** Max consecutive failures before circuit opens. Default: 3 */
  maxFailures?:    number;
  /** After circuit opens, cool-down before retry. Default: 5 min */
  cooldownMs?:     number;
}

export interface ActiveHoursConfig {
  /** UTC hour to start running heavy jobs (inclusive). e.g. 2 = 02:00 UTC */
  startHour: number;
  /** UTC hour to stop running heavy jobs (exclusive). e.g. 6 = 06:00 UTC */
  endHour:   number;
}

export interface CronSchedulerConfig {
  /** From AgentPlatformConfig.cron */
  enabled:      boolean;
  activeHours?: ActiveHoursConfig;
}

interface JobState {
  def:              CronJobDefinition;
  timer:            NodeJS.Timeout | null;
  consecutiveFails: number;
  circuitOpen:      boolean;
  circuitOpenAt:    number;
  running:          boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_MAX_FAILURES = 3;
const DEFAULT_COOLDOWN_MS  = 5 * 60 * 1_000; // 5 min
const DEFAULT_ACTIVE_HOURS: ActiveHoursConfig = { startHour: 2, endHour: 6 };

// ---------------------------------------------------------------------------
// Built-in job IDs
// ---------------------------------------------------------------------------

export const CRON_JOB_IDS = {
  MEMORY_DECAY:       "memory_decay",
  ARCHIVE_SWEEP:      "archive_sweep",
  HARD_DELETE:        "hard_delete",
  TIMEOUT_CHECK:      "job_timeout_check",
  HEARTBEAT_CHECK:    "container_heartbeat_check",
} as const;

// ---------------------------------------------------------------------------
// CronScheduler
// ---------------------------------------------------------------------------

export class CronScheduler {
  private jobs    = new Map<string, JobState>();
  private cfg:    Required<CronSchedulerConfig>;
  private started = false;

  constructor(config: CronSchedulerConfig) {
    this.cfg = {
      enabled:     config.enabled,
      activeHours: config.activeHours ?? DEFAULT_ACTIVE_HOURS,
    };
  }

  // ── Lifecycle ──────────────────────────────────────────────────────────

  /** Register all built-in jobs and start the scheduler. */
  start(): void {
    if (!this.cfg.enabled) {
      console.log("[CronScheduler] disabled — skipping start");
      return;
    }
    if (this.started) return;
    this.started = true;

    this._registerBuiltins();

    for (const state of this.jobs.values()) {
      this._scheduleNext(state);
    }

    console.log(`[CronScheduler] started — ${this.jobs.size} jobs registered`);
  }

  /** Register an additional job at runtime (e.g. from plugin). */
  register(def: CronJobDefinition): void {
    if (this.jobs.has(def.id)) {
      console.warn(`[CronScheduler] job ${def.id} already registered — ignoring`);
      return;
    }

    const state: JobState = {
      def,
      timer:            null,
      consecutiveFails: 0,
      circuitOpen:      false,
      circuitOpenAt:    0,
      running:          false,
    };

    this.jobs.set(def.id, state);

    if (this.started && this.cfg.enabled) {
      this._scheduleNext(state);
    }
  }

  /** Register or replace a named handler (used by scheduler-integrated modules). */
  registerHandler(jobType: string, handler: () => Promise<void>): void {
    const existing = this.jobs.get(jobType);
    if (existing) {
      existing.def.handler = handler;
      return;
    }

    this.register({
      id: jobType,
      name: jobType,
      intervalMs: 60_000,
      respectActiveHours: false,
      handler,
    });
  }

  /** Disable a registered job without restarting the scheduler. */
  disable(jobId: string): void {
    const state = this.jobs.get(jobId);
    if (!state) return;
    if (state.timer) {
      clearTimeout(state.timer);
      state.timer = null;
    }
    void this._upsertRecord(jobId, state.def.name, "disabled", null);
    console.log(`[CronScheduler] job ${jobId} disabled`);
  }

  /** Re-enable a previously disabled job. */
  enable(jobId: string): void {
    const state = this.jobs.get(jobId);
    if (!state || state.timer) return;
    state.circuitOpen      = false;
    state.consecutiveFails = 0;
    this._scheduleNext(state);
    console.log(`[CronScheduler] job ${jobId} re-enabled`);
  }

  /**
   * Graceful shutdown.
   * Clears all timers. In-flight jobs run to completion (up to drainMs).
   */
  async shutdown(drainMs = 10_000): Promise<void> {
    for (const state of this.jobs.values()) {
      if (state.timer) {
        clearTimeout(state.timer);
        state.timer = null;
      }
    }

    const deadline = Date.now() + drainMs;
    while (Date.now() < deadline) {
      const anyRunning = [...this.jobs.values()].some((s) => s.running);
      if (!anyRunning) break;
      await _sleep(200);
    }

    console.log("[CronScheduler] shutdown complete");
  }

  // ── Scheduling ─────────────────────────────────────────────────────────

  private _scheduleNext(state: JobState): void {
    if (state.timer) clearTimeout(state.timer);

    state.timer = setTimeout(() => {
      void this._runJob(state);
    }, state.def.intervalMs);
  }

  // ── Execution ──────────────────────────────────────────────────────────

  private async _runJob(state: JobState): Promise<void> {
    const { def } = state;

    // Circuit breaker: check cool-down expiry
    if (state.circuitOpen) {
      const cooldown = def.cooldownMs ?? DEFAULT_COOLDOWN_MS;
      if (Date.now() - state.circuitOpenAt < cooldown) {
        console.warn(`[CronScheduler] ${def.id} circuit open — skipping`);
        this._scheduleNext(state);
        return;
      }
      // Cool-down elapsed — attempt recovery
      state.circuitOpen = false;
      console.log(`[CronScheduler] ${def.id} circuit recovering`);
    }

    // Active-hours guard
    if (def.respectActiveHours && !this._inActiveHours()) {
      this._scheduleNext(state);
      return;
    }

    if (state.running) {
      // Previous run still in flight — skip this tick
      this._scheduleNext(state);
      return;
    }

    state.running = true;
    const startMs = Date.now();

    await this._upsertRecord(def.id, def.name, "running", null);
    console.log(`[CronScheduler] ${def.id} running`);

    try {
      await def.handler();

      state.consecutiveFails = 0;
      state.circuitOpen      = false;

      await this._upsertRecord(def.id, def.name, "idle", null);
      console.log(`[CronScheduler] ${def.id} done in ${Date.now() - startMs}ms`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      state.consecutiveFails++;

      const maxFails = def.maxFailures ?? DEFAULT_MAX_FAILURES;
      if (state.consecutiveFails >= maxFails) {
        state.circuitOpen   = true;
        state.circuitOpenAt = Date.now();
        console.error(
          `[CronScheduler] ${def.id} circuit opened after ${state.consecutiveFails} failures`
        );
      } else {
        console.error(
          `[CronScheduler] ${def.id} failed (${state.consecutiveFails}/${maxFails}): ${msg}`
        );
      }

      await this._upsertRecord(def.id, def.name, "failed", msg);
    } finally {
      state.running = false;
      this._scheduleNext(state);
    }
  }

  // ── Active-hours guard ─────────────────────────────────────────────────

  private _inActiveHours(): boolean {
    const { startHour, endHour } = this.cfg.activeHours;
    const nowHour = new Date().getUTCHours();

    if (startHour <= endHour) {
      return nowHour >= startHour && nowHour < endHour;
    }
    // Wraps midnight (e.g. 22:00–04:00)
    return nowHour >= startHour || nowHour < endHour;
  }

  // ── CronJob table persistence ──────────────────────────────────────────

  private async _upsertRecord(
    id:     string,
    name:   string,
    status: CronJobStatus,
    error:  string | null
  ): Promise<void> {
    try {
      await (prisma as any).cronJob.upsert({
        where:  { id },
        create: {
          id,
          name,
          status,
          lastError:  error,
          lastRunAt:  status === "running" ? new Date() : undefined,
          lastDoneAt: status === "idle"    ? new Date() : undefined,
        },
        update: {
          name,
          status,
          lastError:  error,
          lastRunAt:  status === "running" ? new Date() : undefined,
          lastDoneAt: status === "idle"    ? new Date() : undefined,
        },
      });
    } catch (err) {
      // Non-fatal — don't let DB write failures kill the scheduler
      console.warn(`[CronScheduler] failed to persist cron record ${id}:`, err);
    }
  }

  // ── Built-in job registration ──────────────────────────────────────────

  private _registerBuiltins(): void {
    // Memory decay — nightly, active-hours only
    this.register({
      id:                 CRON_JOB_IDS.MEMORY_DECAY,
      name:               "Memory importance decay",
      intervalMs:         24 * 60 * 60 * 1_000,
      respectActiveHours: true,
      handler:            () => this._runMemoryDecay(),
    });

    // Archive sweep — nightly, active-hours only
    this.register({
      id:                 CRON_JOB_IDS.ARCHIVE_SWEEP,
      name:               "Memory archive sweep",
      intervalMs:         24 * 60 * 60 * 1_000,
      respectActiveHours: true,
      handler:            () => this._runArchiveSweep(),
    });

    // Hard delete — weekly, active-hours only
    this.register({
      id:                 CRON_JOB_IDS.HARD_DELETE,
      name:               "Memory hard delete (expired archives)",
      intervalMs:         7 * 24 * 60 * 60 * 1_000,
      respectActiveHours: true,
      handler:            () => this._runHardDelete(),
    });

    // Job timeout checker — every 10 seconds, always runs
    this.register({
      id:                 CRON_JOB_IDS.TIMEOUT_CHECK,
      name:               "Job runner timeout enforcement",
      intervalMs:         10_000,
      respectActiveHours: false,
      maxFailures:        10, // more tolerant — this is critical path
      handler:            () => this._runTimeoutCheck(),
    });

    // Container heartbeat checker — every 60 seconds, always runs
    this.register({
      id:                 CRON_JOB_IDS.HEARTBEAT_CHECK,
      name:               "Container heartbeat check",
      intervalMs:         60_000,
      respectActiveHours: false,
      handler:            () => this._runHeartbeatCheck(),
    });
  }

  // ── Built-in handlers ──────────────────────────────────────────────────

  /** Apply importance decay to all active users' memories. */
  private async _runMemoryDecay(): Promise<void> {
    const users = await _getActiveUserIds();
    let totalUpdated = 0;

    for (const userId of users) {
      const { updated } = await applyDecay(userId);
      totalUpdated += updated;
    }

    console.log(`[CronScheduler] memory_decay — ${totalUpdated} records updated across ${users.length} users`);
  }

  /** Soft-archive sub-threshold memories for all active users. */
  private async _runArchiveSweep(): Promise<void> {
    const users = await _getActiveUserIds();
    let totalArchived = 0;

    for (const userId of users) {
      const { archived } = await archiveSweep(userId);
      totalArchived += archived;
    }

    console.log(`[CronScheduler] archive_sweep — ${totalArchived} records archived across ${users.length} users`);
  }

  /** Hard-delete memories archived >30 days ago. */
  private async _runHardDelete(): Promise<void> {
    const users = await _getActiveUserIds();
    let totalDeleted = 0;

    for (const userId of users) {
      const { deleted } = await hardDeleteExpiredArchives(userId);
      totalDeleted += deleted;
    }

    console.log(`[CronScheduler] hard_delete — ${totalDeleted} records purged across ${users.length} users`);
  }

  /** Enforce job-runner turn timeouts. */
  private async _runTimeoutCheck(): Promise<void> {
    const runner = getJobRunner();
    const { timedOut } = await runner.checkTimeouts();
    if (timedOut.length > 0) {
      console.log(`[CronScheduler] timeout_check — expired turns: ${timedOut.join(", ")}`);
    }
  }

  /** Check container heartbeats and flag stale containers. */
  private async _runHeartbeatCheck(): Promise<void> {
    const staleThresholdMs = 90_000; // 90 seconds — 1.5× the 60s heartbeat interval
    const cutoff = new Date(Date.now() - staleThresholdMs);

    const stale = await prisma.containerRecord.findMany({
      where: {
        status:          { not: "stopped" },
        lastHeartbeatAt: { lt: cutoff },
      },
      select: { id: true, userId: true, missedHeartbeats: true },
    });

    if (stale.length === 0) return;

    for (const container of stale) {
      const missed = container.missedHeartbeats + 1;

      await prisma.containerRecord.update({
        where: { id: container.id },
        data:  {
          missedHeartbeats: missed,
          status:           missed >= 3 ? "unresponsive" : undefined,
        },
      });

      if (missed >= 3) {
        console.warn(
          `[CronScheduler] container ${container.id} uid=${container.userId} marked unresponsive (${missed} missed heartbeats)`
        );
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function _getActiveUserIds(): Promise<string[]> {
  // Active = has at least one non-stopped container
  const containers = await prisma.containerRecord.findMany({
    where:  { status: { not: "stopped" } },
    select: { userId: true },
    distinct: ["userId"],
  });
  return containers.map((c: { userId: string }) => c.userId);
}

function _sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

let _instance: CronScheduler | null = null;

export function initCronScheduler(config: CronSchedulerConfig): CronScheduler {
  _instance = new CronScheduler(config);
  return _instance;
}

export function getCronScheduler(): CronScheduler {
  if (!_instance) throw new Error("CronScheduler not initialised — call initCronScheduler first");
  return _instance;
}
