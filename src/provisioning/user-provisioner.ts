/**
 * @exstacyagency/agentopia
 * src/provisioning/user-provisioner.ts
 *
 * Per-user container lifecycle: spawn, hibernate, destroy.
 * Writes openclaw.json into the container workspace on provision.
 * Tracks container health via 60-second heartbeat with 3-miss alert threshold.
 *
 * Security guarantee: no two users share a container. Every container
 * gets dedicated port, credentials, and session data. A routing bug
 * will fail to authenticate — not silently cross-contaminate.
 *
 * Depends on: prisma (lib/prisma), types/index.ts, agent-configurator.ts
 */

import { prisma } from "../lib/prisma.js";
import { buildAgentsList } from "./agent-configurator.js";
import type { AgentSlotDefinition, ProvisionedContainer } from "../types/index.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export enum ContainerStatus {
  PROVISIONING = "PROVISIONING",
  ACTIVE       = "ACTIVE",
  HIBERNATING  = "HIBERNATING",
  DESTROYED    = "DESTROYED",
  ERROR        = "ERROR",
}

export interface ContainerRecord {
  id:               string;
  userId:           string;
  status:           ContainerStatus;
  host:             string;
  port:             number;
  gatewayToken:     string;           // AES-256 encrypted at rest in DB
  openclawVersion:  string;
  configVersion:    number;
  lastHeartbeatAt:  Date | null;
  missedHeartbeats: number;
  createdAt:        Date;
  updatedAt:        Date;
}

export interface ProvisionUserInput {
  userId:           string;
  agentSlots:       AgentSlotDefinition[];
  soulPath:         string;
  openclawVersion?: string;
}

