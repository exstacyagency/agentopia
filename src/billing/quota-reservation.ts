/**
 * @exstacyagency/agentopia
 * src/billing/quota-reservation.ts
 *
 * Reserve-and-rollback pattern for in-flight job spend.
 * Holds an estimated credit amount against a user's balance for the
 * duration of job execution. Released (rolled back) or consumed
 * (settled via credit-ledger) when the job completes or fails.
 *
 * Depends on: Prisma client, billing/credit-ledger.ts, types/index.ts
 */

import { prisma } from "../lib/prisma";
import { getBalance, CreditDomain } from "./credit-ledger";

// ---------------------------------------------------------------------------
// Enums & Types
// ---------------------------------------------------------------------------

export enum ReservationStatus {
  ACTIVE    = "ACTIVE",    // credits held, job in flight
  RELEASED  = "RELEASED",  // job failed / cancelled — hold lifted, no charge
  CONSUMED  = "CONSUMED",  // job completed — settlement fired, hold closed
  EXPIRED   = "EXPIRED",   // job exceeded timeout — supervisor releases hold
}

export interface CreditReservation {
  id:               string;
  userId:           string;
  jobId:            string;
  jobType:          string;
  domain:           CreditDomain;
  estimatedCredits: number;       // amount held upfront
  status:           ReservationStatus;
  createdAt:        Date;
  resolvedAt:       Date | null;
}

