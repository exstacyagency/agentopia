/**
 * @exstacyagency/agentopia
 * src/platform.ts
 *
 * Platform factory. Single call-site that wires all singletons in
 * dependency order and returns a typed handle.
 *
 * This is a library — callers own the process and SIGTERM handling.
 * Pattern:
 *
 *   import { createPlatform } from "@exstacyagency/agentopia";
 *
 *   const platform = await createPlatform(config);
 *   platform.start();
 *
 *   process.on("SIGTERM", () => platform.shutdown());
 *
 * Init order (each step depends on the previous):
 *   1. Job registry build         — pure, no I/O
 *   2. registerJobTypes()         — injects registry into pricing-catalog
 *   3. initModelRouter()          — key pool rotation + failover
 *   4. initJobRunner()            — turn lifecycle, needs job registry
 *   5. initCompactionMonitor()    — context compaction, needs nothing
 *   6. initCronScheduler()        — scheduled maintenance, needs job runner
 *   7. cron.start()               — arms timers (separated so tests can skip)
 *
 * Depends on: all singleton init functions, types/index.ts
 */

import type { AgentPlatformConfig, JobTypeDefinition, RegisteredJobType, JobTypeRegistry } from "./types/index.js";
import { registerJobTypes }       from "./billing/pricing-catalog.js";
import { initModelRouter }        from "./models/model-router.js";
import { initJobRunner }          from "./orchestration/job-runner.js";
import { initCompactionMonitor }  from "./orchestration/compaction-monitor.js";
import { initCronScheduler }      from "./orchestration/cron-scheduler.js";

// ---------------------------------------------------------------------------
// Public handle
// ---------------------------------------------------------------------------

export interface AgentPlatform {
  /** Arms cron timers. Safe to call multiple times — idempotent. */
  start(): void;
  /**
   * Graceful shutdown.
   * Stops cron scheduler, drains in-flight jobs.
   * @param drainMs max milliseconds to wait for in-flight cron jobs. Default 10000.
   */
  shutdown(drainMs?: number): Promise<void>;
  /** Read-only view of the resolved job registry. */
  readonly jobRegistry: JobTypeRegistry;
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/**
 * Wire all platform singletons in dependency order.
 * Synchronous — no I/O at init time (Prisma connects lazily on first query).
 *
 * Call `platform.start()` after to arm cron timers.
 */
export function createPlatform(cfg: AgentPlatformConfig): AgentPlatform {
  // ── 1. Build job registry ──────────────────────────────────────────────
  const jobRegistry = _buildJobRegistry(cfg.jobs);

  // ── 2. Inject registry into pricing-catalog ────────────────────────────
  registerJobTypes(jobRegistry);

  // ── 3. Model router (key pool + failover) ──────────────────────────────
  initModelRouter(cfg.anthropicKeyPool);

  // ── 4. Job runner (turn lifecycle + timeout enforcement) ───────────────
  initJobRunner(jobRegistry);

  // ── 5. Compaction monitor (context window management) ──────────────────
  initCompactionMonitor(cfg.compaction);

  // ── 6. Cron scheduler (maintenance jobs) ───────────────────────────────
  const cron = initCronScheduler({ enabled: cfg.cron.enabled });

  // ── 7. Return handle ───────────────────────────────────────────────────
  return {
    jobRegistry,

    start(): void {
      cron.start();
    },

    async shutdown(drainMs = 10_000): Promise<void> {
      await cron.shutdown(drainMs);
    },
  };
}

// ---------------------------------------------------------------------------
// Job registry builder
// Converts JobTypeDefinition[] (flat config) → Map<id, RegisteredJobType>
// ---------------------------------------------------------------------------

function _buildJobRegistry(defs: JobTypeDefinition[]): JobTypeRegistry {
  const registry = new Map<string, RegisteredJobType>();

  for (const def of defs) {
    const registered: RegisteredJobType = {
      id:      def.id,
      domain:  def.domain,
      agent:   def.agentSlot,
      timeout: def.timeoutSeconds,
    };
    registry.set(def.id, registered);
  }

  return registry;
}
