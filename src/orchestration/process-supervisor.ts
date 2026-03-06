/**
 * process-supervisor.ts
 * @exstacyagency/agentopia
 *
 * Top-level cron coordinator. Runs on a single Node.js setInterval loop
 * per process. Owns all scheduled maintenance tasks:
 *
 *   Every 10s  — job timeout enforcement
 *   Every 60s  — container heartbeat check
 *   Every 60s  — memory decay + archive sweep (staggered 30s after heartbeat)
 *   Every 24h  — hard delete expired archives
 *
 * Designed to run in the platform process — not a separate worker.
 * All tasks are non-overlapping: a task skipped if previous run still active.
 *
 * Depends on: job-runner, user-provisioner, memory-store, types/index.ts
 */

import { EventEmitter } from "events";
import { getJobRunner } from "./job-runner.js";
import { checkHeartbeats } from "../provisioning/user-provisioner.js";
import { applyDecay, archiveSweep, hardDeleteExpiredArchives } from "../memory/memory-store.js";
import { prisma } from "../lib/prisma.js";
import type { CronConfig, DecayConfig } from "../types/index.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SupervisorConfig {
  cron: CronConfig;
  decayConfig: DecayConfig;
}

export interface TaskRunResult {
  task: string;
  startedAt: Date;
  durationMs: number;
  success: boolean;
  error?: string;
  meta?: Record<string, unknown>;
}

export interface SupervisorEvents {
  taskComplete: (result: TaskRunResult) => void;
  taskError: (task: string, err: Error) => void;
  started: () => void;
  stopped: () => void;
}

declare interface ProcessSupervisor {
  on<K extends keyof SupervisorEvents>(event: K, listener: SupervisorEvents[K]): this;
  emit<K extends keyof SupervisorEvents>(event: K, ...args: Parameters<SupervisorEvents[K]>): boolean;
}

// ---------------------------------------------------------------------------
// Intervals
// ---------------------------------------------------------------------------

const TIMEOUT_CHECK_INTERVAL_MS  = 10_000;   // 10s
const HEARTBEAT_INTERVAL_MS      = 60_000;   // 60s
const DECAY_INTERVAL_MS          = 60_000;   // 60s (staggered 30s after heartbeat)
const HARD_DELETE_INTERVAL_MS    = 86_400_000; // 24h

// ---------------------------------------------------------------------------
// ProcessSupervisor
// ---------------------------------------------------------------------------

class ProcessSupervisor extends EventEmitter {
  private config: SupervisorConfig;
  private timers: NodeJS.Timeout[] = [];
  private running = false;

  /** Guards per-task — prevents overlap if a task runs slow */
  private inProgress = new Set<string>();

  constructor(config: SupervisorConfig) {
    super();
    this.config = config;
  }

  // ── Lifecycle ──────────────────────────────────────────────────────────

  start(): void {
    if (!this.config.cron.enabled) return;
    if (this.running) return;
    this.running = true;

    // Job timeout check — every 10s
    this.timers.push(
      setInterval(() => this._run("timeout_check", () => this._timeoutCheck()), TIMEOUT_CHECK_INTERVAL_MS)
    );

    // Heartbeat check — every 60s
    this.timers.push(
      setInterval(() => this._run("heartbeat_check", () => this._heartbeatCheck()), HEARTBEAT_INTERVAL_MS)
    );

    // Memory decay + archive sweep — every 60s, staggered 30s
    this.timers.push(
      setTimeout(() => {
        this._run("memory_decay", () => this._memoryDecay());
        this.timers.push(
          setInterval(() => this._run("memory_decay", () => this._memoryDecay()), DECAY_INTERVAL_MS)
        );
      }, 30_000)
    );

    // Hard delete expired archives — every 24h
    this.timers.push(
      setInterval(() => this._run("hard_delete", () => this._hardDelete()), HARD_DELETE_INTERVAL_MS)
    );

    this.emit("started");
  }

  stop(): void {
    for (const timer of this.timers) {
      clearInterval(timer);
      clearTimeout(timer);
    }
    this.timers = [];
    this.running = false;
    this.emit("stopped");
  }

  get isRunning(): boolean {
    return this.running;
  }

  // ── Task runner ────────────────────────────────────────────────────────

  private async _run(
    name: string,
    task: () => Promise<Record<string, unknown>>
  ): Promise<void> {
    if (this.inProgress.has(name)) return; // skip overlapping run
    this.inProgress.add(name);

    const startedAt = new Date();
    try {
      const meta = await task();
      const result: TaskRunResult = {
        task: name,
        startedAt,
        durationMs: Date.now() - startedAt.getTime(),
        success: true,
        meta,
      };
      this.emit("taskComplete", result);
    } catch (err) {
      const error = err as Error;
      const result: TaskRunResult = {
        task: name,
        startedAt,
        durationMs: Date.now() - startedAt.getTime(),
        success: false,
        error: error.message,
      };
      this.emit("taskComplete", result);
      this.emit("taskError", name, error);
    } finally {
      this.inProgress.delete(name);
    }
  }

  // ── Tasks ──────────────────────────────────────────────────────────────

  private async _timeoutCheck(): Promise<Record<string, unknown>> {
    const runner = getJobRunner();
    const { timedOut } = await runner.checkTimeouts();
    return { timedOut: timedOut.length };
  }

  private async _heartbeatCheck(): Promise<Record<string, unknown>> {
    const { alerted } = await checkHeartbeats();
    return { alerted: alerted.length };
  }

  private async _memoryDecay(): Promise<Record<string, unknown>> {
    // Get all active user IDs — decay runs per-user
    const users = await prisma.containerRecord.findMany({
      where:  { status: "ACTIVE" },
      select: { userId: true },
    });

    let totalDecayed = 0;
    let totalArchived = 0;

    await Promise.all(
      users.map(async ({ userId }: { userId: string }) => {
        try {
          const decayed = await applyDecay(userId, this.config.decayConfig);
          totalDecayed += decayed.updated;
          const swept = await archiveSweep(userId);
          totalArchived += swept.archived;
        } catch {
          // Per-user failure is non-fatal — log via taskError on next wrap
        }
      })
    );

    return { users: users.length, decayed: totalDecayed, archived: totalArchived };
  }

  private async _hardDelete(): Promise<Record<string, unknown>> {
    const users = await prisma.containerRecord.findMany({
      where:  { status: { not: "DESTROYED" } },
      select: { userId: true },
    });

    let totalDeleted = 0;
    await Promise.all(
      users.map(async ({ userId }: { userId: string }) => {
        try {
          const { deleted } = await hardDeleteExpiredArchives(userId);
          totalDeleted += deleted;
        } catch {
          // non-fatal
        }
      })
    );

    return { users: users.length, deleted: totalDeleted };
  }
}

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

let _instance: ProcessSupervisor | null = null;

export function initProcessSupervisor(config: SupervisorConfig): ProcessSupervisor {
  _instance = new ProcessSupervisor(config);
  return _instance;
}

export function getProcessSupervisor(): ProcessSupervisor {
  if (!_instance) throw new Error("ProcessSupervisor not initialised — call initProcessSupervisor first");
  return _instance;
}

export { ProcessSupervisor };
