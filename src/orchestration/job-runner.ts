/**
 * job-runner.ts
 * @exstacyagency/agentopia
 *
 * Turn lifecycle manager. Tracks every running turn from dispatch to
 * completion, enforces timeouts, handles retries, and settles billing
 * after job completion.
 *
 * One JobRunner instance per platform process. Holds a Map of all
 * in-flight turns. Process supervisor calls checkTimeouts() on a cron.
 *
 * Depends on: billing (consumeReservation, releaseReservation),
 *             gateway-ws-client, types/index.ts
 */

import { EventEmitter } from "events";
import { randomUUID } from "crypto";
import { consumeReservation, releaseReservation } from "../billing/quota-reservation.js";
import { calculateActualCost } from "../billing/pricing-catalog.js";
import { prisma } from "../lib/prisma.js";
import type { RunningTurn, JobStatus, JobTypeRegistry } from "../types/index.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface StartTurnInput {
  userId: string;
  agentSlot: string;
  sessionId: string;
  jobType: string;
  timeoutSeconds: number;
  reservationId: string | null;
  modelUsed: string;
  domain: string;
}

export interface CompleteTurnInput {
  turnId: string;
  inputTokens: number;
  outputTokens: number;
  finishReason: string;
}

export interface FailTurnInput {
  turnId: string;
  error: string;
  retryable?: boolean;
}

export interface TurnRecord extends RunningTurn {
  reservationId: string | null;
  modelUsed: string;
  domain: string;
  completedAt: Date | null;
  failureReason: string | null;
}

export interface JobRunnerEvents {
  started: (turn: TurnRecord) => void;
  completed: (turn: TurnRecord) => void;
  failed: (turn: TurnRecord) => void;
  timedOut: (turn: TurnRecord) => void;
  retrying: (turn: TurnRecord, attempt: number) => void;
  settled: (turnId: string, creditsConsumed: number) => void;
  error: (err: Error) => void;
}

declare interface JobRunner {
  on<K extends keyof JobRunnerEvents>(event: K, listener: JobRunnerEvents[K]): this;
  emit<K extends keyof JobRunnerEvents>(event: K, ...args: Parameters<JobRunnerEvents[K]>): boolean;
}

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const MAX_RETRY_ATTEMPTS = 2;
const DEAD_LETTER_AFTER_RETRIES = 3;

// ---------------------------------------------------------------------------
// JobRunner
// ---------------------------------------------------------------------------

class JobRunner extends EventEmitter {
  private turns = new Map<string, TurnRecord>();
  private jobRegistry: JobTypeRegistry;

  constructor(jobRegistry: JobTypeRegistry) {
    super();
    this.jobRegistry = jobRegistry;
  }

  // ── Turn lifecycle ─────────────────────────────────────────────────────

  startTurn(input: StartTurnInput): TurnRecord {
    const turn: TurnRecord = {
      id: randomUUID(),
      userId: input.userId,
      agentSlot: input.agentSlot,
      sessionId: input.sessionId,
      jobType: input.jobType,
      startedAt: new Date(),
      timeoutSeconds: input.timeoutSeconds,
      status: "running",
      retryCount: 0,
      reservationId: input.reservationId,
      modelUsed: input.modelUsed,
      domain: input.domain,
      completedAt: null,
      failureReason: null,
    };

    this.turns.set(turn.id, turn);
    this._persistStatus(turn).catch((err) => this.emit("error", err));
    this.emit("started", turn);
    return turn;
  }

  async completeTurn(input: CompleteTurnInput): Promise<void> {
    const turn = this._require(input.turnId);
    turn.status = "completed";
    turn.completedAt = new Date();

    this.turns.delete(turn.id);
    await this._persistStatus(turn);
    this.emit("completed", turn);

    // Settle billing async
    this._settle(turn, input.inputTokens, input.outputTokens).catch((err) =>
      this.emit("error", err)
    );
  }

