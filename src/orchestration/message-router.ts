/**
 * message-router.ts
 * @exstacyagency/agentopia
 *
 * Inbound message interception layer. Every message from every channel passes
 * through here before touching a Gateway. Three responsibilities:
 *
 *   1. Coalesce buffer  — debounce multi-part messages within a window
 *   2. Complexity score — route light/standard/heavy before dispatch
 *   3. Ack layer        — immediate Haiku ack (<2s) then async job dispatch
 *
 * Depends on: gateway-ws-client, complexity-scorer, billing (spend-cap,
 * quota-reservation), types/index.ts
 */

import { EventEmitter } from "events";
import { randomUUID } from "crypto";

import { gatewayFleet, type GatewayWsClient } from "./gateway-ws-client.js";
import { scoreComplexity, type ComplexityScore } from "./complexity-scorer.js";
import { assertUnderSpendCap } from "../billing/spend-cap.js";
import { CreditDomain } from "../billing/credit-ledger.js";
import { reserveCredits, releaseReservation, InsufficientCreditsError } from "../billing/quota-reservation.js";
import type { JobTypeRegistry, RoutingConfig, Platform } from "../types/index.js";

// ---------------------------------------------------------------------------
// Inbound message shape (from channel broker or built-in chat)
// ---------------------------------------------------------------------------

export interface InboundMessage {
  /** Internal routing ID — set by broker, not user-visible */
  routeId: string;
  userId: string;
  platform: Platform | "chat";
  platformUserId: string;
  platformChannelId: string;
  content: string;
  /** Unix ms. Used for coalesce ordering. */
  receivedAt: number;
  /** DM sessions bypass coalescing per spec */
  isDm: boolean;
}

// ---------------------------------------------------------------------------
// Coalesced turn — what exits the buffer
// ---------------------------------------------------------------------------

export interface CoalescedTurn {
  turnId: string;
  userId: string;
  platform: Platform | "chat";
  platformChannelId: string;
  /** Merged content from all coalesced messages, joined with newline */
  content: string;
  /** Raw messages in arrival order */
  messages: InboundMessage[];
  complexity: ComplexityScore;
  complexityConfidence: number;
  receivedAt: number;
  isDm: boolean;
}

// ---------------------------------------------------------------------------
// Dispatch result — emitted after ack + job routing
// ---------------------------------------------------------------------------

export interface DispatchResult {
  turnId: string;
  userId: string;
  jobId: string;
  jobType: string | null;
  agentSlot: string | null;
  complexity: ComplexityScore;
  reservationId: string | null;
  status: "dispatched" | "rejected_spend_cap" | "rejected_no_credits" | "rejected_no_client";
  rejectionReason?: string;
}

// ---------------------------------------------------------------------------
// Router config
// ---------------------------------------------------------------------------

export interface MessageRouterConfig {
  routing: RoutingConfig;
  jobRegistry: JobTypeRegistry;
  /** Called to send an immediate ack back to the originating channel */
  ackSender: (userId: string, platformChannelId: string, platform: Platform | "chat", message: string) => Promise<void>;
  /** Called after coalescing to determine which job type to dispatch */
  jobResolver: (turn: CoalescedTurn) => string | null;
  /** Estimated credits to reserve per job type (domain → amount) */
  creditEstimator: (jobType: string | null, domain: string | null) => number;
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

export class MessageRouter extends EventEmitter {
  /** userId → pending messages in coalesce window */
  private buffer = new Map<string, InboundMessage[]>();
  /** userId → debounce timer handle */
  private timers = new Map<string, NodeJS.Timeout>();

  private readonly config: MessageRouterConfig;

  constructor(config: MessageRouterConfig) {
    super();
    this.config = config;
  }

  // ── Public entry point ─────────────────────────────────────────────────

  /**
   * Accept an inbound message from any channel. Returns immediately.
   * Ack and dispatch happen asynchronously.
   */
  accept(msg: InboundMessage): void {
    if (msg.isDm) {
      // DM sessions bypass coalescing — flush immediately as single-message turn
      this._flush(msg.userId, [msg]);
      return;
    }

    const pending = this.buffer.get(msg.userId) ?? [];
    pending.push(msg);
    this.buffer.set(msg.userId, pending);

    // Reset debounce timer
    const existing = this.timers.get(msg.userId);
    if (existing) clearTimeout(existing);

    const timer = setTimeout(() => {
      const messages = this.buffer.get(msg.userId) ?? [];
      this.buffer.delete(msg.userId);
      this.timers.delete(msg.userId);
      if (messages.length > 0) this._flush(msg.userId, messages);
    }, this.config.routing.coalesceWindowMs);

    this.timers.set(msg.userId, timer);
  }

  // ── Internal: coalesce → score → ack → dispatch ────────────────────────

  private _flush(userId: string, messages: InboundMessage[]): void {
    // Merge content in arrival order
    const merged = messages.map((m) => m.content).join("\n").trim();
    const first = messages[0];

    const { score, confidence } = scoreComplexity(merged);

    const turn: CoalescedTurn = {
      turnId: randomUUID(),
      userId,
      platform: first.platform,
      platformChannelId: first.platformChannelId,
      content: merged,
      messages,
      complexity: score,
      complexityConfidence: confidence,
      receivedAt: first.receivedAt,
      isDm: first.isDm,
    };

    this.emit("turn", turn);

    // Fire-and-forget — ack + dispatch run async, channel never blocks
    this._processAsync(turn).catch((err) => {
      this.emit("error", err);
    });
  }

