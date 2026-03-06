/**
 * @exstacyagency/agentopia
 * src/billing/spend-cap.ts
 *
 * Spend cap enforcement. The first gate in the job admission sequence —
 * must pass before reserveCredits() is called.
 *
 * Call order:
 *   assertUnderSpendCap()  ← this file
 *   → reserveCredits()     ← quota-reservation.ts
 *   → dispatch job
 *   → settleJobCost()      ← credit-ledger.ts
 *   → consumeReservation() ← quota-reservation.ts
 *
 * Depends on: Prisma client, billing/credit-ledger.ts,
 *             billing/quota-reservation.ts, types/index.ts
 */

import { prisma } from "../lib/prisma";
import { getBalance, getUsageSummary, CreditDomain } from "./credit-ledger";
import { getActiveReservationTotal } from "./quota-reservation";

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class SpendCapExceededError extends Error {
  constructor(
    public readonly userId:       string,
    public readonly domain:       CreditDomain,
    public readonly capType:      "daily" | "monthly" | "subscription",
    public readonly capValue:     number,
    public readonly currentSpend: number
  ) {
    super(
      `Spend cap exceeded for user ${userId} in domain ${domain}. ` +
      `Cap type: ${capType}, limit: ${capValue}, current spend: ${currentSpend}`
    );
    this.name = "SpendCapExceededError";
  }
}

