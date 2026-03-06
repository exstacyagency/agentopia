/**
 * @exstacyagency/agentopia
 * src/orchestration/config-pusher.ts
 *
 * Hot-reload config delivery to live user containers.
 * Pushes SOUL.md updates, openclaw.json patches, and skill file changes
 * to all containers, a tier cohort, or a single user — without restart.
 *
 * Features:
 *   - Versioned config tracking (hash-based, per container)
 *   - Diff preview before push
 *   - Rollback to last known-good config
 *   - Audit log entry per push operation
 *   - Target scoping: all | tier cohort | single user
 *
 * Depends on: gateway-ws-client (fleet), prisma, types/index.ts
 */

import * as fs        from "fs/promises";
import * as crypto    from "crypto";
import * as path      from "path";
import { prisma }     from "../lib/prisma.js";
import { gatewayFleet, type GatewayWsClient } from "./gateway-ws-client.js";
import type { AgentSlotDefinition } from "../types/index.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type PushTarget =
  | { scope: "all" }
  | { scope: "tier"; tier: string }
  | { scope: "user"; userId: string };

export type ConfigAssetType = "soul" | "skill" | "openclaw_json" | "raw_file";

export interface ConfigAsset {
  type:     ConfigAssetType;
  /** Absolute path to the source file on the platform host */
  filePath: string;
  /** Destination path inside the container workspace */
  destPath: string;
}

export interface PushOptions {
  /** Assets to push */
  assets:     ConfigAsset[];
  /** Who is initiating the push (admin user ID or 'system') */
  initiator:  string;
  /** Dry-run: compute diff and affected users, do not push */
  dryRun?:    boolean;
  /** If true, skip containers that are currently running a job */
  skipBusy?:  boolean;
}

export interface DiffEntry {
  userId:     string;
  assetType:  ConfigAssetType;
  destPath:   string;
  oldHash:    string | null;
  newHash:    string;
  changed:    boolean;
}

export interface PushResult {
  target:     PushTarget;
  dryRun:     boolean;
  totalUsers: number;
  pushed:     number;
  skipped:    number;
  failed:     number;
  diffs:      DiffEntry[];
  errors:     Array<{ userId: string; error: string }>;
  pushedAt:   Date;
}

export interface RollbackResult {
  userId:     string;
  rolledBack: number;
  errors:     string[];
}

// ---------------------------------------------------------------------------
// Internal
// ---------------------------------------------------------------------------

interface ConfigVersion {
  userId:    string;
  destPath:  string;
  hash:      string;
  content:   string;
  pushedAt:  Date;
}

// ---------------------------------------------------------------------------
// ConfigPusher
// ---------------------------------------------------------------------------

export class ConfigPusher {
  /**
   * In-memory version store: `${userId}::${destPath}` → ConfigVersion[]
   * Last entry = current. Second-to-last = rollback target.
   */
  private versions = new Map<string, ConfigVersion[]>();

  // ── Public API ────────────────────────────────────────────────────────

  /**
   * Push config assets to targeted containers.
   * Returns a full result including diffs, skip/fail counts, and audit log.
   */
  async push(target: PushTarget, opts: PushOptions): Promise<PushResult> {
    const { assets, initiator, dryRun = false, skipBusy = false } = opts;

    const userIds = await this._resolveTarget(target);
    const assetContents = await this._loadAssets(assets);

    const result: PushResult = {
      target,
      dryRun,
      totalUsers: userIds.length,
      pushed:  0,
      skipped: 0,
      failed:  0,
      diffs:   [],
      errors:  [],
      pushedAt: new Date(),
    };

    for (const userId of userIds) {
      // Skip busy containers if requested
      if (skipBusy && (await this._isBusy(userId))) {
        result.skipped++;
        continue;
      }

      const client = gatewayFleet.get(userId);
      if (!client) {
        result.skipped++;
        continue;
      }

      // Compute diffs
      const diffs = this._computeDiffs(userId, assets, assetContents);
      result.diffs.push(...diffs);

      const hasChanges = diffs.some((d) => d.changed);
      if (!hasChanges) {
        result.skipped++;
        continue;
      }

      if (dryRun) {
        result.pushed++;
        continue;
      }

      // Deliver each asset
      const pushErrors: string[] = [];
      for (let i = 0; i < assets.length; i++) {
        const asset   = assets[i]!;
        const content = assetContents[i]!;
        const diff    = diffs[i]!;

        if (!diff.changed) continue;

        try {
          await this._deliverAsset(client, asset, content);
          this._recordVersion(userId, asset.destPath, diff.newHash, content);
        } catch (err) {
          pushErrors.push(`${asset.destPath}: ${(err as Error).message}`);
        }
      }

      if (pushErrors.length > 0) {
        result.failed++;
        result.errors.push({ userId, error: pushErrors.join("; ") });
      } else {
        result.pushed++;
      }
    }

    // Audit log
    if (!dryRun) {
      await this._auditLog(initiator, target, result);
    }

    return result;
  }

