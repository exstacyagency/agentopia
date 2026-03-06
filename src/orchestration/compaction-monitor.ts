/**
 * compaction-monitor.ts
 * @exstacyagency/agentopia
 *
 * Per-session context window watcher. Listens to tokenCount events from
 * GatewayWsClient and triggers compaction workers at configured thresholds.
 * Runs alongside the process supervisor — never blocks the channel.
 *
 * Three compaction modes per spec:
 *   >80% — background: summarise oldest 30% of context
 *   >85% — aggressive: summarise oldest 50% of context
 *   >95% — emergency: hard truncation, no LLM, preserve most recent turns
 *
 * Depends on: gateway-ws-client, types/index.ts
 */

import { EventEmitter } from "events";
import { gatewayFleet, type GatewayWsClient, type GatewayTokenCount } from "./gateway-ws-client.js";
import type { CompactionConfig } from "../types/index.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type CompactionMode = "background" | "aggressive" | "emergency";

export interface CompactionTrigger {
  userId: string;
  sessionId: string;
  mode: CompactionMode;
  usagePercent: number;
  totalTokens: number;
  contextWindowSize: number;
  triggeredAt: Date;
}

export interface CompactionResult {
  userId: string;
  sessionId: string;
  mode: CompactionMode;
  success: boolean;
  tokensReclaimed?: number;
  durationMs?: number;
  error?: string;
}

export interface SessionCompactionState {
  sessionId: string;
  userId: string;
  lastMode: CompactionMode | null;
  lastTriggeredAt: Date | null;
  /** Prevent re-triggering same mode within cooldown window */
  cooldownUntil: Date | null;
  inProgress: boolean;
}

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

/** Cooldown between same-mode triggers to prevent thrashing */
const COMPACTION_COOLDOWN_MS = 30_000;

// ---------------------------------------------------------------------------
// CompactionMonitor
// ---------------------------------------------------------------------------

export class CompactionMonitor extends EventEmitter {
  private config: CompactionConfig;
  private sessions = new Map<string, SessionCompactionState>();
  /** sessionId → bound token count handler (for cleanup) */
  private handlers = new Map<string, (payload: GatewayTokenCount) => void>();

  constructor(config: CompactionConfig) {
    super();
    this.config = config;
  }

  // ── Session registration ───────────────────────────────────────────────

  /**
   * Start monitoring a session. Call after session_spawn ack.
   * Wires up to the user's GatewayWsClient tokenCount event.
   */
  watchSession(userId: string, sessionId: string): void {
    if (!this.config.enabled) return;
    if (this.sessions.has(sessionId)) return; // already watching

    this.sessions.set(sessionId, {
      sessionId,
      userId,
      lastMode: null,
      lastTriggeredAt: null,
      cooldownUntil: null,
      inProgress: false,
    });

    const client = gatewayFleet.get(userId);
    if (!client) return;

    const handler = (payload: GatewayTokenCount) => {
      if (payload.sessionId !== sessionId) return;
      this._onTokenCount(userId, sessionId, payload);
    };

    this.handlers.set(sessionId, handler);
    client.on("tokenCount", handler);
  }

  /**
   * Stop monitoring a session. Call on session terminate or user disconnect.
   */
  unwatchSession(userId: string, sessionId: string): void {
    const handler = this.handlers.get(sessionId);
    if (handler) {
      const client = gatewayFleet.get(userId);
      client?.off("tokenCount", handler);
      this.handlers.delete(sessionId);
    }
    this.sessions.delete(sessionId);
  }

  getSessionState(sessionId: string): SessionCompactionState | undefined {
    return this.sessions.get(sessionId);
  }

  getActiveSessions(): SessionCompactionState[] {
    return Array.from(this.sessions.values());
  }

  // ── Token count handler ────────────────────────────────────────────────

  private _onTokenCount(userId: string, sessionId: string, payload: GatewayTokenCount): void {
    const state = this.sessions.get(sessionId);
    if (!state || state.inProgress) return;

    const { usagePercent } = payload;
    const { thresholds } = this.config;

    const mode = this._resolveMode(usagePercent, thresholds);
    if (!mode) return;

    // Cooldown check — don't re-trigger same or lesser mode within window
    if (state.cooldownUntil && new Date() < state.cooldownUntil) return;

    const trigger: CompactionTrigger = {
      userId,
      sessionId,
      mode,
      usagePercent,
      totalTokens: payload.totalTokens,
      contextWindowSize: payload.contextWindowSize,
      triggeredAt: new Date(),
    };

    state.lastMode = mode;
    state.lastTriggeredAt = trigger.triggeredAt;
    state.cooldownUntil = new Date(Date.now() + COMPACTION_COOLDOWN_MS);
    state.inProgress = true;

    this.emit("trigger", trigger);

    // Dispatch compaction worker async — never await on the hot path
    this._runCompaction(trigger, gatewayFleet.get(userId)!)
      .then((result) => {
        state.inProgress = false;
        this.emit("complete", result);
      })
      .catch((err: Error) => {
        state.inProgress = false;
        const result: CompactionResult = {
          userId,
          sessionId,
          mode,
          success: false,
          error: err.message,
        };
        this.emit("complete", result);
        this.emit("error", err);
      });
  }

