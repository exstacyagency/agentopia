/**
 * channel-broker.ts
 * @exstacyagency/agentopia
 *
 * Multi-platform inbound/outbound dispatcher. Normalises messages from
 * Discord, Telegram, WhatsApp, Slack, Signal into InboundMessage and
 * hands them to MessageRouter. Routes outbound GatewayResponseMessage
 * back to the originating channel via platform adapters.
 *
 * Platform adapters are registered at init — the broker itself is
 * platform-agnostic. Each adapter implements PlatformAdapter.
 *
 * Depends on: message-router, gateway-ws-client, types/index.ts
 */

import { EventEmitter } from "events";
import { randomUUID } from "crypto";
import { prisma } from "../lib/prisma.js";
import { MessageRouter, type InboundMessage, type DispatchResult } from "./message-router.js";
import { gatewayFleet } from "./gateway-ws-client.js";
import type { Platform, ChannelRoute } from "../types/index.js";

// ---------------------------------------------------------------------------
// Platform adapter interface
// ---------------------------------------------------------------------------

export interface PlatformAdapter {
  platform: Platform;
  /** Send a message back to a channel. Returns platform message ID or void. */
  send(channelId: string, userId: string, content: string): Promise<string | void>;
  /** Optional: called when broker boots to register webhooks / start polling */
  start?(): Promise<void>;
  /** Optional: called on graceful shutdown */
  stop?(): Promise<void>;
}

// ---------------------------------------------------------------------------
// Broker events
// ---------------------------------------------------------------------------

export interface BrokerEvents {
  inbound: (msg: InboundMessage) => void;
  dispatched: (result: DispatchResult) => void;
  outbound: (userId: string, platform: Platform | "chat", channelId: string, content: string) => void;
  routeNotFound: (platform: Platform, platformUserId: string) => void;
  adapterError: (platform: Platform, err: Error) => void;
  error: (err: Error) => void;
}

declare interface ChannelBroker {
  on<K extends keyof BrokerEvents>(event: K, listener: BrokerEvents[K]): this;
  emit<K extends keyof BrokerEvents>(event: K, ...args: Parameters<BrokerEvents[K]>): boolean;
}

// ---------------------------------------------------------------------------
// ChannelBroker
// ---------------------------------------------------------------------------

class ChannelBroker extends EventEmitter {
  private adapters = new Map<Platform, PlatformAdapter>();
  private router: MessageRouter | null = null;

  // ── Lifecycle ──────────────────────────────────────────────────────────

  init(router: MessageRouter): void {
    this.router = router;

    // Wire dispatch results back to channels
    router.on("dispatch", (result) => {
      this.emit("dispatched", result);
    });

    // Wire gateway responses back to originating channel
    this._watchGatewayResponses();
  }

  registerAdapter(adapter: PlatformAdapter): void {
    this.adapters.set(adapter.platform, adapter);
  }

  async start(): Promise<void> {
    for (const adapter of this.adapters.values()) {
      if (adapter.start) {
        await adapter.start().catch((err: Error) => {
          this.emit("adapterError", adapter.platform, err);
        });
      }
    }
  }

  async stop(): Promise<void> {
    for (const adapter of this.adapters.values()) {
      if (adapter.stop) {
        await adapter.stop().catch(() => {});
      }
    }
    this.removeAllListeners();
  }

  // ── Inbound: platform → router ─────────────────────────────────────────

  /**
   * Called by platform adapters when a message arrives.
   * Resolves the ChannelRoute, builds InboundMessage, passes to router.
   */
  async accept(
    platform: Platform,
    platformUserId: string,
    platformChannelId: string,
    content: string,
    isDm = false
  ): Promise<void> {
    if (!this.router) throw new Error("ChannelBroker: not initialised — call init() first");

    const route = await this._resolveRoute(platform, platformUserId);
    if (!route) {
      this.emit("routeNotFound", platform, platformUserId);
      return;
    }

    const msg: InboundMessage = {
      routeId: route.id,
      userId: route.userId,
      platform,
      platformUserId,
      platformChannelId,
      content: content.trim(),
      receivedAt: Date.now(),
      isDm,
    };

    // Update lastMessageAt async — non-blocking
    this._touchRoute(route.id).catch(() => {});

    this.emit("inbound", msg);
    this.router.accept(msg);
  }