  /**
   * Preview what would change for a target without pushing.
   * Equivalent to push(..., { dryRun: true }).
   */
  async preview(target: PushTarget, assets: ConfigAsset[]): Promise<DiffEntry[]> {
    const userIds      = await this._resolveTarget(target);
    const assetContents = await this._loadAssets(assets);
    const diffs: DiffEntry[] = [];

    for (const userId of userIds) {
      diffs.push(...this._computeDiffs(userId, assets, assetContents));
    }

    return diffs;
  }

  /**
   * Roll back the last push for a specific user.
   * Restores all assets to their previous version.
   */
  async rollback(userId: string, initiator: string): Promise<RollbackResult> {
    const client = gatewayFleet.get(userId);
    const errors: string[] = [];
    let rolledBack = 0;

    if (!client) {
      return { userId, rolledBack: 0, errors: ["Container not connected"] };
    }

    // Find all tracked dest paths for this user
    for (const [key, history] of this.versions.entries()) {
      if (!key.startsWith(`${userId}::`)) continue;
      if (history.length < 2) continue; // nothing to roll back to

      const destPath = key.slice(userId.length + 2);
      const previous = history[history.length - 2]!;

      try {
        const asset: ConfigAsset = {
          type:     "raw_file",
          filePath: "",   // not needed for rollback — content is cached
          destPath,
        };
        await this._deliverRaw(client, destPath, previous.content);
        // Pop current version
        history.pop();
        rolledBack++;
      } catch (err) {
        errors.push(`${destPath}: ${(err as Error).message}`);
      }
    }

    await this._auditLog(initiator, { scope: "user", userId }, {
      target: { scope: "user", userId },
      dryRun: false,
      totalUsers: 1,
      pushed: rolledBack,
      skipped: 0,
      failed: errors.length,
      diffs: [],
      errors: errors.map((e) => ({ userId, error: e })),
      pushedAt: new Date(),
    }, "rollback");

    return { userId, rolledBack, errors };
  }

  /**
   * Push SOUL.md to a target. Convenience wrapper.
   */
  async pushSoul(soulPath: string, target: PushTarget, initiator: string): Promise<PushResult> {
    return this.push(target, {
      assets: [{
        type:     "soul",
        filePath: soulPath,
        destPath: "SOUL.md",
      }],
      initiator,
    });
  }

  /**
   * Push a skill file to a target. Convenience wrapper.
   */
  async pushSkill(skillPath: string, jobType: string, target: PushTarget, initiator: string): Promise<PushResult> {
    const fileName = path.basename(skillPath);
    return this.push(target, {
      assets: [{
        type:     "skill",
        filePath: skillPath,
        destPath: `skills/${jobType}/${fileName}`,
      }],
      initiator,
    });
  }

  /**
   * Push openclaw.json patch to a target. Convenience wrapper.
   */
  async pushOpenclawConfig(
    configPath: string,
    target: PushTarget,
    initiator: string,
  ): Promise<PushResult> {
    return this.push(target, {
      assets: [{
        type:     "openclaw_json",
        filePath: configPath,
        destPath: "openclaw.json",
      }],
      initiator,
    });
  }

  /**
   * Return the current tracked version hash for a user + destPath.
   * Returns null if never pushed.
   */
  getCurrentHash(userId: string, destPath: string): string | null {
    const history = this.versions.get(`${userId}::${destPath}`);
    return history?.at(-1)?.hash ?? null;
  }

  // ── Target resolution ─────────────────────────────────────────────────

  private async _resolveTarget(target: PushTarget): Promise<string[]> {
    if (target.scope === "user") {
      return [target.userId];
    }

    if (target.scope === "tier") {
      const subs = await (prisma as any).userSubscription.findMany({
        where:  { tier: target.tier, status: "active" },
        select: { userId: true },
      }) as Array<{ userId: string }>;
      return subs.map((s) => s.userId);
    }

    // scope === "all" — every user with a live container
    const containers = await prisma.containerRecord.findMany({
      where:  { status: { not: "stopped" } },
      select: { userId: true },
      distinct: ["userId"],
    });
    return containers.map((c: { userId: string }) => c.userId);
  }

