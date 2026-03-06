/**
 * @exstacyagency/agentopia
 * src/memory/memory-store.ts
 *
 * Source of truth for all long-term memory. Postgres table partitioned
 * by user_id. pgvector enables semantic similarity search. memory_edges
 * stores typed relationships between records.
 *
 * Responsibilities:
 *   - CRUD for memory_records
 *   - CRUD for memory_edges
 *   - pgvector cosine similarity search
 *   - Importance decay application
 *   - Archive sweep
 *
 * Depends on: lib/prisma.ts, types/index.ts
 */

import { prisma } from "../lib/prisma.js";
import type { MemoryRecord, MemoryEdge, MemoryType, EdgeType, MemorySource } from "../types/index.js";
export type { MemoryRecord, MemoryEdge, MemoryType, EdgeType, MemorySource } from "../types/index.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CreateMemoryInput {
  userId:      string;
  type:        MemoryType;
  domain:      string;
  content:     string;
  importance:  number;
  embedding:   number[];
  source:      MemorySource;
  pinned?:     boolean;
}

export interface UpdateMemoryInput {
  content?:    string;
  importance?: number;
  embedding?:  number[];
  pinned?:     boolean;
  archived?:   boolean;
  supersededBy?: string;
}

export interface MemorySearchOptions {
  userId:      string;
  domain?:     string;
  types?:      MemoryType[];
  limit?:      number;
  includeArchived?: boolean;
}

export interface VectorSearchOptions extends MemorySearchOptions {
  embedding:   number[];
  threshold?:  number;   // minimum cosine similarity 0.0–1.0, default 0.7
}

// ---------------------------------------------------------------------------
// Decay Config
// Half-life in days per memory type — matches spec decay config
// ---------------------------------------------------------------------------

export const DEFAULT_DECAY_CONFIG: Record<MemoryType, number> = {
  Fact:        60,
  Preference:  180,
  Decision:    90,
  Goal:        45,
  Observation: 30,
  Event:       21,
  Todo:        14,
  Identity:    365,  // identity records decay very slowly
};

// ---------------------------------------------------------------------------
// Archive Threshold
// Records below this combined score are soft-archived on sweep
// ---------------------------------------------------------------------------

const ARCHIVE_IMPORTANCE_THRESHOLD = 0.15;

// ---------------------------------------------------------------------------
// CRUD — Memory Records
// ---------------------------------------------------------------------------

/**
 * Create a new memory record.
 * Embedding must be pre-computed by embedding-pipeline before calling this.
 */
export async function createMemory(input: CreateMemoryInput): Promise<MemoryRecord> {
  const {
    userId, type, domain, content, importance, embedding, source,
    pinned = false,
  } = input;

  if (importance < 0 || importance > 1) {
    throw new Error(`createMemory: importance must be between 0 and 1 (got ${importance})`);
  }

  if (embedding.length !== 1536) {
    throw new Error(`createMemory: embedding must be vector(1536) (got ${embedding.length})`);
  }

  const record = await prisma.memoryRecord.create({
    data: {
      userId,
      type,
      domain,
      content,
      importance,
      embedding:      JSON.stringify(embedding),  // stored as JSON, queried via pgvector
      createdAt:      new Date(),
      lastAccessedAt: new Date(),
      pinned,
      archived:       false,
      source,
      supersededBy:   null,
    },
  });

  return deserialiseMemory(record);
}

/**
 * Get a single memory record by ID.
 * Updates lastAccessedAt on read.
 */
export async function getMemory(id: string): Promise<MemoryRecord | null> {
  const record = await prisma.memoryRecord.findUnique({
    where: { id },
  });

  if (!record) return null;

  // Update access timestamp asynchronously — don't block the read
  void prisma.memoryRecord.update({
    where: { id },
    data:  { lastAccessedAt: new Date() },
  });

  return deserialiseMemory(record);
}

/**
 * Update a memory record.
 * Used by Cortex for reconciliation, and by user edits in the UI.
 */