  // ── Outbound: gateway → platform ──────────────────────────────────────

  /**
   * Send a message to a user's active channel.
   * Resolves their platform route and dispatches via the correct adapter.
   */
  async send(userId: string, content: string, platform?: Platform): Promise<void> {
    const route = await this._getActiveRoute(userId, platform);
    if (!route) {
      this.emit("error", new Error(`ChannelBroker: no active route for user ${userId}`));
      return;
    }

    await this._sendViaAdapter(route, content);
    this.emit("outbound", userId, route.platform, route.platformChannelId, content);
  }

  /**
   * Ack sender — passed to MessageRouter as config.ackSender.
   * MessageRouter calls this; broker routes to correct adapter.
   */
  ackSender = async (
    userId: string,
    platformChannelId: string,
    platform: Platform | "chat",
    message: string
  ): Promise<void> => {
    if (platform === "chat") {
      // Chat uses gateway WS directly — no adapter needed
      this.emit("outbound", userId, platform, platformChannelId, message);
      return;
    }
    const adapter = this.adapters.get(platform);
    if (!adapter) return;
    await adapter.send(platformChannelId, userId, message).catch((err: Error) => {
      this.emit("adapterError", platform, err);
    });
    this.emit("outbound", userId, platform, platformChannelId, message);
  };

  // ── Route management ───────────────────────────────────────────────────

  async createRoute(input: Omit<ChannelRoute, "id" | "lastMessageAt">): Promise<ChannelRoute> {
    const route = await prisma.channelRoute.create({
      data: { ...input, id: randomUUID() },
    });
    return route as ChannelRoute;
  }

  async deactivateRoute(routeId: string): Promise<void> {
    await prisma.channelRoute.update({
      where: { id: routeId },
      data: { active: false },
    });
  }

  async getRoutesForUser(userId: string): Promise<ChannelRoute[]> {
    const routes = await prisma.channelRoute.findMany({
      where: { userId, active: true },
    });
    return routes as ChannelRoute[];
  }

  // ── Internal ───────────────────────────────────────────────────────────

  private async _resolveRoute(
    platform: Platform,
    platformUserId: string
  ): Promise<ChannelRoute | null> {
    const route = await prisma.channelRoute.findFirst({
      where: { platform, platformUserId, active: true },
    });
    return route as ChannelRoute | null;
  }

  private async _getActiveRoute(userId: string, platform?: Platform): Promise<ChannelRoute | null> {
    const where = platform
      ? { userId, platform, active: true }
      : { userId, active: true };
    const route = await prisma.channelRoute.findFirst({ where });
    return route as ChannelRoute | null;
  }

  private async _sendViaAdapter(route: ChannelRoute, content: string): Promise<void> {
    const adapter = this.adapters.get(route.platform);
    if (!adapter) {
      this.emit("error", new Error(`ChannelBroker: no adapter registered for platform ${route.platform}`));
      return;
    }
    await adapter.send(route.platformChannelId, route.userId, content).catch((err: Error) => {
      this.emit("adapterError", route.platform, err);
    });
  }

  private async _touchRoute(routeId: string): Promise<void> {
    await prisma.channelRoute.update({
      where: { id: routeId },
      data: { lastMessageAt: new Date() },
    });
  }

  /** Wire all connected gateway clients to push responses back to channels */
  private _watchGatewayResponses(): void {
    // New clients added to fleet after init also need wiring —
    // call attachResponseHandler when adding a user's client
    for (const [userId, client] of gatewayFleet.entries()) {
      this._attachResponseHandler(userId, client);
    }
  }

  /**
   * Call this after gatewayFleet.getOrCreate() for a user.
   * Wires gateway response messages to their channel.
   */
  attachResponseHandler(userId: string): void {
    const client = gatewayFleet.get(userId);
    if (client) this._attachResponseHandler(userId, client);
  }

  private _attachResponseHandler(userId: string, client: InstanceType<typeof import("./gateway-ws-client.js").GatewayWsClient>): void {
    client.on("message", (msg) => {
      if (msg.type === "response") {
        this.send(userId, msg.content).catch((err: Error) => {
          this.emit("error", err);
        });
      }
    });
  }
}

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

export const channelBroker = new ChannelBroker();
export { ChannelBroker };