export interface ReserveCreditsInput {
  userId:           string;
  jobId:            string;
  jobType:          string;
  domain:           CreditDomain;
  estimatedCredits: number;
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class InsufficientCreditsError extends Error {
  constructor(
    public readonly userId: string,
    public readonly domain: CreditDomain,
    public readonly available: number,
    public readonly required: number
  ) {
    super(
      `Insufficient credits for user ${userId} in domain ${domain}: ` +
      `required ${required}, available ${available} (after active reservations)`
    );
    this.name = "InsufficientCreditsError";
  }
}

export class ReservationNotFoundError extends Error {
  constructor(public readonly reservationId: string) {
    super(`Reservation not found: ${reservationId}`);
    this.name = "ReservationNotFoundError";
  }
}

export class ReservationAlreadyResolvedError extends Error {
  constructor(
    public readonly reservationId: string,
    public readonly currentStatus: ReservationStatus
  ) {
    super(
      `Reservation ${reservationId} is already resolved (status: ${currentStatus})`
    );
    this.name = "ReservationAlreadyResolvedError";
  }
}

// ---------------------------------------------------------------------------
// Active Reservation Helpers
// ---------------------------------------------------------------------------

/**
 * Sum of all ACTIVE reservations for a user in a domain.
 * This is the "in-flight hold" that must be subtracted from the
 * ledger balance to get the true available balance.
 */
export async function getActiveReservationTotal(
  userId: string,
  domain: CreditDomain
): Promise<number> {
  const result = await prisma.creditReservation.aggregate({
    where: {
      userId,
      domain,
      status: ReservationStatus.ACTIVE,
    },
    _sum: { estimatedCredits: true },
  });
  return result._sum.estimatedCredits ?? 0;
}

/**
 * Available balance = ledger balance minus active reservation holds.
 * Use this — not getBalance() — whenever deciding whether to allow a job.
 */
export async function getAvailableBalance(
  userId: string,
  domain: CreditDomain
): Promise<number> {
  const [ledgerBalance, heldCredits] = await Promise.all([
    getBalance(userId, domain),
    getActiveReservationTotal(userId, domain),
  ]);
  return ledgerBalance - heldCredits;
}

// ---------------------------------------------------------------------------
// Reserve
// ---------------------------------------------------------------------------

/**
 * Place a hold on estimated credits for an in-flight job.
 * Throws InsufficientCreditsError if available balance < estimatedCredits.
 *
 * Called by the job runner immediately before dispatching work to the agent.
 * The spend-cap check (assertUnderSpendCap) must pass before calling this.
 */
export async function reserveCredits(
  input: ReserveCreditsInput
): Promise<CreditReservation> {
  const { userId, jobId, jobType, domain, estimatedCredits } = input;

  if (estimatedCredits <= 0) {
    throw new Error(
      `reserveCredits: estimatedCredits must be positive (got ${estimatedCredits})`
    );
  }

  const available = await getAvailableBalance(userId, domain);

  if (available < estimatedCredits) {
    throw new InsufficientCreditsError(userId, domain, available, estimatedCredits);
  }

  const reservation = await prisma.creditReservation.create({
    data: {
      userId,
      jobId,
      jobType,
      domain,
      estimatedCredits,
      status:     ReservationStatus.ACTIVE,
      createdAt:  new Date(),
      resolvedAt: null,
    },
  });

  return reservation as CreditReservation;
}

// ---------------------------------------------------------------------------
// Release (rollback — job failed, cancelled, or timed out)
// ---------------------------------------------------------------------------

/**
 * Release an ACTIVE reservation without charging the user.
 * Called when a job fails, is cancelled by the user, or is killed
 * by the process supervisor after timeout.
 *
 * Does NOT write a ledger event — the hold simply lifts.
 */
export async function releaseReservation(
  reservationId: string
): Promise<CreditReservation> {
  const existing = await prisma.creditReservation.findUnique({
    where: { id: reservationId },
  });

  if (!existing) {
    throw new ReservationNotFoundError(reservationId);
  }

  if (existing.status !== ReservationStatus.ACTIVE) {
    throw new ReservationAlreadyResolvedError(
      reservationId,
      existing.status as ReservationStatus
    );
  }

  const updated = await prisma.creditReservation.update({
    where: { id: reservationId },
    data: {
      status:     ReservationStatus.RELEASED,
      resolvedAt: new Date(),
    },
  });

  return updated as CreditReservation;
}

// ---------------------------------------------------------------------------
// Consume (settlement path — job completed successfully)
// ---------------------------------------------------------------------------

/**
 * Mark a reservation CONSUMED after job settlement fires.
 * Called by the job runner immediately after settleJobCost() succeeds.
 *
 * The reservation hold is lifted here. The actual deduction already
 * happened in the ledger via settleJobCost().
 */
export async function consumeReservation(
  reservationId: string
): Promise<CreditReservation> {
  const existing = await prisma.creditReservation.findUnique({
    where: { id: reservationId },
  });

  if (!existing) {
    throw new ReservationNotFoundError(reservationId);
  }

  if (existing.status !== ReservationStatus.ACTIVE) {
    throw new ReservationAlreadyResolvedError(
      reservationId,
      existing.status as ReservationStatus
    );
  }

  const updated = await prisma.creditReservation.update({
    where: { id: reservationId },
    data: {
      status:     ReservationStatus.CONSUMED,
      resolvedAt: new Date(),
    },
  });

  return updated as CreditReservation;
}

// ---------------------------------------------------------------------------
// Expiry (process supervisor path — timeout killed job)
// ---------------------------------------------------------------------------

/**
 * Expire a reservation that was never resolved because the job
 * exceeded its timeout and was promoted to dead letter.
 * Functionally the same as release (no charge) but logged separately
 * so the admin portal can surface timeout-related credit events.
 */
export async function expireReservation(
  reservationId: string
): Promise<CreditReservation> {
  const existing = await prisma.creditReservation.findUnique({
    where: { id: reservationId },
  });

  if (!existing) {
    throw new ReservationNotFoundError(reservationId);
  }

  if (existing.status !== ReservationStatus.ACTIVE) {
    throw new ReservationAlreadyResolvedError(
      reservationId,
      existing.status as ReservationStatus
    );
  }

  const updated = await prisma.creditReservation.update({
    where: { id: reservationId },
    data: {
      status:     ReservationStatus.EXPIRED,
      resolvedAt: new Date(),
    },
  });

  return updated as CreditReservation;
}

// ---------------------------------------------------------------------------
// Lookup helpers (admin portal / job runner)
// ---------------------------------------------------------------------------

/**
 * Get the reservation attached to a specific job.
 * Job runner uses this to get the reservationId for consume/release calls.
 */
export async function getReservationByJobId(
  jobId: string
): Promise<CreditReservation | null> {
  const reservation = await prisma.creditReservation.findFirst({
    where:   { jobId },
    orderBy: { createdAt: "desc" },
  });
  return reservation as CreditReservation | null;
}

/**
 * List all ACTIVE reservations for a user.
 * Used by the admin portal user view and the spend-cap check.
 */
export async function getActiveReservations(
  userId: string
): Promise<CreditReservation[]> {
  const reservations = await prisma.creditReservation.findMany({
    where:   { userId, status: ReservationStatus.ACTIVE },
    orderBy: { createdAt: "desc" },
  });
  return reservations as CreditReservation[];
}
