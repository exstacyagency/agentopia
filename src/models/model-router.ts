/**
 * model-router.ts
 * @exstacyagency/agentopia
 *
 * Key pool dispatch, routing profiles, tier ceiling enforcement, and
 * fallback chains. Sits between message-router and the Anthropic API.
 *
 * Consumes: complexity-scorer output, pricing-catalog model resolution,
 * failover-manager key selection.
 *
 * Never makes API calls directly — returns a resolved RouteDecision that
 * the caller uses to construct the actual Anthropic SDK call.
 */

import {
  resolveModel,
  TIER_MODEL_CEILING,
  ROUTING_PROFILE_MODELS,
  type RoutingProfile,
  type ComplexityScore,
} from "../billing/pricing-catalog.js";
import { FailoverManager, type FailoverResult } from "./failover-manager.js";
import type { AgentSlotDefinition } from "../types/index.js";

// ---------------------------------------------------------------------------
// Model constants — single source of truth for string literals
// ---------------------------------------------------------------------------

export const MODELS = {
  HAIKU:  "claude-haiku-4-5-20251001",
  SONNET: "claude-sonnet-4-6",
  OPUS:   "claude-opus-4-6",
} as const;

export type ModelString = (typeof MODELS)[keyof typeof MODELS];

// Map tier names → canonical model strings
const TIER_TO_MODEL: Record<string, ModelString> = {
  haiku:  MODELS.HAIKU,
  sonnet: MODELS.SONNET,
  opus:   MODELS.OPUS,
};

// ---------------------------------------------------------------------------
// Route decision — what the caller uses to make the API call
// ---------------------------------------------------------------------------

export interface RouteDecision {
  model: ModelString;
  apiKey: string;
  keyId: string;
  /** true if the model was stepped down from requested */
  isFallback: boolean;
  fallbackReason?: string;
  /** The profile-resolved model before ceiling enforcement */
  requestedModel: ModelString;
  /** The ceiling model for this user's tier */
  ceilingModel: ModelString;
}

// ---------------------------------------------------------------------------
// Router config
// ---------------------------------------------------------------------------

export interface ModelRouterConfig {
  /** User's subscription tier: 'growth' | 'scale' | 'enterprise' */
  userTier: string;
  /** Routing profile from user config or tier default */
  routingProfile: RoutingProfile;
  /** Agent slot definition — may carry a modelOverride */
  agentSlot: AgentSlotDefinition;
  /** Key pool from platform init */
  keyPool: string[];
}

// ---------------------------------------------------------------------------
// ModelRouter
// ---------------------------------------------------------------------------

export class ModelRouter {
  private failover: FailoverManager;

  constructor(keyPool: string[]) {
    this.failover = new FailoverManager(keyPool);
  }

  // ── Route resolution ───────────────────────────────────────────────────

  /**
   * Resolve the model + API key for a given turn.
   * Order of precedence:
   *   1. agentSlot.modelOverride (hard override, bypasses profile)
   *   2. Routing profile × complexity score
   *   3. Tier ceiling enforcement (never exceed user's tier)
   *   4. Failover key selection with fallback chain
   */
  resolve(complexity: ComplexityScore, config: ModelRouterConfig): RouteDecision {
    const { userTier, routingProfile, agentSlot } = config;

    // 1. Hard override from slot definition
    let targetModel: ModelString;
    if (agentSlot.modelOverride) {
      targetModel = this._toModelString(agentSlot.modelOverride);
    } else {
      // 2. Profile × complexity
      const profileMap = ROUTING_PROFILE_MODELS[routingProfile];
      const profileTier: string = profileMap?.[complexity] ?? "haiku";
      targetModel = this._toModelString(profileTier);
    }

    // 3. Ceiling enforcement
    const ceilingTier = TIER_MODEL_CEILING[userTier] ?? "sonnet";
    const ceilingModel = this._toModelString(ceilingTier);
    const enforcedModel = this._applyModelCeiling(targetModel, ceilingModel);

    // 4. Key selection with failover
    let failoverResult: FailoverResult;
    try {
      failoverResult = this.failover.selectKey(enforcedModel);
    } catch (err) {
      throw new Error(`ModelRouter: no available keys — ${(err as Error).message}`);
    }

    return {
      model: failoverResult.model as ModelString,
      apiKey: failoverResult.key.key,
      keyId: failoverResult.key.id,
      isFallback: failoverResult.isFallback,
      fallbackReason: failoverResult.fallbackReason,
      requestedModel: enforcedModel,
      ceilingModel,
    };
  }

  // ── Feedback passthrough ───────────────────────────────────────────────

  recordSuccess(keyId: string, remainingRequests?: number, remainingTokens?: number, resetAt?: number): void {
    this.failover.recordSuccess(keyId, remainingRequests, remainingTokens, resetAt);
  }

  recordRateLimit(keyId: string, retryAfterMs?: number): void {
    this.failover.recordRateLimit(keyId, retryAfterMs);
  }

  recordError(keyId: string): void {
    this.failover.recordError(keyId);
  }

  getPoolStatus() {
    return this.failover.getPoolStatus();
  }

  getFlaggedKeys() {
    return this.failover.getFlaggedKeys();
  }

  // ── Internal ───────────────────────────────────────────────────────────

  private _toModelString(tierOrModel: string): ModelString {
    // Accept both tier names ('haiku') and full model strings
    return (TIER_TO_MODEL[tierOrModel] ?? tierOrModel) as ModelString;
  }

  /**
   * Enforce tier ceiling. If requested model is more capable than ceiling,
   * step down to ceiling. Model power order: haiku < sonnet < opus.
   */
  private _applyModelCeiling(requested: ModelString, ceiling: ModelString): ModelString {
    const power: Record<ModelString, number> = {
      [MODELS.HAIKU]:  1,
      [MODELS.SONNET]: 2,
      [MODELS.OPUS]:   3,
    };
    const reqPower = power[requested] ?? 1;
    const ceilPower = power[ceiling] ?? 2;
    return reqPower > ceilPower ? ceiling : requested;
  }
}

// ---------------------------------------------------------------------------
// Singleton — shared across all orchestration modules
// ---------------------------------------------------------------------------

let _instance: ModelRouter | null = null;

export function initModelRouter(keyPool: string[]): ModelRouter {
  _instance = new ModelRouter(keyPool);
  return _instance;
}

export function getModelRouter(): ModelRouter {
  if (!_instance) throw new Error("ModelRouter not initialised — call initModelRouter first");
  return _instance;
}
