/**
 * gateway-ws-client.ts
 * @exstacyagency/agentopia
 *
 * Typed WebSocket API client for a single user's OpenClaw Gateway container.
 * One instance per provisioned container. Handles connect, reconnect, send,
 * and typed message dispatch. All orchestration modules talk to OpenClaw
 * through this client — never raw WebSocket calls.
 */

import { EventEmitter } from "events";
import WebSocket from "ws";
import type { ProvisionedContainer } from "../types/index.js";

// ---------------------------------------------------------------------------
// OpenClaw wire types
// ---------------------------------------------------------------------------

export type GatewayMessageRole = "user" | "assistant" | "system";

export interface GatewayInboundMessage {
  type: "message";
  sessionId: string;
  role: GatewayMessageRole;
  content: string;
  /** Attached tool results, if any */
  toolResults?: unknown[];
}

export interface GatewaySessionSpawn {
  type: "session_spawn";
  sessionId: string;
  agentSlot: string;
  systemPrompt?: string;
  workspaceFiles?: string[];
}

export interface GatewaySessionSend {
  type: "session_send";
  sessionId: string;
  content: string;
  role?: GatewayMessageRole;
}

export interface GatewaySessionHistory {
  type: "session_history";
  sessionId: string;
}

export interface GatewaySessionTerminate {
  type: "session_terminate";
  sessionId: string;
}

export type GatewayOutbound =
  | GatewaySessionSpawn
  | GatewaySessionSend
  | GatewaySessionHistory
  | GatewaySessionTerminate;

// ---------------------------------------------------------------------------
// Gateway response types (inbound from OpenClaw)
// ---------------------------------------------------------------------------

export interface GatewayResponseMessage {
  type: "response";
  sessionId: string;
  content: string;
  usage?: { inputTokens: number; outputTokens: number };
  finishReason?: "end_turn" | "tool_use" | "max_tokens" | "stop_sequence";
}

export interface GatewayResponseHistory {
  type: "history";
  sessionId: string;
  turns: Array<{ role: GatewayMessageRole; content: string; timestamp: string }>;
}

export interface GatewayResponseError {
  type: "error";
  sessionId?: string;
  code: string;
  message: string;
}

export interface GatewayResponseAck {
  type: "ack";
  sessionId: string;
  ref?: string;
}

export interface GatewayTokenCount {
  type: "token_count";
  sessionId: string;
  totalTokens: number;
  contextWindowSize: number;
  usagePercent: number;
}

export type GatewayInbound =
  | GatewayResponseMessage
  | GatewayResponseHistory
  | GatewayResponseError
  | GatewayResponseAck
  | GatewayTokenCount;

// ---------------------------------------------------------------------------
// Client config & events
// ---------------------------------------------------------------------------

export interface GatewayClientOptions {
  /** Milliseconds between reconnect attempts. Default: 2000 */
  reconnectDelayMs?: number;
  /** Max reconnect attempts before giving up. Default: 10 */
  maxReconnectAttempts?: number;
  /** Ping interval to detect stale connections. Default: 30000 */
  pingIntervalMs?: number;
  /** Per-send timeout before treating message as lost. Default: 10000 */
  sendTimeoutMs?: number;
}

export interface GatewayClientEvents {
  connected: () => void;
  disconnected: (code: number, reason: string) => void;
  reconnecting: (attempt: number) => void;
  error: (err: Error) => void;
  message: (msg: GatewayInbound) => void;
  /** Emitted whenever token_count crosses a threshold (for compaction-monitor) */
  tokenCount: (payload: GatewayTokenCount) => void;
}

declare interface GatewayWsClient {
  on<K extends keyof GatewayClientEvents>(event: K, listener: GatewayClientEvents[K]): this;
  emit<K extends keyof GatewayClientEvents>(event: K, ...args: Parameters<GatewayClientEvents[K]>): boolean;
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

class GatewayWsClient extends EventEmitter {
  private readonly userId: string;
  private readonly url: string;
  private readonly token: string;
  private readonly opts: Required<GatewayClientOptions>;

  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private pingTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private destroyed = false;

  constructor(container: ProvisionedContainer, opts: GatewayClientOptions = {}) {
    super();
    this.userId = container.userId;
    this.url = `ws://${container.host}:${container.port}`;
    this.token = container.gatewayToken;
    this.opts = {
      reconnectDelayMs: opts.reconnectDelayMs ?? 2000,
      maxReconnectAttempts: opts.maxReconnectAttempts ?? 10,
      pingIntervalMs: opts.pingIntervalMs ?? 30_000,
      sendTimeoutMs: opts.sendTimeoutMs ?? 10_000,
    };
  }

  // ── Lifecycle ──────────────────────────────────────────────────────────

  connect(): void {
    if (this.destroyed) throw new Error(`GatewayWsClient(${this.userId}): already destroyed`);
    this._open();
  }