  private async _processAsync(turn: CoalescedTurn): Promise<void> {
    const { userId, platformChannelId, platform, complexity } = turn;

    // 1. Immediate ack via Haiku acknowledgment message
    await this._sendAck(userId, platformChannelId, platform, complexity).catch(() => {
      // Ack failure is non-fatal — log and continue
      this.emit("ackFailed", turn);
    });

    // 2. Resolve job type from turn content
    const jobType = this.config.jobResolver(turn);
    const jobDef = jobType ? this.config.jobRegistry.get(jobType) : null;
    const domain = jobDef?.domain ?? null;
    const agentSlot = jobDef?.agent ?? null;
    const jobId = randomUUID();
    const estimatedCredits = domain
      ? this.config.creditEstimator(jobType, domain)
      : 0;

    // 3. Spend cap check
    try {
      if (domain) await assertUnderSpendCap(userId, domain as CreditDomain, estimatedCredits);
    } catch {
      const result: DispatchResult = {
        turnId: turn.turnId,
        userId,
        jobId,
        jobType,
        agentSlot,
        complexity,
        reservationId: null,
        status: "rejected_spend_cap",
        rejectionReason: "Monthly spend cap reached",
      };
      this.emit("dispatch", result);
      return;
    }

    // 4. Credit reservation
    let reservationId: string | null = null;
    if (domain) {
      try {
        const reservation = await reserveCredits({
          userId,
          jobId,
          jobType: jobType ?? "UNKNOWN",
          domain: domain as CreditDomain,
          estimatedCredits,
        });
        reservationId = reservation.id;
      } catch (err) {
        if (err instanceof InsufficientCreditsError) {
          const result: DispatchResult = {
            turnId: turn.turnId,
            userId,
            jobId,
            jobType,
            agentSlot,
            complexity,
            reservationId: null,
            status: "rejected_no_credits",
            rejectionReason: `Insufficient credits in ${domain} domain`,
          };
          this.emit("dispatch", result);
          return;
        }
        throw err;
      }
    }

    // 5. Get gateway client for this user
    const client = gatewayFleet.get(userId);
    if (!client || !client.isConnected) {
      // Release reservation if we bailed
      if (reservationId) await releaseReservation(reservationId).catch(() => {});
      const result: DispatchResult = {
        turnId: turn.turnId,
        userId,
        jobId,
        jobType,
        agentSlot,
        complexity,
        reservationId: null,
        status: "rejected_no_client",
        rejectionReason: "User container not connected",
      };
      this.emit("dispatch", result);
      return;
    }

    // 6. Dispatch to agent via Gateway
    await this._dispatchToGateway(client, turn, agentSlot ?? "orchestrator");

    const result: DispatchResult = {
      turnId: turn.turnId,
      userId,
      jobId,
      jobType,
      agentSlot,
      complexity,
      reservationId,
      status: "dispatched",
    };
    this.emit("dispatch", result);
  }

  // ── Ack ────────────────────────────────────────────────────────────────

  private async _sendAck(
    userId: string,
    platformChannelId: string,
    platform: Platform | "chat",
    complexity: ComplexityScore
  ): Promise<void> {
    const ackMessages: Record<ComplexityScore, string> = {
      light: "On it.",
      standard: "Got it — working on this now.",
      heavy: "Got it — this will take a moment, working on it now.",
    };
    await this.config.ackSender(userId, platformChannelId, platform, ackMessages[complexity]);
  }

  // ── Gateway dispatch ───────────────────────────────────────────────────

  private async _dispatchToGateway(
    client: GatewayWsClient,
    turn: CoalescedTurn,
    agentSlot: string
  ): Promise<void> {
    // Orchestrator is always the entry point — it routes internally to workers
    const sessionId = `${turn.userId}:${agentSlot}`;
    await client.sendMessage(sessionId, turn.content);
  }

  // ── Cleanup ────────────────────────────────────────────────────────────

  /** Flush all pending buffers immediately (e.g. on graceful shutdown) */
  flushAll(): void {
    for (const [userId, messages] of this.buffer.entries()) {
      const timer = this.timers.get(userId);
      if (timer) clearTimeout(timer);
      this.timers.delete(userId);
      this.buffer.delete(userId);
      if (messages.length > 0) this._flush(userId, messages);
    }
  }

  destroy(): void {
    for (const timer of this.timers.values()) clearTimeout(timer);
    this.timers.clear();
    this.buffer.clear();
    this.removeAllListeners();
  }
}

// ---------------------------------------------------------------------------
// Events reference (for consumers)
// ---------------------------------------------------------------------------
//
// router.on("turn", (turn: CoalescedTurn) => ...)
//   — fired after coalescing, before ack. Use for logging/observability.
//
// router.on("dispatch", (result: DispatchResult) => ...)
//   — fired after ack + dispatch attempt. Always fires, check result.status.
//
// router.on("ackFailed", (turn: CoalescedTurn) => ...)
//   — ack send failed (non-fatal). Log and alert.
//
// router.on("error", (err: Error) => ...)
//   — unexpected async error in processing pipeline.
