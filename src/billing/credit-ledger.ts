/**
 * @exstacyagency/agentopia
 * src/billing/credit-ledger.ts
 *
 * Append-only credit ledger. Handles UsageEvent recording, balance reads,
 * and job cost settlement. Never mutates existing rows.
 *
 * Depends on: Prisma client (shared schema), types/index.ts
 */

import { prisma } from "../lib/prisma";

// ---------------------------------------------------------------------------
// Enums & Types
// ---------------------------------------------------------------------------

export enum UsageEventType {
  JOB_SETTLEMENT = "JOB_SETTLEMENT",   // deducted after job.actualCost known
  CREDIT_GRANT   = "CREDIT_GRANT",     // subscription renewal, top-off pack
  ADMIN_ADJUST   = "ADMIN_ADJUST",     // manual admin credit/debit
  ROLLOVER       = "ROLLOVER",         // Enterprise 60-day job rollover credit
  REFUND         = "REFUND",           // disputed charge reversal
}

export enum CreditDomain {
  RESEARCH   = "research",
  CREATIVE   = "creative",
  GENERAL    = "general",   // non-domain platform events
}

export interface UsageEvent {
  id:          string;
  userId:      string;
  type:        UsageEventType;
  domain:      CreditDomain;
  jobId:       string | null;   // null for non-job events (grants, adjustments)
  jobType:     string | null;
  modelUsed:   string | null;
  deltaCredits: number;          // positive = credit added, negative = deducted
  balanceAfter: number;          // snapshot of balance at event time
  metadata:    Record<string, unknown>;
  createdAt:   Date;
}

export interface BalanceSummary {
  userId:          string;
  researchCredits: number;
  creativeCredits: number;
  lastUpdatedAt:   Date;
}

export interface JobSettlementInput {
  userId:      string;
  jobId:       string;
  jobType:     string;
  domain:      CreditDomain;
  modelUsed:   string;
  actualCost:  number;          // in credits, resolved post-completion
  metadata?:   Record<string, unknown>;
}

