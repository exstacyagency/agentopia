/**
 * @exstacyagency/agentopia
 * src/billing/pricing-catalog.ts
 *
 * Base rates per model and per job type. Reads from the job registry
 * at runtime — no hardcoded job type assumptions in this file.
 *
 * Responsibilities:
 *   - Model base rates (cost per 1k input/output tokens)
 *   - Job cost estimation (used by reserveCredits upfront)
 *   - Job cost settlement (actualCost after completion)
 *   - Tier multipliers and routing profile overrides
 *   - Top-off pack definitions
 *
 * Depends on: Prisma client, types/index.ts (JobTypeRegistry)
 */

import { prisma } from "../lib/prisma";
import type { JobTypeRegistry, RegisteredJobType } from "../types";

// ---------------------------------------------------------------------------
// Model Base Rates
// Cost in credits per 1k tokens. 1 credit = $0.01 USD at base rate.
// ---------------------------------------------------------------------------

export const MODEL_RATES: Record<string, ModelRate> = {
  // Haiku — orchestrator, cortex, acknowledgment layer
  "claude-haiku-4-5": {
    model:           "claude-haiku-4-5",
    inputPer1k:      0.025,   // $0.00025 / 1k tokens → 0.025 credits
    outputPer1k:     0.125,   // $0.00125 / 1k tokens → 0.125 credits
    cacheWritePer1k: 0.03,
    cacheReadPer1k:  0.003,
  },

  // Sonnet — standard worker jobs, balanced profile default
  "claude-sonnet-4-6": {
    model:           "claude-sonnet-4-6",
    inputPer1k:      0.3,     // $0.003 / 1k tokens → 0.3 credits
    outputPer1k:     1.5,     // $0.015 / 1k tokens → 1.5 credits
    cacheWritePer1k: 0.375,
    cacheReadPer1k:  0.03,
  },

  // Opus — heavy jobs, Enterprise and premium profile only
  "claude-opus-4-6": {
    model:           "claude-opus-4-6",
    inputPer1k:      1.5,     // $0.015 / 1k tokens → 1.5 credits
    outputPer1k:     7.5,     // $0.075 / 1k tokens → 7.5 credits
    cacheWritePer1k: 1.875,
    cacheReadPer1k:  0.15,
  },

  // Embedding — memory store writes, not billed per job but tracked
  "text-embedding-3-small": {
    model:           "text-embedding-3-small",
    inputPer1k:      0.002,
    outputPer1k:     0,
    cacheWritePer1k: 0,
    cacheReadPer1k:  0,
  },
} as const;

// ---------------------------------------------------------------------------
// Tier Multipliers
// Applied on top of base model rate at settlement time.
// Growth pays base rate. Scale and Enterprise pay less per job
// because their subscription covers the margin.
// ---------------------------------------------------------------------------

export const TIER_MULTIPLIERS: Record<string, number> = {
  growth:     1.0,
  scale:      0.85,
  enterprise: 0.70,
} as const;

// ---------------------------------------------------------------------------
// Routing Profile Model Maps
// Determines which model handles light/standard/heavy complexity scores
// within the hard tier ceiling.
// ---------------------------------------------------------------------------

export const ROUTING_PROFILE_MODELS: Record<
  RoutingProfile,
  Record<ComplexityScore, string>
> = {
  eco: {
    light:    "claude-haiku-4-5",
    standard: "claude-haiku-4-5",
    heavy:    "claude-sonnet-4-6",
  },
  balanced: {
    light:    "claude-haiku-4-5",
    standard: "claude-sonnet-4-6",
    heavy:    "claude-opus-4-6",
  },
  premium: {
    light:    "claude-sonnet-4-6",
    standard: "claude-sonnet-4-6",
    heavy:    "claude-opus-4-6",
  },
} as const;

// Tier model ceiling — a job can never use a model above this regardless
// of routing profile or complexity score.
export const TIER_MODEL_CEILING: Record<string, string> = {
  growth:     "claude-sonnet-4-6",
  scale:      "claude-opus-4-6",
  enterprise: "claude-opus-4-6",
} as const;

// ---------------------------------------------------------------------------
// Top-Off Pack Definitions
// Matches the pricing table in the spec exactly.
// ---------------------------------------------------------------------------