export class SpendCapNotFoundError extends Error {
  constructor(public readonly userId: string) {
    super(`No spend cap configuration found for user ${userId}`);
    this.name = "SpendCapNotFoundError";
  }
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SpendCap {
  id:               string;
  userId:           string;
  domain:           CreditDomain | "all";   // "all" applies across both domains
  dailyLimit:       number | null;           // null = no daily cap
  monthlyLimit:     number | null;           // null = no monthly cap
  subscriptionLimit: number | null;          // null = no subscription-period cap
  enabled:          boolean;
  createdAt:        Date;
  updatedAt:        Date;
}

export interface SpendCapStatus {
  userId:              string;
  domain:              CreditDomain;
  dailySpend:          number;
  monthlySpend:        number;
  subscriptionSpend:   number;
  dailyLimit:          number | null;
  monthlyLimit:        number | null;
  subscriptionLimit:   number | null;
  availableBalance:    number;
  activeHolds:         number;
  withinCap:           boolean;
}

// ---------------------------------------------------------------------------
// Period Helpers
// ---------------------------------------------------------------------------

function startOfToday(): Date {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}

function startOfMonth(): Date {
  const d = new Date();
  d.setDate(1);
  d.setHours(0, 0, 0, 0);
  return d;
}

/**
 * Returns the start of the current billing period for a user.
 * Anchored to their subscription start day-of-month.
 * Falls back to start of calendar month if no subscription found.
 */
async function startOfBillingPeriod(userId: string): Promise<Date> {
  const subscription = await prisma.userSubscription.findFirst({
    where:   { userId, active: true },
    select:  { billingAnchorDay: true },
    orderBy: { createdAt: "desc" },
  });

  const anchorDay = subscription?.billingAnchorDay ?? 1;
  const now       = new Date();
  const year      = now.getFullYear();
  const month     = now.getMonth();
  const day       = now.getDate();

  // If we haven't yet passed the anchor day this month, use last month's anchor
  const periodStart = day >= anchorDay
    ? new Date(year, month, anchorDay, 0, 0, 0, 0)
    : new Date(year, month - 1, anchorDay, 0, 0, 0, 0);

  return periodStart;
}

// ---------------------------------------------------------------------------
// Spend Reads
// ---------------------------------------------------------------------------

async function getDailySpend(userId: string, domain: CreditDomain): Promise<number> {
  const summary = await getUsageSummary(userId, startOfToday(), new Date());
  return summary.find((r) => r.domain === domain)?.totalSpent ?? 0;
}

async function getMonthlySpend(userId: string, domain: CreditDomain): Promise<number> {
  const summary = await getUsageSummary(userId, startOfMonth(), new Date());
  return summary.find((r) => r.domain === domain)?.totalSpent ?? 0;
}

async function getSubscriptionSpend(userId: string, domain: CreditDomain): Promise<number> {
  const periodStart = await startOfBillingPeriod(userId);
  const summary     = await getUsageSummary(userId, periodStart, new Date());
  return summary.find((r) => r.domain === domain)?.totalSpent ?? 0;
}

// ---------------------------------------------------------------------------
// Core Assertion
// ---------------------------------------------------------------------------

/**
 * Assert that adding `estimatedCredits` to the user's current spend
 * will not breach any configured cap.
 *
 * Throws SpendCapExceededError on the first cap violation found.
 * Returns void on success — job admission may proceed to reserveCredits().
 *
 * Checks in order: subscription cap → monthly cap → daily cap.
 * All three are evaluated against domain-scoped spend.
 */
export async function assertUnderSpendCap(
  userId:           string,
  domain:           CreditDomain,
  estimatedCredits: number
): Promise<void> {
  const cap = await prisma.spendCap.findFirst({
    where: {
      userId,
      enabled: true,
      OR: [{ domain }, { domain: "all" }],
    },
  });

  // No cap configured — pass through
  if (!cap) return;

  const [subscriptionSpend, monthlySpend, dailySpend] = await Promise.all([
    getSubscriptionSpend(userId, domain),
    getMonthlySpend(userId, domain),
    getDailySpend(userId, domain),
  ]);

  const projectedSubscription = subscriptionSpend + estimatedCredits;
  const projectedMonthly      = monthlySpend      + estimatedCredits;
  const projectedDaily        = dailySpend        + estimatedCredits;

  if (cap.subscriptionLimit !== null && projectedSubscription > cap.subscriptionLimit) {
    throw new SpendCapExceededError(
      userId, domain, "subscription",
      cap.subscriptionLimit, subscriptionSpend
    );
  }

  if (cap.monthlyLimit !== null && projectedMonthly > cap.monthlyLimit) {
    throw new SpendCapExceededError(
      userId, domain, "monthly",
      cap.monthlyLimit, monthlySpend
    );
  }

  if (cap.dailyLimit !== null && projectedDaily > cap.dailyLimit) {
    throw new SpendCapExceededError(
      userId, domain, "daily",
      cap.dailyLimit, dailySpend
    );
  }
}

// ---------------------------------------------------------------------------
// Status Read (billing UI + admin portal)
// ---------------------------------------------------------------------------

/**
 * Full spend cap status for a user in a domain.
 * Used by the billing tab and admin user view.
 */
export async function getSpendCapStatus(
  userId: string,
  domain: CreditDomain
): Promise<SpendCapStatus> {
  const cap = await prisma.spendCap.findFirst({
    where: {
      userId,
      enabled: true,
      OR: [{ domain }, { domain: "all" }],
    },
  });

  const [
    subscriptionSpend,
    monthlySpend,
    dailySpend,
    ledgerBalance,
    activeHolds,
  ] = await Promise.all([
    getSubscriptionSpend(userId, domain),
    getMonthlySpend(userId, domain),
    getDailySpend(userId, domain),
    getBalance(userId, domain),
    getActiveReservationTotal(userId, domain),
  ]);

  return {
    userId,
    domain,
    dailySpend,
    monthlySpend,
    subscriptionSpend,
    dailyLimit:         cap?.dailyLimit         ?? null,
    monthlyLimit:       cap?.monthlyLimit        ?? null,
    subscriptionLimit:  cap?.subscriptionLimit   ?? null,
    availableBalance:   ledgerBalance - activeHolds,
    activeHolds,
    withinCap:          true, // if we got here without throwing, cap is fine
  };
}

// ---------------------------------------------------------------------------
// Cap Management (admin portal)
// ---------------------------------------------------------------------------

export interface UpsertSpendCapInput {
  userId:            string;
  domain:            CreditDomain | "all";
  dailyLimit?:       number | null;
  monthlyLimit?:     number | null;
  subscriptionLimit?: number | null;
  enabled?:          boolean;
}

/**
 * Create or update a spend cap for a user.
 * Admin portal and subscription provisioning both call this.
 */
export async function upsertSpendCap(input: UpsertSpendCapInput): Promise<SpendCap> {
  const { userId, domain, dailyLimit, monthlyLimit, subscriptionLimit, enabled = true } = input;

  const existing = await prisma.spendCap.findFirst({
    where: { userId, domain },
  });

  if (existing) {
    const updated = await prisma.spendCap.update({
      where: { id: existing.id },
      data: {
        ...(dailyLimit        !== undefined ? { dailyLimit }        : {}),
        ...(monthlyLimit      !== undefined ? { monthlyLimit }      : {}),
        ...(subscriptionLimit !== undefined ? { subscriptionLimit } : {}),
        enabled,
        updatedAt: new Date(),
      },
    });
    return updated as SpendCap;
  }

  const created = await prisma.spendCap.create({
    data: {
      userId,
      domain,
      dailyLimit:        dailyLimit        ?? null,
      monthlyLimit:      monthlyLimit       ?? null,
      subscriptionLimit: subscriptionLimit  ?? null,
      enabled,
      createdAt:  new Date(),
      updatedAt:  new Date(),
    },
  });
  return created as SpendCap;
}

/**
 * Disable a spend cap without deleting it.
 * Preserves history. Re-enable with upsertSpendCap({ enabled: true }).
 */
export async function disableSpendCap(
  userId: string,
  domain: CreditDomain | "all"
): Promise<void> {
  await prisma.spendCap.updateMany({
    where: { userId, domain },
    data:  { enabled: false, updatedAt: new Date() },
  });
}