export async function updateMemory(
  id:    string,
  input: UpdateMemoryInput
): Promise<MemoryRecord> {
  const data: Record<string, unknown> = {};

  if (input.content    !== undefined) data.content    = input.content;
  if (input.importance !== undefined) {
    if (input.importance < 0 || input.importance > 1) {
      throw new Error(`updateMemory: importance must be between 0 and 1`);
    }
    data.importance = input.importance;
  }
  if (input.embedding    !== undefined) data.embedding    = JSON.stringify(input.embedding);
  if (input.pinned       !== undefined) data.pinned       = input.pinned;
  if (input.archived     !== undefined) data.archived     = input.archived;
  if (input.supersededBy !== undefined) data.supersededBy = input.supersededBy;

  const record = await prisma.memoryRecord.update({
    where: { id },
    data,
  });

  return deserialiseMemory(record);
}

/**
 * Soft-archive a memory record.
 * Archived records are excluded from injection and search by default.
 * Hard deletion happens via the cleanup job after 30-day grace period.
 */
export async function archiveMemory(id: string): Promise<void> {
  await prisma.memoryRecord.update({
    where: { id },
    data:  { archived: true },
  });
}

/**
 * Restore a soft-archived record.
 * Available in the Memories tab UI.
 */
export async function restoreMemory(id: string): Promise<MemoryRecord> {
  const record = await prisma.memoryRecord.update({
    where: { id },
    data:  { archived: false },
  });
  return deserialiseMemory(record);
}

/**
 * Pin a memory record — pinned records are never archived by decay sweep.
 */
export async function pinMemory(id: string): Promise<void> {
  await prisma.memoryRecord.update({
    where: { id },
    data:  { pinned: true },
  });
}

export async function unpinMemory(id: string): Promise<void> {
  await prisma.memoryRecord.update({
    where: { id },
    data:  { pinned: false },
  });
}

// ---------------------------------------------------------------------------
// Query — Memory Records
// ---------------------------------------------------------------------------

/**
 * List memory records for a user with optional domain and type filtering.
 * Used by the Memories tab UI and the memory injector.
 */
export async function listMemories(
  options: MemorySearchOptions
): Promise<MemoryRecord[]> {
  const {
    userId,
    domain,
    types,
    limit            = 100,
    includeArchived  = false,
  } = options;

  const records = await prisma.memoryRecord.findMany({
    where: {
      userId,
      ...(domain  ? { domain }                    : {}),
      ...(types   ? { type: { in: types } }       : {}),
      ...(includeArchived ? {} : { archived: false }),
    },
    orderBy: [
      { pinned:    "desc" },
      { importance: "desc" },
      { createdAt:  "desc" },
    ],
    take: limit,
  });

  return records.map(deserialiseMemory);
}

/**
 * pgvector cosine similarity search.
 * Returns records ordered by semantic similarity to the query embedding.
 *
 * Note: This uses a raw query because Prisma does not yet support
 * pgvector operators natively. Requires pgvector extension installed.
 */
export async function vectorSearch(
  options: VectorSearchOptions
): Promise<Array<MemoryRecord & { similarity: number }>> {
  const {
    userId,
    embedding,
    domain,
    types,
    limit     = 20,
    threshold = 0.7,
    includeArchived = false,
  } = options;

  const vectorLiteral = `[${embedding.join(",")}]`;

  const domainClause    = domain ? `AND domain = '${domain}'`          : "";
  const typesClause     = types  ? `AND type IN (${types.map((t) => `'${t}'`).join(",")})` : "";
  const archivedClause  = includeArchived ? "" : "AND archived = false";

  const results = await prisma.$queryRawUnsafe<
    Array<Record<string, unknown>>
  >(
    `
    SELECT
      *,
      1 - (embedding::vector <=> '${vectorLiteral}'::vector) AS similarity
    FROM "MemoryRecord"
    WHERE
      "userId" = '${userId}'
      ${domainClause}
      ${typesClause}
      ${archivedClause}
      AND 1 - (embedding::vector <=> '${vectorLiteral}'::vector) >= ${threshold}
    ORDER BY similarity DESC
    LIMIT ${limit}
    `
  );

  return results.map((r: Record<string, unknown>) => ({
    ...deserialiseMemory(r as Parameters<typeof deserialiseMemory>[0]),
    similarity: Number(r["similarity"]),
  }));
}

/**
 * Get recently accessed memories for a user.
 * Used by Cortex to find sessions worth harvesting.
 */