export interface CreditGrantInput {
  userId:       string;
  domain:       CreditDomain;
  credits:      number;
  type:         UsageEventType.CREDIT_GRANT | UsageEventType.ADMIN_ADJUST | UsageEventType.ROLLOVER | UsageEventType.REFUND;
  reason:       string;
  grantedBy?:   string;         // admin userId if ADMIN_ADJUST
  metadata?:    Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Balance Helpers
// ---------------------------------------------------------------------------

/**
 * Read current credit balance for a user in a specific domain.
 * Derived from the ledger sum — always consistent with event history.
 */
export async function getBalance(
  userId: string,
  domain: CreditDomain
): Promise<number> {
  const result = await prisma.usageEvent.aggregate({
    where: { userId, domain },
    _sum: { deltaCredits: true },
  });
  return result._sum.deltaCredits ?? 0;
}

/**
 * Read balances for all domains in a single call.
 */
export async function getAllBalances(userId: string): Promise<BalanceSummary> {
  const [research, creative] = await Promise.all([
    getBalance(userId, CreditDomain.RESEARCH),
    getBalance(userId, CreditDomain.CREATIVE),
  ]);

  const latest = await prisma.usageEvent.findFirst({
    where: { userId },
    orderBy: { createdAt: "desc" },
    select: { createdAt: true },
  });

  return {
    userId,
    researchCredits: research,
    creativeCredits: creative,
    lastUpdatedAt:   latest?.createdAt ?? new Date(),
  };
}

// ---------------------------------------------------------------------------
// Settlement
// ---------------------------------------------------------------------------

/**
 * Settle a completed job against the user's credit balance.
 * Deducts job.actualCost — never estimated cost.
 * Appends an immutable UsageEvent row.
 *
 * Called by the job runner after job.status transitions to COMPLETE.
 * The quota reservation for this job should be released before calling this.
 */
export async function settleJobCost(input: JobSettlementInput): Promise<UsageEvent> {
  const {
    userId, jobId, jobType, domain, modelUsed, actualCost, metadata = {}
  } = input;

  if (actualCost < 0) {
    throw new Error(`settleJobCost: actualCost must be non-negative (got ${actualCost})`);
  }

  const currentBalance = await getBalance(userId, domain);
  const balanceAfter   = currentBalance - actualCost;

  const event = await prisma.usageEvent.create({
    data: {
      userId,
      type:         UsageEventType.JOB_SETTLEMENT,
      domain,
      jobId,
      jobType,
      modelUsed,
      deltaCredits: -actualCost,
      balanceAfter,
      metadata:     metadata as never,
      createdAt:    new Date(),
    },
  });

  return event as UsageEvent;
}

// ---------------------------------------------------------------------------
// Credit Grants (subscription renewal, top-offs, admin, rollover, refunds)
// ---------------------------------------------------------------------------

/**
 * Add credits to a user's balance.
 * Used for: subscription renewals, top-off pack purchases, admin adjustments,
 * Enterprise rollovers, and refunds.
 */
export async function grantCredits(input: CreditGrantInput): Promise<UsageEvent> {
  const {
    userId, domain, credits, type, reason, grantedBy, metadata = {}
  } = input;

  if (credits <= 0) {
    throw new Error(`grantCredits: credits must be positive (got ${credits})`);
  }

  const currentBalance = await getBalance(userId, domain);
  const balanceAfter   = currentBalance + credits;

  const event = await prisma.usageEvent.create({
    data: {
      userId,
      type,
      domain,
      jobId:        null,
      jobType:      null,
      modelUsed:    null,
      deltaCredits: credits,
      balanceAfter,
      metadata:     { reason, grantedBy: grantedBy ?? null, ...metadata },
      createdAt:    new Date(),
    },
  });

  return event as UsageEvent;
}

// ---------------------------------------------------------------------------
// Ledger History
// ---------------------------------------------------------------------------

export interface LedgerQueryOptions {
  domain?:   CreditDomain;
  type?:     UsageEventType;
  fromDate?: Date;
  toDate?:   Date;
  limit?:    number;
  offset?:   number;
}

/**
 * Paginated ledger history for a user.
 * Returns events newest-first.
 */
export async function getLedgerHistory(
  userId:  string,
  options: LedgerQueryOptions = {}
): Promise<UsageEvent[]> {
  const {
    domain, type, fromDate, toDate,
    limit  = 50,
    offset = 0,
  } = options;

  const events = await prisma.usageEvent.findMany({
    where: {
      userId,
      ...(domain   ? { domain }   : {}),
      ...(type     ? { type }     : {}),
      ...(fromDate || toDate ? {
        createdAt: {
          ...(fromDate ? { gte: fromDate } : {}),
          ...(toDate   ? { lte: toDate   } : {}),
        },
      } : {}),
    },
    orderBy: { createdAt: "desc" },
    take:    limit,
    skip:    offset,
  });

  return events as UsageEvent[];
}

/**
 * Summarise credit usage for a user within a date range.
 * Used by the admin cost dashboard.
 */
export async function getUsageSummary(
  userId:    string,
  fromDate:  Date,
  toDate:    Date
): Promise<{ domain: CreditDomain; totalSpent: number; jobCount: number }[]> {
  const rows = await prisma.usageEvent.groupBy({
    by:     ["domain"],
    where: {
      userId,
      type:      UsageEventType.JOB_SETTLEMENT,
      createdAt: { gte: fromDate, lte: toDate },
    },
    _sum:   { deltaCredits: true },
    _count: { jobId: true },
  });

  return rows.map((r: { domain: string; _sum: { deltaCredits: number | null }; _count: { jobId: number } }) => ({
    domain:     r.domain as CreditDomain,
    totalSpent: Math.abs(r._sum.deltaCredits ?? 0),
    jobCount:   r._count.jobId,
  }));
}