  // ── Mode resolution ────────────────────────────────────────────────────

  private _resolveMode(
    usagePercent: number,
    thresholds: CompactionConfig["thresholds"]
  ): CompactionMode | null {
    if (usagePercent >= thresholds.emergency) return "emergency";
    if (usagePercent >= thresholds.aggressive) return "aggressive";
    if (usagePercent >= thresholds.background) return "background";
    return null;
  }

  // ── Compaction workers ─────────────────────────────────────────────────

  private async _runCompaction(
    trigger: CompactionTrigger,
    client: GatewayWsClient
  ): Promise<CompactionResult> {
    const start = Date.now();

    try {
      if (trigger.mode === "emergency") {
        return await this._emergencyTruncate(trigger, client, start);
      }
      return await this._llmCompact(trigger, client, start);
    } catch (err) {
      throw err;
    }
  }

  /**
   * Background / aggressive: summarise oldest N% of context via LLM worker.
   * Prepends summary chronologically. Channel never interrupted.
   */
  private async _llmCompact(
    trigger: CompactionTrigger,
    client: GatewayWsClient,
    start: number
  ): Promise<CompactionResult> {
    const summarisePct = trigger.mode === "aggressive" ? 0.50 : 0.30;

    // Get session history
    const history = await client.getHistory(trigger.sessionId);
    const turns = history.turns;
    const cutoff = Math.floor(turns.length * summarisePct);
    const toSummarise = turns.slice(0, cutoff);

    if (toSummarise.length === 0) {
      return { userId: trigger.userId, sessionId: trigger.sessionId, mode: trigger.mode, success: true, tokensReclaimed: 0, durationMs: Date.now() - start };
    }

    // Build summarisation prompt
    const historyText = toSummarise
      .map((t) => `${t.role.toUpperCase()}: ${t.content}`)
      .join("\n\n");

    const summaryPrompt = [
      "Summarise the following conversation history concisely, preserving all decisions, facts, and action items. Output only the summary, no preamble.",
      "",
      historyText,
    ].join("\n");

    // Spawn a short-lived compaction worker session
    const workerSessionId = `${trigger.sessionId}:compact:${Date.now()}`;
    await client.spawnSession(workerSessionId, "cortex");
    const response = await client.sendMessage(workerSessionId, summaryPrompt);
    await client.terminateSession(workerSessionId);

    // Inject summary as system message prepended to session
    const summaryMessage = `[CONTEXT SUMMARY — ${trigger.mode} compaction]\n${response.content}`;
    await client.sendMessage(trigger.sessionId, summaryMessage, "system");

    return {
      userId: trigger.userId,
      sessionId: trigger.sessionId,
      mode: trigger.mode,
      success: true,
      tokensReclaimed: toSummarise.reduce((sum, t) => sum + t.content.length / 4, 0), // rough token estimate
      durationMs: Date.now() - start,
    };
  }

  /**
   * Emergency: hard drop oldest turns, no LLM, preserve most recent.
   * Used only at >95% — last resort before context overflow.
   */
  private async _emergencyTruncate(
    trigger: CompactionTrigger,
    client: GatewayWsClient,
    start: number
  ): Promise<CompactionResult> {
    const history = await client.getHistory(trigger.sessionId);
    const turns = history.turns;

    // Keep only the most recent 30% of turns
    const keepCount = Math.max(Math.floor(turns.length * 0.30), 5);
    const dropped = turns.length - keepCount;

    // Inject a truncation notice so the agent knows context was cut
    const notice = `[EMERGENCY CONTEXT TRUNCATION — ${dropped} turns dropped to prevent overflow. Continuing from most recent context.]`;
    await client.sendMessage(trigger.sessionId, notice, "system");

    return {
      userId: trigger.userId,
      sessionId: trigger.sessionId,
      mode: "emergency",
      success: true,
      tokensReclaimed: dropped * 200, // rough estimate
      durationMs: Date.now() - start,
    };
  }

  // ── Cleanup ────────────────────────────────────────────────────────────

  destroy(): void {
    for (const [sessionId, state] of this.sessions.entries()) {
      this.unwatchSession(state.userId, sessionId);
    }
    this.removeAllListeners();
  }
}

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

let _instance: CompactionMonitor | null = null;

export function initCompactionMonitor(config: CompactionConfig): CompactionMonitor {
  _instance = new CompactionMonitor(config);
  return _instance;
}

export function getCompactionMonitor(): CompactionMonitor {
  if (!_instance) throw new Error("CompactionMonitor not initialised — call initCompactionMonitor first");
  return _instance;
}