export async function getRecentMemories(
  userId:  string,
  sinceMs: number = 24 * 60 * 60 * 1000   // last 24h default
): Promise<MemoryRecord[]> {
  const since = new Date(Date.now() - sinceMs);

  const records = await prisma.memoryRecord.findMany({
    where: {
      userId,
      archived:       false,
      lastAccessedAt: { gte: since },
    },
    orderBy: { lastAccessedAt: "desc" },
  });

  return records.map(deserialiseMemory);
}

// ---------------------------------------------------------------------------
// CRUD — Memory Edges
// ---------------------------------------------------------------------------

/**
 * Create a typed edge between two memory records.
 * Called by Cortex during reconciliation.
 */
export async function createEdge(
  fromId: string,
  toId:   string,
  type:   EdgeType
): Promise<MemoryEdge> {
  // Prevent self-referencing edges
  if (fromId === toId) {
    throw new Error("createEdge: fromId and toId must be different records");
  }

  const edge = await prisma.memoryEdge.create({
    data: {
      fromId,
      toId,
      type,
      createdAt: new Date(),
    },
  });

  return edge as MemoryEdge;
}

/**
 * Get all edges from a memory record (first-degree neighbours).
 * Used by memory injector to pull graph context for top results.
 */
export async function getEdgesFrom(fromId: string): Promise<MemoryEdge[]> {
  const edges = await prisma.memoryEdge.findMany({
    where: { fromId },
  });
  return edges as MemoryEdge[];
}

/**
 * Get all edges to a memory record.
 */
export async function getEdgesTo(toId: string): Promise<MemoryEdge[]> {
  const edges = await prisma.memoryEdge.findMany({
    where: { toId },
  });
  return edges as MemoryEdge[];
}

/**
 * Get first-degree neighbour records for a set of memory IDs.
 * Used by memory injector — pulls related records to enrich injection context.
 */
export async function getNeighbours(
  memoryIds:       string[],
  edgeTypes?:      EdgeType[]
): Promise<MemoryRecord[]> {
  const edges = await prisma.memoryEdge.findMany({
    where: {
      fromId: { in: memoryIds },
      ...(edgeTypes ? { type: { in: edgeTypes } } : {}),
    },
  });

  const neighbourIds = ([...new Set(edges.map((e: { toId: string }) => e.toId))] as string[]).filter(
    (id: string) => !memoryIds.includes(id)
  );

  if (neighbourIds.length === 0) return [];

  const records = await prisma.memoryRecord.findMany({
    where: { id: { in: neighbourIds }, archived: false },
  });

  return records.map(deserialiseMemory);
}

/**
 * Delete all edges involving a memory record.
 * Called before archiving a record to keep the graph clean.
 */
export async function deleteEdgesForRecord(memoryId: string): Promise<void> {
  await prisma.memoryEdge.deleteMany({
    where: {
      OR: [{ fromId: memoryId }, { toId: memoryId }],
    },
  });
}

// ---------------------------------------------------------------------------
// Importance Decay
// ---------------------------------------------------------------------------

/**
 * Apply importance decay to all non-pinned records for a user.
 * Decay is based on type half-life and days since last access.
 * Called by the Cortex scheduler on each run.
 */
export async function applyDecay(
  userId:      string,
  decayConfig: Record<MemoryType, number> = DEFAULT_DECAY_CONFIG
): Promise<{ updated: number }> {
  const records = await prisma.memoryRecord.findMany({
    where:  { userId, archived: false, pinned: false },
    select: { id: true, type: true, importance: true, lastAccessedAt: true },
  });

  let updated = 0;

  for (const record of (records as Array<{ id: string; type: string; importance: number; lastAccessedAt: Date }>)) {
    const halfLife    = decayConfig[record.type as MemoryType] ?? 30;
    const daysSince   = (Date.now() - record.lastAccessedAt.getTime()) / (1000 * 60 * 60 * 24);
    const decayFactor = Math.pow(0.5, daysSince / halfLife);
    const newImportance = Math.max(0, record.importance * decayFactor);

    if (Math.abs(newImportance - record.importance) > 0.001) {
      await prisma.memoryRecord.update({
        where: { id: record.id },
        data:  { importance: newImportance },
      });
      updated++;
    }
  }

  return { updated };
}