export const TOP_OFF_PACKS: TopOffPack[] = [
  {
    id:          "research-boost",
    name:        "Research Boost",
    domain:      "research",
    jobs:        5,
    priceUsd:    90,
    perJobRate:  18,
    tier:        null,   // available to all tiers
  },
  {
    id:          "research-pro",
    name:        "Research Pro",
    domain:      "research",
    jobs:        15,
    priceUsd:    210,
    perJobRate:  14,
    tier:        null,
  },
  {
    id:          "creative-boost",
    name:        "Creative Boost",
    domain:      "creative",
    jobs:        10,
    priceUsd:    80,
    perJobRate:  8,
    tier:        null,
  },
  {
    id:          "creative-pro",
    name:        "Creative Pro",
    domain:      "creative",
    jobs:        30,
    priceUsd:    180,
    perJobRate:  6,
    tier:        null,
  },
  {
    id:          "enterprise-research",
    name:        "Enterprise Research",
    domain:      "research",
    jobs:        25,
    priceUsd:    250,
    perJobRate:  10,
    tier:        "enterprise",
  },
  {
    id:          "enterprise-creative",
    name:        "Enterprise Creative",
    domain:      "creative",
    jobs:        50,
    priceUsd:    200,
    perJobRate:  4,
    tier:        "enterprise",
  },
] as const;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ModelRate {
  model:           string;
  inputPer1k:      number;
  outputPer1k:     number;
  cacheWritePer1k: number;
  cacheReadPer1k:  number;
}

export type RoutingProfile = "eco" | "balanced" | "premium";
export type ComplexityScore = "light" | "standard" | "heavy";

export interface TopOffPack {
  id:         string;
  name:       string;
  domain:     "research" | "creative";
  jobs:       number;
  priceUsd:   number;
  perJobRate: number;
  tier:       string | null;   // null = available to all tiers
}

export interface JobCostEstimate {
  jobType:          string;
  model:            string;
  estimatedCredits: number;
  breakdown: {
    estimatedInputTokens:  number;
    estimatedOutputTokens: number;
    inputCost:             number;
    outputCost:            number;
    tierMultiplier:        number;
  };
}

export interface JobActualCost {
  jobType:       string;
  model:         string;
  actualCredits: number;
  breakdown: {
    inputTokens:    number;
    outputTokens:   number;
    cacheWriteTokens: number;
    cacheReadTokens:  number;
    inputCost:      number;
    outputCost:     number;
    cacheWriteCost: number;
    cacheReadCost:  number;
    tierMultiplier: number;
  };
}

// ---------------------------------------------------------------------------
// Runtime Job Registry Reader
// Reads registered job types — no hardcoded job type assumptions.
// ---------------------------------------------------------------------------

let _jobRegistry: JobTypeRegistry | null = null;

/**
 * Inject the job registry at platform init.
 * Called once by AgentPlatform constructor.
 */
export function registerJobTypes(registry: JobTypeRegistry): void {
  _jobRegistry = registry;
}

function getJobRegistry(): JobTypeRegistry {
  if (!_jobRegistry) {
    throw new Error(
      "pricing-catalog: job registry not initialised. " +
      "Call registerJobTypes() at platform init before any billing operations."
    );
  }
  return _jobRegistry;
}

export function getRegisteredJobType(jobTypeId: string): RegisteredJobType {
  const registry = getJobRegistry();
  const job      = registry.get(jobTypeId);
  if (!job) {
    throw new Error(`pricing-catalog: unknown job type "${jobTypeId}"`);
  }
  return job;
}

// ---------------------------------------------------------------------------
// Model Resolution
// Resolves the actual model for a job given tier ceiling and routing profile.
// ---------------------------------------------------------------------------

/**
 * Resolve the model that will be used for a job.
 * Applies routing profile + complexity score, then caps at tier ceiling.
 */
export function resolveModel(
  jobTypeId:      string,
  tier:           string,
  routingProfile: RoutingProfile,
  complexity:     ComplexityScore
): string {
  const job = getRegisteredJobType(jobTypeId);

  // Job-level model override takes precedence (e.g. analysis slot is always Opus)
  if (job.modelOverride) {
    return enforceTierCeiling(job.modelOverride, tier);
  }

  const profileModel = ROUTING_PROFILE_MODELS[routingProfile][complexity];
  return enforceTierCeiling(profileModel, tier);
}

function enforceTierCeiling(model: string, tier: string): string {
  const ceiling      = TIER_MODEL_CEILING[tier] ?? "claude-sonnet-4-6";
  const modelRank    = getModelRank(model);
  const ceilingRank  = getModelRank(ceiling);
  return modelRank > ceilingRank ? ceiling : model;
}

function getModelRank(model: string): number {
  const ranks: Record<string, number> = {
    "claude-haiku-4-5":   1,
    "claude-sonnet-4-6":  2,
    "claude-opus-4-6":    3,
  };
  return ranks[model] ?? 0;
}