  async failTurn(input: FailTurnInput): Promise<void> {
    const turn = this._require(input.turnId);
    turn.failureReason = input.error;

    const shouldRetry = (input.retryable ?? true) && turn.retryCount < MAX_RETRY_ATTEMPTS;

    if (shouldRetry) {
      turn.retryCount++;
      turn.status = "pending";
      this.emit("retrying", turn, turn.retryCount);
      await this._persistStatus(turn);
      return;
    }

    turn.status = turn.retryCount >= DEAD_LETTER_AFTER_RETRIES ? "dead_letter" : "failed";
    turn.completedAt = new Date();
    this.turns.delete(turn.id);

    await this._persistStatus(turn);
    await this._releaseOnFailure(turn);
    this.emit("failed", turn);
  }

  // ── Timeout enforcement ────────────────────────────────────────────────

  /**
   * Called by process supervisor on a short cron (e.g. every 10s).
   * Marks timed-out turns as failed and releases reservations.
   */
  async checkTimeouts(): Promise<{ timedOut: string[] }> {
    const now = Date.now();
    const timedOut: string[] = [];

    for (const turn of this.turns.values()) {
      if (turn.status !== "running") continue;
      const elapsed = (now - turn.startedAt.getTime()) / 1000;
      if (elapsed > turn.timeoutSeconds) {
        turn.status = "failed";
        turn.failureReason = `Timeout after ${turn.timeoutSeconds}s`;
        turn.completedAt = new Date();
        this.turns.delete(turn.id);
        timedOut.push(turn.id);

        await this._persistStatus(turn).catch(() => {});
        await this._releaseOnFailure(turn).catch(() => {});
        this.emit("timedOut", turn);
      }
    }

    return { timedOut };
  }

  // ── Queries ────────────────────────────────────────────────────────────

  getRunningTurns(): TurnRecord[] {
    return Array.from(this.turns.values()).filter((t) => t.status === "running");
  }

  getTurn(turnId: string): TurnRecord | undefined {
    return this.turns.get(turnId);
  }

  getRunningCountForUser(userId: string): number {
    return Array.from(this.turns.values()).filter(
      (t) => t.userId === userId && t.status === "running"
    ).length;
  }

  // ── Internal ───────────────────────────────────────────────────────────

  private _require(turnId: string): TurnRecord {
    const turn = this.turns.get(turnId);
    if (!turn) throw new Error(`JobRunner: turn ${turnId} not found`);
    return turn;
  }

  private async _settle(
    turn: TurnRecord,
    inputTokens: number,
    outputTokens: number
  ): Promise<void> {
    if (!turn.reservationId) return;

    try {
      const cost = calculateActualCost(
        turn.jobType,
        turn.modelUsed,
        turn.domain,
        { inputTokens, outputTokens }
      );

      await consumeReservation(turn.reservationId);

      this.emit("settled", turn.id, cost.actualCredits);
    } catch (err) {
      // Settlement failure is non-fatal — log, alert, don't crash
      this.emit("error", new Error(`JobRunner: settlement failed for turn ${turn.id}: ${(err as Error).message}`));
    }
  }

  private async _releaseOnFailure(turn: TurnRecord): Promise<void> {
    if (!turn.reservationId) return;
    await releaseReservation(turn.reservationId).catch(() => {});
  }

  private async _persistStatus(turn: TurnRecord): Promise<void> {
    await prisma.runningTurn.upsert({
      where: { id: turn.id },
      create: {
        id:             turn.id,
        userId:         turn.userId,
        agentSlot:      turn.agentSlot,
        sessionId:      turn.sessionId,
        jobType:        turn.jobType,
        startedAt:      turn.startedAt,
        timeoutSeconds: turn.timeoutSeconds,
        status:         turn.status,
        retryCount:     turn.retryCount,
      },
      update: {
        status:      turn.status,
        retryCount:  turn.retryCount,
        updatedAt:   new Date(),
      },
    });
  }
}

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

let _instance: JobRunner | null = null;

export function initJobRunner(jobRegistry: JobTypeRegistry): JobRunner {
  _instance = new JobRunner(jobRegistry);
  return _instance;
}

export function getJobRunner(): JobRunner {
  if (!_instance) throw new Error("JobRunner not initialised — call initJobRunner first");
  return _instance;
}

export { JobRunner };