// ---------------------------------------------------------------------------
// Archive Sweep
// ---------------------------------------------------------------------------

/**
 * Soft-archive records below the combined importance threshold.
 * Pinned records are never archived.
 * Called by Cortex after decay application.
 */
export async function archiveSweep(userId: string): Promise<{ archived: number }> {
  const result = await prisma.memoryRecord.updateMany({
    where: {
      userId,
      archived:   false,
      pinned:     false,
      importance: { lt: ARCHIVE_IMPORTANCE_THRESHOLD },
    },
    data: { archived: true },
  });

  return { archived: result.count };
}

/**
 * Hard-delete records that have been archived for more than 30 days.
 * Called by the cleanup cron job.
 */
export async function hardDeleteExpiredArchives(userId: string): Promise<{ deleted: number }> {
  const cutoff = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);

  const expired = await prisma.memoryRecord.findMany({
    where: {
      userId,
      archived:  true,
      updatedAt: { lt: cutoff },
    },
    select: { id: true },
  });

  const ids = expired.map((r: { id: string }) => r.id);

  if (ids.length === 0) return { deleted: 0 };

  // Clean up edges first
  await prisma.memoryEdge.deleteMany({
    where: { OR: [{ fromId: { in: ids } }, { toId: { in: ids } }] },
  });

  const result = await prisma.memoryRecord.deleteMany({
    where: { id: { in: ids } },
  });

  return { deleted: result.count };
}

// ---------------------------------------------------------------------------
// Stats (admin portal + Cortex tab UI)
// ---------------------------------------------------------------------------

export interface MemoryStats {
  userId:        string;
  totalActive:   number;
  totalArchived: number;
  totalPinned:   number;
  byType:        Record<string, number>;
  byDomain:      Record<string, number>;
  bySource:      Record<string, number>;
}

export async function getMemoryStats(userId: string): Promise<MemoryStats> {
  const [active, archived, pinned, byType, byDomain, bySource] = await Promise.all([
    prisma.memoryRecord.count({ where: { userId, archived: false } }),
    prisma.memoryRecord.count({ where: { userId, archived: true  } }),
    prisma.memoryRecord.count({ where: { userId, pinned:   true  } }),
    prisma.memoryRecord.groupBy({
      by:    ["type"],
      where: { userId, archived: false },
      _count: { id: true },
    }),
    prisma.memoryRecord.groupBy({
      by:    ["domain"],
      where: { userId, archived: false },
      _count: { id: true },
    }),
    prisma.memoryRecord.groupBy({
      by:    ["source"],
      where: { userId, archived: false },
      _count: { id: true },
    }),
  ]);

  return {
    userId,
    totalActive:   active,
    totalArchived: archived,
    totalPinned:   pinned,
    byType:   Object.fromEntries(byType.map((r: { type: string; _count: { id: number } })   => [r.type,   r._count.id])),
    byDomain: Object.fromEntries(byDomain.map((r: { domain: string; _count: { id: number } }) => [r.domain, r._count.id])),
    bySource: Object.fromEntries(bySource.map((r: { source: string; _count: { id: number } }) => [r.source, r._count.id])),
  };
}

// ---------------------------------------------------------------------------
// Deserialisation
// ---------------------------------------------------------------------------

type RawMemoryRecord = {
  id:             string;
  userId:         string;
  type:           string;
  domain:         string;
  content:        string;
  importance:     number;
  embedding:      string | number[];
  createdAt:      Date;
  lastAccessedAt: Date;
  pinned:         boolean;
  archived:       boolean;
  source:         string;
  supersededBy:   string | null;
  updatedAt?:     Date;
};

function deserialiseMemory(raw: RawMemoryRecord): MemoryRecord {
  return {
    id:             raw.id,
    userId:         raw.userId,
    type:           raw.type        as MemoryType,
    domain:         raw.domain,
    content:        raw.content,
    importance:     raw.importance,
    embedding:      typeof raw.embedding === "string"
                      ? JSON.parse(raw.embedding) as number[]
                      : raw.embedding,
    createdAt:      raw.createdAt,
    lastAccessedAt: raw.lastAccessedAt,
    pinned:         raw.pinned,
    archived:       raw.archived,
    source:         raw.source      as MemorySource,
    supersededBy:   raw.supersededBy,
  };
}