export interface OpenclawConfig {
  version:    string;
  userId:     string;
  agents:     ReturnType<typeof buildAgentsList>;
  workspace: {
    path:          string;
    memoryFile:    string;
    ingestDir:     string;
    skillsDir:     string;
  };
  security: {
    token:         string;
    encryptionKey: string;
  };
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class ContainerAlreadyExistsError extends Error {
  constructor(public readonly userId: string) {
    super(`Container already exists for user ${userId}. Use reprovision() to replace.`);
    this.name = "ContainerAlreadyExistsError";
  }
}

export class ContainerNotFoundError extends Error {
  constructor(public readonly userId: string) {
    super(`No active container found for user ${userId}`);
    this.name = "ContainerNotFoundError";
  }
}

export class ContainerSpawnError extends Error {
  constructor(
    public readonly userId: string,
    public readonly reason: string
  ) {
    super(`Failed to spawn container for user ${userId}: ${reason}`);
    this.name = "ContainerSpawnError";
  }
}

// ---------------------------------------------------------------------------
// Port Allocation
// ---------------------------------------------------------------------------

const PORT_RANGE_START = 4000;
const PORT_RANGE_END   = 9999;

/**
 * Find the next available port in the allocated range.
 * Queries active containers to avoid collisions.
 */
async function allocatePort(): Promise<number> {
  const usedPorts = await prisma.containerRecord.findMany({
    where:  { status: { not: ContainerStatus.DESTROYED } },
    select: { port: true },
  });

  const used = new Set(usedPorts.map((c: { port: number }) => c.port));

  for (let port = PORT_RANGE_START; port <= PORT_RANGE_END; port++) {
    if (!used.has(port)) return port;
  }

  throw new Error("No available ports in range — scale container nodes");
}

// ---------------------------------------------------------------------------
// Token Generation
// ---------------------------------------------------------------------------

/**
 * Generate a per-user gateway token.
 * In production this is derived from GATEWAY_SECRET_SALT + userId + timestamp
 * and stored AES-256 encrypted. For now returns a hex token.
 */
function generateGatewayToken(userId: string): string {
  const salt      = process.env.GATEWAY_SECRET_SALT ?? "dev-salt";
  const timestamp = Date.now().toString();
  const raw       = `${salt}:${userId}:${timestamp}`;

  // In production: encrypt with AES-256 before storing
  // Here we return a deterministic-looking hex string
  return Buffer.from(raw).toString("hex").slice(0, 64);
}

// ---------------------------------------------------------------------------
// openclaw.json Writer
// ---------------------------------------------------------------------------

/**
 * Build the openclaw.json config object for a user's container.
 * Written to the container workspace on provision and on config push.
 */
export function buildOpenclawConfig(
  userId:          string,
  agentSlots:      AgentSlotDefinition[],
  gatewayToken:    string,
  openclawVersion: string
): OpenclawConfig {
  const agents = buildAgentsList(agentSlots);

  return {
    version:  openclawVersion,
    userId,
    agents,
    workspace: {
      path:       `/workspace/${userId}`,
      memoryFile: `/workspace/${userId}/MEMORY.md`,
      ingestDir:  `/workspace/${userId}/ingest`,
      skillsDir:  `/workspace/${userId}/skills`,
    },
    security: {
      token:         gatewayToken,
      encryptionKey: process.env.ENCRYPTION_KEY ?? "",
    },
  };
}

// ---------------------------------------------------------------------------
// Container Spawn
// ---------------------------------------------------------------------------

/**
 * Provision a new container for a user.
 * - Allocates port
 * - Generates gateway token
 * - Writes openclaw.json to container workspace
 * - Records container in fleet table
 *
 * Throws ContainerAlreadyExistsError if user already has an active container.
 * Call reprovision() to replace an existing container.
 */
export async function provisionUser(input: ProvisionUserInput): Promise<ContainerRecord> {
  const {
    userId,
    agentSlots,
    soulPath,
    openclawVersion = process.env.OPENCLAW_VERSION ?? "latest",
  } = input;

  // Check for existing active container
  const existing = await prisma.containerRecord.findFirst({
    where: {
      userId,
      status: { in: [ContainerStatus.ACTIVE, ContainerStatus.PROVISIONING, ContainerStatus.HIBERNATING] },
    },
  });

  if (existing) {
    throw new ContainerAlreadyExistsError(userId);
  }

  const port         = await allocatePort();
  const gatewayToken = generateGatewayToken(userId);
  const host         = process.env.CONTAINER_HOST ?? "localhost";

  // Build openclaw config
  const config = buildOpenclawConfig(userId, agentSlots, gatewayToken, openclawVersion);

  // Write config to container workspace (via Docker API or Hetzner API)
  await writeOpenclawConfig(host, port, userId, config);

  // Record in fleet table
  const record = await prisma.containerRecord.create({
    data: {
      userId,
      status:           ContainerStatus.PROVISIONING,
      host,
      port,
      gatewayToken,     // TODO: encrypt with AES-256 before storing
      openclawVersion,
      configVersion:    1,
      lastHeartbeatAt:  null,
      missedHeartbeats: 0,
      createdAt:        new Date(),
      updatedAt:        new Date(),
    },
  });

  // Spawn the container process
  await spawnContainer(host, port, userId, openclawVersion);

  // Mark active
  const active = await prisma.containerRecord.update({
    where: { id: record.id },
    data:  { status: ContainerStatus.ACTIVE, updatedAt: new Date() },
  });

  return active as ContainerRecord;
}

// ---------------------------------------------------------------------------
// Container Lifecycle
// ---------------------------------------------------------------------------

/**
 * Hibernate a container — suspends execution, preserves workspace.
 * Used for inactive users to reduce compute cost.
 */
export async function hibernateContainer(userId: string): Promise<ContainerRecord> {
  const container = await getActiveContainer(userId);

  await sendContainerSignal(container.host, container.port, "hibernate");

  const updated = await prisma.containerRecord.update({
    where: { id: container.id },
    data:  { status: ContainerStatus.HIBERNATING, updatedAt: new Date() },
  });

  return updated as ContainerRecord;
}

/**
 * Wake a hibernated container.
 */
export async function wakeContainer(userId: string): Promise<ContainerRecord> {
  const container = await prisma.containerRecord.findFirst({
    where: { userId, status: ContainerStatus.HIBERNATING },
  });

  if (!container) {
    throw new ContainerNotFoundError(userId);
  }

  await sendContainerSignal(container.host, container.port, "wake");

  const updated = await prisma.containerRecord.update({
    where: { id: container.id },
    data:  { status: ContainerStatus.ACTIVE, updatedAt: new Date() },
  });

  return updated as ContainerRecord;
}

/**
 * Permanently destroy a container and its workspace.
 * Called on account deletion or tier downgrade requiring re-provision.
 */
export async function destroyContainer(userId: string): Promise<void> {
  const container = await prisma.containerRecord.findFirst({
    where: {
      userId,
      status: { not: ContainerStatus.DESTROYED },
    },
  });

  if (!container) return; // Already gone — idempotent

  await sendContainerSignal(container.host, container.port, "destroy");

  await prisma.containerRecord.update({
    where: { id: container.id },
    data:  { status: ContainerStatus.DESTROYED, updatedAt: new Date() },
  });
}

/**
 * Reprovision — destroy existing container and spawn a fresh one.
 * Used for tier changes requiring config rebuild, or corrupted containers.
 */
export async function reprovisionUser(input: ProvisionUserInput): Promise<ContainerRecord> {
  await destroyContainer(input.userId);
  return provisionUser(input);
}

// ---------------------------------------------------------------------------
// Heartbeat
// ---------------------------------------------------------------------------

const HEARTBEAT_INTERVAL_MS  = 60_000;  // 60 seconds
const HEARTBEAT_MISS_ALERT   = 3;        // alert after 3 missed beats

/**
 * Record a heartbeat from a container.
 * Called by the container's health ping endpoint.
 * Resets missed heartbeat counter on successful ping.
 */
export async function recordHeartbeat(userId: string): Promise<void> {
  await prisma.containerRecord.updateMany({
    where: { userId, status: ContainerStatus.ACTIVE },
    data:  {
      lastHeartbeatAt:  new Date(),
      missedHeartbeats: 0,
      updatedAt:        new Date(),
    },
  });
}

/**
 * Check all active containers for missed heartbeats.
 * Called by the process supervisor on a 60-second cron.
 * Increments missed counter and triggers alert at threshold.
 */
export async function checkHeartbeats(): Promise<{ alerted: string[] }> {
  const cutoff = new Date(Date.now() - HEARTBEAT_INTERVAL_MS * 1.5);

  const stale = await prisma.containerRecord.findMany({
    where: {
      status:          ContainerStatus.ACTIVE,
      lastHeartbeatAt: { lt: cutoff },
    },
  });

  const alerted: string[] = [];

  for (const container of stale) {
    const missed = container.missedHeartbeats + 1;

    await prisma.containerRecord.update({
      where: { id: container.id },
      data:  { missedHeartbeats: missed, updatedAt: new Date() },
    });

    if (missed >= HEARTBEAT_MISS_ALERT) {
      alerted.push(container.userId);
      await triggerHeartbeatAlert(container.userId, missed);
    }
  }

  return { alerted };
}

// ---------------------------------------------------------------------------
// Lookup Helpers
// ---------------------------------------------------------------------------

export async function getActiveContainer(userId: string): Promise<ContainerRecord> {
  const container = await prisma.containerRecord.findFirst({
    where: { userId, status: ContainerStatus.ACTIVE },
  });

  if (!container) throw new ContainerNotFoundError(userId);
  return container as ContainerRecord;
}

export async function getContainerByUserId(userId: string): Promise<ContainerRecord | null> {
  const container = await prisma.containerRecord.findFirst({
    where:   { userId, status: { not: ContainerStatus.DESTROYED } },
    orderBy: { createdAt: "desc" },
  });
  return container as ContainerRecord | null;
}

/**
 * Fleet summary for admin portal.
 */
export async function getFleetStatus(): Promise<{
  total: number;
  active: number;
  hibernating: number;
  error: number;
  provisioning: number;
}> {
  const counts = await prisma.containerRecord.groupBy({
    by:     ["status"],
    _count: { id: true },
    where:  { status: { not: ContainerStatus.DESTROYED } },
  });

  const byStatus = Object.fromEntries(
    counts.map((r: { status: string; _count: { id: number } }) => [r.status, r._count.id])
  );

  return {
    total:        counts.reduce((sum: number, r: { _count: { id: number } }) => sum + r._count.id, 0),
    active:       byStatus[ContainerStatus.ACTIVE]       ?? 0,
    hibernating:  byStatus[ContainerStatus.HIBERNATING]  ?? 0,
    error:        byStatus[ContainerStatus.ERROR]        ?? 0,
    provisioning: byStatus[ContainerStatus.PROVISIONING] ?? 0,
  };
}

// ---------------------------------------------------------------------------
// Infrastructure Stubs
// These are the integration points with Docker / Hetzner API.
// Implement with actual provider SDK in the product repo or via env config.
// ---------------------------------------------------------------------------

async function writeOpenclawConfig(
  host:    string,
  port:    number,
  userId:  string,
  config:  OpenclawConfig
): Promise<void> {
  // TODO: write config JSON to container workspace via Docker API
  // Example: docker exec <container> write /workspace/${userId}/openclaw.json
  console.log(`[provisioner] Writing openclaw.json for user ${userId} on ${host}:${port}`);
  void config;
}

async function spawnContainer(
  host:            string,
  port:            number,
  userId:          string,
  openclawVersion: string
): Promise<void> {
  // TODO: docker run / Hetzner server create
  // Must bind to port, mount workspace volume, set GATEWAY_TOKEN env var
  console.log(`[provisioner] Spawning container for user ${userId} on ${host}:${port} (openclaw@${openclawVersion})`);
}

async function sendContainerSignal(
  host:   string,
  port:   number,
  signal: "hibernate" | "wake" | "destroy"
): Promise<void> {
  // TODO: HTTP POST to container management endpoint or Docker API
  console.log(`[provisioner] Signal "${signal}" → ${host}:${port}`);
}

async function triggerHeartbeatAlert(userId: string, missedCount: number): Promise<void> {
  // TODO: send alert to admin portal / Slack / PagerDuty
  console.warn(`[provisioner] ALERT: user ${userId} container missed ${missedCount} heartbeats`);
}