  destroy(): void {
    this.destroyed = true;
    this._clearTimers();
    if (this.ws) {
      this.ws.removeAllListeners();
      this.ws.terminate();
      this.ws = null;
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // ── Public API ─────────────────────────────────────────────────────────

  spawnSession(sessionId: string, agentSlot: string, systemPrompt?: string, workspaceFiles?: string[]): Promise<GatewayResponseAck> {
    return this._sendAndAck({ type: "session_spawn", sessionId, agentSlot, systemPrompt, workspaceFiles });
  }

  sendMessage(sessionId: string, content: string, role: GatewayMessageRole = "user"): Promise<GatewayResponseMessage> {
    return this._sendAndReceive<GatewayResponseMessage>(
      { type: "session_send", sessionId, content, role },
      "response",
      sessionId
    );
  }

  getHistory(sessionId: string): Promise<GatewayResponseHistory> {
    return this._sendAndReceive<GatewayResponseHistory>(
      { type: "session_history", sessionId },
      "history",
      sessionId
    );
  }

  terminateSession(sessionId: string): Promise<GatewayResponseAck> {
    return this._sendAndAck({ type: "session_terminate", sessionId });
  }

  // ── Internal: send helpers ─────────────────────────────────────────────

  private _send(payload: GatewayOutbound): void {
    if (!this.isConnected || !this.ws) {
      throw new Error(`GatewayWsClient(${this.userId}): not connected`);
    }
    this.ws.send(JSON.stringify(payload));
  }

  private _sendAndAck(payload: GatewayOutbound): Promise<GatewayResponseAck> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(`GatewayWsClient(${this.userId}): ack timeout`)), this.opts.sendTimeoutMs);

      const handler = (msg: GatewayInbound) => {
        if (msg.type === "ack" && "sessionId" in payload && msg.sessionId === (payload as { sessionId: string }).sessionId) {
          clearTimeout(timer);
          this.off("message", handler);
          resolve(msg);
        }
        if (msg.type === "error") {
          clearTimeout(timer);
          this.off("message", handler);
          reject(new Error(`Gateway error [${msg.code}]: ${msg.message}`));
        }
      };

      this.on("message", handler);
      try {
        this._send(payload);
      } catch (err) {
        clearTimeout(timer);
        this.off("message", handler);
        reject(err);
      }
    });
  }

  private _sendAndReceive<T extends GatewayInbound>(
    payload: GatewayOutbound,
    expectedType: T["type"],
    sessionId: string
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(
        () => reject(new Error(`GatewayWsClient(${this.userId}): response timeout (${expectedType})`)),
        this.opts.sendTimeoutMs
      );

      const handler = (msg: GatewayInbound) => {
        if (msg.type === expectedType && "sessionId" in msg && msg.sessionId === sessionId) {
          clearTimeout(timer);
          this.off("message", handler);
          resolve(msg as T);
        }
        if (msg.type === "error" && (!("sessionId" in msg) || msg.sessionId === sessionId)) {
          clearTimeout(timer);
          this.off("message", handler);
          reject(new Error(`Gateway error [${(msg as GatewayResponseError).code}]: ${(msg as GatewayResponseError).message}`));
        }
      };

      this.on("message", handler);
      try {
        this._send(payload);
      } catch (err) {
        clearTimeout(timer);
        this.off("message", handler);
        reject(err);
      }
    });
  }

  // ── Internal: connection management ───────────────────────────────────

  private _open(): void {
    const ws = new WebSocket(this.url, {
      headers: { Authorization: `Bearer ${this.token}` },
    });

    ws.on("open", () => {
      this.ws = ws;
      this.reconnectAttempts = 0;
      this._startPing();
      this.emit("connected");
    });

    ws.on("message", (data: WebSocket.RawData) => {
      let msg: GatewayInbound;
      try {
        msg = JSON.parse(data.toString()) as GatewayInbound;
      } catch {
        this.emit("error", new Error(`GatewayWsClient(${this.userId}): unparseable message`));
        return;
      }
      if (msg.type === "token_count") {
        this.emit("tokenCount", msg);
      }
      this.emit("message", msg);
    });

    ws.on("close", (code: number, reason: Buffer) => {
      this._clearTimers();
      this.ws = null;
      if (!this.destroyed) {
        this.emit("disconnected", code, reason.toString());
        this._scheduleReconnect();
      }
    });

    ws.on("error", (err: Error) => {
      this.emit("error", err);
    });
  }

  private _scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.opts.maxReconnectAttempts) {
      this.emit("error", new Error(`GatewayWsClient(${this.userId}): max reconnect attempts reached`));
      return;
    }
    this.reconnectAttempts++;
    this.emit("reconnecting", this.reconnectAttempts);
    const delay = Math.min(this.opts.reconnectDelayMs * this.reconnectAttempts, 30_000);
    this.reconnectTimer = setTimeout(() => this._open(), delay);
  }

  private _startPing(): void {
    this.pingTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.ping();
      }
    }, this.opts.pingIntervalMs);
  }

  private _clearTimers(): void {
    if (this.pingTimer) { clearInterval(this.pingTimer); this.pingTimer = null; }
    if (this.reconnectTimer) { clearTimeout(this.reconnectTimer); this.reconnectTimer = null; }
  }
}

// ---------------------------------------------------------------------------
// Fleet registry — one client per live container
// ---------------------------------------------------------------------------

class GatewayFleetManager {
  private clients = new Map<string, GatewayWsClient>();

  getOrCreate(container: ProvisionedContainer, opts?: GatewayClientOptions): GatewayWsClient {
    if (this.clients.has(container.userId)) {
      return this.clients.get(container.userId)!;
    }
    const client = new GatewayWsClient(container, opts);
    this.clients.set(container.userId, client);
    client.connect();
    return client;
  }

  get(userId: string): GatewayWsClient | undefined {
    return this.clients.get(userId);
  }

  /** Cleanly destroy and remove a user's client (container teardown). */
  remove(userId: string): void {
    const client = this.clients.get(userId);
    if (client) {
      client.destroy();
      this.clients.delete(userId);
    }
  }

  get size(): number {
    return this.clients.size;
  }
}

export { GatewayWsClient, GatewayFleetManager };
export const gatewayFleet = new GatewayFleetManager();
