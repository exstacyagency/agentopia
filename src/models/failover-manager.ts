/**
 * failover-manager.ts
 * @exstacyagency/agentopia
 *
 * API key pool management and rate-limit-aware failover.
 * Tracks per-key rate limit state, rotates keys under pressure,
 * and provides fallback model chains when a model tier is unavailable.
 *
 * Consumed by model-router.ts — never called directly by orchestration.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ApiKey {
  id: string;
  key: string;
  /** Requests remaining in current window (updated on 429 headers) */
  remainingRequests: number;
  /** Tokens remaining in current window */
  remainingTokens: number;
  /** Unix ms when the rate limit window resets */
  resetAt: number;
  /** Consecutive 429s without recovery */
  consecutiveFailures: number;
  /** Soft-disabled after too many failures */
  suspended: boolean;
  suspendedUntil: number;
}

export interface KeyPoolStatus {
  totalKeys: number;
  activeKeys: number;
  suspendedKeys: number;
  /** 0.0–1.0 headroom across active keys (avg remaining / limit) */
  headroom: number;
}

export interface FailoverResult {
  key: ApiKey;
  model: string;
  /** true if this is a fallback from the originally requested model */
  isFallback: boolean;
  fallbackReason?: string;
}

// ---------------------------------------------------------------------------
// Model fallback chains
// Per spec: rate limit or unavailability → step down, never step up
// ---------------------------------------------------------------------------

const MODEL_FALLBACK_CHAINS: Record<string, string[]> = {
  "claude-opus-4-6":        ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
  "claude-sonnet-4-6":      ["claude-haiku-4-5-20251001"],
  "claude-haiku-4-5-20251001": [],
};

// Suspension config
const MAX_CONSECUTIVE_FAILURES = 5;
const SUSPENSION_DURATION_MS = 60_000; // 1 minute
const LOW_HEADROOM_THRESHOLD = 0.15;   // flag key if <15% remaining

// ---------------------------------------------------------------------------
// FailoverManager
// ---------------------------------------------------------------------------

export class FailoverManager {
  private keys: Map<string, ApiKey> = new Map();

  constructor(rawKeys: string[]) {
    for (const key of rawKeys) {
      const id = `key_${Math.random().toString(36).slice(2, 8)}`;
      this.keys.set(id, {
        id,
        key,
        remainingRequests: 1000,
        remainingTokens: 100_000,
        resetAt: 0,
        consecutiveFailures: 0,
        suspended: false,
        suspendedUntil: 0,
      });
    }
  }

  // ── Key selection ──────────────────────────────────────────────────────

  /**
   * Pick the best available key for the requested model.
   * Falls back through the model chain if needed.
   * Throws if no key + model combination is available.
   */
  selectKey(requestedModel: string): FailoverResult {
    const now = Date.now();
    const modelsToTry = [requestedModel, ...(MODEL_FALLBACK_CHAINS[requestedModel] ?? [])];

    for (let i = 0; i < modelsToTry.length; i++) {
      const model = modelsToTry[i];
      const key = this._pickBestKey(now);
      if (key) {
        return {
          key,
          model,
          isFallback: i > 0,
          fallbackReason: i > 0 ? `Fell back from ${requestedModel} — no available keys` : undefined,
        };
      }
    }

    throw new Error(`FailoverManager: no available API keys for model ${requestedModel} or its fallbacks`);
  }

  // ── Rate limit feedback ────────────────────────────────────────────────

  /**
   * Call after a successful response to update key health.
   */
  recordSuccess(keyId: string, remainingRequests?: number, remainingTokens?: number, resetAt?: number): void {
    const key = this.keys.get(keyId);
    if (!key) return;
    key.consecutiveFailures = 0;
    key.suspended = false;
    if (remainingRequests !== undefined) key.remainingRequests = remainingRequests;
    if (remainingTokens !== undefined) key.remainingTokens = remainingTokens;
    if (resetAt !== undefined) key.resetAt = resetAt;
  }

  /**
   * Call on 429. Suspends key if failures exceed threshold.
   */
  recordRateLimit(keyId: string, retryAfterMs?: number): void {
    const key = this.keys.get(keyId);
    if (!key) return;
    key.consecutiveFailures++;
    key.remainingRequests = 0;
    if (retryAfterMs !== undefined) {
      key.resetAt = Date.now() + retryAfterMs;
    }
    if (key.consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
      key.suspended = true;
      key.suspendedUntil = Date.now() + SUSPENSION_DURATION_MS;
    }
  }

  /**
   * Call on non-429 API error.
   */
  recordError(keyId: string): void {
    const key = this.keys.get(keyId);
    if (!key) return;
    key.consecutiveFailures++;
    if (key.consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
      key.suspended = true;
      key.suspendedUntil = Date.now() + SUSPENSION_DURATION_MS;
    }
  }

  // ── Pool status ────────────────────────────────────────────────────────

  getPoolStatus(): KeyPoolStatus {
    const now = Date.now();
    const all = Array.from(this.keys.values());
    const active = all.filter((k) => this._isKeyAvailable(k, now));
    const suspended = all.filter((k) => k.suspended && k.suspendedUntil > now);

    const avgHeadroom =
      active.length > 0
        ? active.reduce((sum, k) => sum + Math.min(k.remainingRequests / 1000, 1), 0) / active.length
        : 0;

    return {
      totalKeys: all.length,
      activeKeys: active.length,
      suspendedKeys: suspended.length,
      headroom: avgHeadroom,
    };
  }

  /** Keys approaching rate limits — for admin portal flagging */
  getFlaggedKeys(): ApiKey[] {
    const now = Date.now();
    return Array.from(this.keys.values()).filter(
      (k) => this._isKeyAvailable(k, now) && k.remainingRequests / 1000 < LOW_HEADROOM_THRESHOLD
    );
  }

  // ── Internal ───────────────────────────────────────────────────────────

  private _isKeyAvailable(key: ApiKey, now: number): boolean {
    if (key.suspended && key.suspendedUntil > now) return false;
    // Auto-recover suspended key if window has reset
    if (key.suspended && key.suspendedUntil <= now) {
      key.suspended = false;
      key.consecutiveFailures = 0;
      key.remainingRequests = 1000;
    }
    if (key.remainingRequests <= 0 && key.resetAt > now) return false;
    // Auto-recover after reset window
    if (key.remainingRequests <= 0 && key.resetAt <= now) {
      key.remainingRequests = 1000;
      key.remainingTokens = 100_000;
    }
    return true;
  }

  /** Pick key with most remaining headroom */
  private _pickBestKey(now: number): ApiKey | null {
    let best: ApiKey | null = null;
    let bestRemaining = -1;
    for (const key of this.keys.values()) {
      if (!this._isKeyAvailable(key, now)) continue;
      if (key.remainingRequests > bestRemaining) {
        bestRemaining = key.remainingRequests;
        best = key;
      }
    }
    return best;
  }
}