// ---------------------------------------------------------------------------
// Cost Estimation (used by reserveCredits upfront)
// ---------------------------------------------------------------------------

/**
 * Estimate job cost before execution.
 * Uses job-type token budgets from the registry as the basis.
 * Result is passed to reserveCredits() as estimatedCredits.
 */
export function estimateJobCost(
  jobTypeId:      string,
  tier:           string,
  routingProfile: RoutingProfile,
  complexity:     ComplexityScore
): JobCostEstimate {
  const job   = getRegisteredJobType(jobTypeId);
  const model = resolveModel(jobTypeId, tier, routingProfile, complexity);
  const rates = MODEL_RATES[model];

  if (!rates) {
    throw new Error(`pricing-catalog: no rate defined for model "${model}"`);
  }

  const estimatedInputTokens  = job.estimatedInputTokens  ?? 2000;
  const estimatedOutputTokens = job.estimatedOutputTokens ?? 1000;
  const tierMultiplier        = TIER_MULTIPLIERS[tier]    ?? 1.0;

  const inputCost  = (estimatedInputTokens  / 1000) * rates.inputPer1k;
  const outputCost = (estimatedOutputTokens / 1000) * rates.outputPer1k;
  const rawCost    = inputCost + outputCost;

  return {
    jobType:          jobTypeId,
    model,
    estimatedCredits: parseFloat((rawCost * tierMultiplier).toFixed(4)),
    breakdown: {
      estimatedInputTokens,
      estimatedOutputTokens,
      inputCost:      parseFloat(inputCost.toFixed(4)),
      outputCost:     parseFloat(outputCost.toFixed(4)),
      tierMultiplier,
    },
  };
}

// ---------------------------------------------------------------------------
// Actual Cost Settlement (used by settleJobCost after completion)
// ---------------------------------------------------------------------------

export interface TokenUsageInput {
  inputTokens:      number;
  outputTokens:     number;
  cacheWriteTokens?: number;
  cacheReadTokens?:  number;
}

/**
 * Calculate the actual cost of a completed job from real token usage.
 * Result's actualCredits is passed to settleJobCost() as actualCost.
 */
export function calculateActualCost(
  jobTypeId:    string,
  model:        string,
  tier:         string,
  tokenUsage:   TokenUsageInput
): JobActualCost {
  const rates = MODEL_RATES[model];

  if (!rates) {
    throw new Error(`pricing-catalog: no rate defined for model "${model}"`);
  }

  const {
    inputTokens,
    outputTokens,
    cacheWriteTokens = 0,
    cacheReadTokens  = 0,
  } = tokenUsage;

  const tierMultiplier  = TIER_MULTIPLIERS[tier] ?? 1.0;

  const inputCost      = (inputTokens      / 1000) * rates.inputPer1k;
  const outputCost     = (outputTokens     / 1000) * rates.outputPer1k;
  const cacheWriteCost = (cacheWriteTokens / 1000) * rates.cacheWritePer1k;
  const cacheReadCost  = (cacheReadTokens  / 1000) * rates.cacheReadPer1k;
  const rawCost        = inputCost + outputCost + cacheWriteCost + cacheReadCost;

  return {
    jobType:       jobTypeId,
    model,
    actualCredits: parseFloat((rawCost * tierMultiplier).toFixed(4)),
    breakdown: {
      inputTokens,
      outputTokens,
      cacheWriteTokens,
      cacheReadTokens,
      inputCost:      parseFloat(inputCost.toFixed(4)),
      outputCost:     parseFloat(outputCost.toFixed(4)),
      cacheWriteCost: parseFloat(cacheWriteCost.toFixed(4)),
      cacheReadCost:  parseFloat(cacheReadCost.toFixed(4)),
      tierMultiplier,
    },
  };
}

// ---------------------------------------------------------------------------
// Top-Off Pack Helpers
// ---------------------------------------------------------------------------

/**
 * Get packs available to a specific tier.
 * Filters out tier-restricted packs the user's tier can't access.
 */
export function getAvailablePacks(tier: string): TopOffPack[] {
  return TOP_OFF_PACKS.filter(
    (pack) => pack.tier === null || pack.tier === tier
  );
}

/**
 * Get a single pack by ID. Throws if not found.
 */
export function getPackById(packId: string): TopOffPack {
  const pack = TOP_OFF_PACKS.find((p) => p.id === packId);
  if (!pack) {
    throw new Error(`pricing-catalog: unknown top-off pack "${packId}"`);
  }
  return pack;
}