  // ── Asset loading ─────────────────────────────────────────────────────

  private async _loadAssets(assets: ConfigAsset[]): Promise<string[]> {
    return Promise.all(
      assets.map(async (asset) => {
        if (!asset.filePath) return ""; // rollback path — content sourced from cache
        try {
          return await fs.readFile(asset.filePath, "utf-8");
        } catch (err) {
          throw new Error(`ConfigPusher: cannot read asset ${asset.filePath} — ${(err as Error).message}`);
        }
      })
    );
  }

  // ── Diff computation ──────────────────────────────────────────────────

  private _computeDiffs(
    userId:        string,
    assets:        ConfigAsset[],
    assetContents: string[],
  ): DiffEntry[] {
    return assets.map((asset, i) => {
      const content = assetContents[i]!;
      const newHash = this._hash(content);
      const oldHash = this.getCurrentHash(userId, asset.destPath);
      return {
        userId,
        assetType: asset.type,
        destPath:  asset.destPath,
        oldHash,
        newHash,
        changed:   oldHash !== newHash,
      };
    });
  }

  // ── Delivery ──────────────────────────────────────────────────────────

  /**
   * Deliver a single asset to a connected container.
   * Uses the Gateway WS API workspace file write mechanism.
   */
  private async _deliverAsset(
    client:  GatewayWsClient,
    asset:   ConfigAsset,
    content: string,
  ): Promise<void> {
    await this._deliverRaw(client, asset.destPath, content);
  }

  private async _deliverRaw(
    client:   GatewayWsClient,
    destPath: string,
    content:  string,
  ): Promise<void> {
    if (!client.isConnected) {
      throw new Error("Container not connected");
    }

    // Encode as a system message that OpenClaw interprets as a workspace write.
    // OpenClaw processes file_write tool results delivered via session_send on
    // the reserved "__config__" session ID.
    const payload = JSON.stringify({
      op:      "workspace_write",
      path:    destPath,
      content,
    });

    await client.spawnSession("__config__", "orchestrator").catch(() => {
      // Session may already exist — ignore spawn errors
    });

    await client.sendMessage("__config__", payload, "system");
  }

  // ── Busy check ────────────────────────────────────────────────────────

  private async _isBusy(userId: string): Promise<boolean> {
    const running = await prisma.runningTurn.count({
      where: { userId, status: "running" },
    });
    return running > 0;
  }

  // ── Version tracking ──────────────────────────────────────────────────

  private _recordVersion(
    userId:   string,
    destPath: string,
    hash:     string,
    content:  string,
  ): void {
    const key     = `${userId}::${destPath}`;
    const history = this.versions.get(key) ?? [];

    history.push({ userId, destPath, hash, content, pushedAt: new Date() });

    // Keep only last 3 versions per asset per user to cap memory
    if (history.length > 3) history.shift();

    this.versions.set(key, history);
  }

  // ── Audit log ─────────────────────────────────────────────────────────

  private async _auditLog(
    initiator: string,
    target:    PushTarget,
    result:    PushResult,
    action:    string = "config_push",
  ): Promise<void> {
    try {
      await (prisma as any).auditLog.create({
        data: {
          action,
          initiator,
          target:    JSON.stringify(target),
          pushed:    result.pushed,
          skipped:   result.skipped,
          failed:    result.failed,
          errorSummary: result.errors.length > 0
            ? result.errors.map((e) => `${e.userId}: ${e.error}`).join(" | ")
            : null,
          createdAt: result.pushedAt,
        },
      });
    } catch {
      // Audit table may not exist yet — non-fatal
      console.warn("[ConfigPusher] audit log write failed — non-fatal");
    }
  }

  // ── Utilities ─────────────────────────────────────────────────────────

  private _hash(content: string): string {
    return crypto.createHash("sha256").update(content).digest("hex").slice(0, 16);
  }
}

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

let _instance: ConfigPusher | null = null;

export function initConfigPusher(): ConfigPusher {
  _instance = new ConfigPusher();
  return _instance;
}

export function getConfigPusher(): ConfigPusher {
  if (!_instance) throw new Error("ConfigPusher not initialised — call initConfigPusher first");
  return _instance;
}
