/**
 * hybrid-search.ts
 * @exstacyagency/agentopia
 *
 * Hybrid memory search: RRF (Reciprocal Rank Fusion) merge of
 * pgvector cosine similarity + Postgres tsvector full-text search.
 *
 * Better than vector-only for exact-match names, brand terms, and
 * short keyword queries where semantic similarity undershoots.
 *
 * Depends on: memory-store (vectorSearch, listMemories), types/index.ts
 */

import { prisma } from "../lib/prisma.js";
import { vectorSearch } from "./memory-store.js";
import type { MemoryRecord, MemoryType } from "./memory-store.js";

// ---------------------------------------------------------------------------
// RRF config
// ---------------------------------------------------------------------------

/** Standard RRF constant. 60 is the de-facto default from the original paper. */
const RRF_K = 60;

// ---------------------------------------------------------------------------
// Input / output types
// ---------------------------------------------------------------------------

export interface HybridSearchOptions {
  userId: string;
  /** The raw query string — used for full-text AND embedding generation */
  query: string;
  /** Pre-computed embedding for the query. Caller is responsible for generating. */
  queryEmbedding: number[];
  domain?: string;
  types?: MemoryType[];
  /** Max results to return after merge. Default: 20 */
  limit?: number;
  /** Minimum vector similarity threshold (0.0–1.0). Default: 0.65 */
  vectorThreshold?: number;
  includeArchived?: boolean;
}

export interface HybridSearchResult extends MemoryRecord {
  /** Final RRF score — higher is better */
  rrfScore: number;
  /** Rank in vector results (null if not found) */
  vectorRank: number | null;
  /** Rank in full-text results (null if not found) */
  fulltextRank: number | null;
  /** Raw vector similarity (null if not in vector results) */
  vectorSimilarity: number | null;
}

// ---------------------------------------------------------------------------
// Full-text search via Postgres tsvector
// ---------------------------------------------------------------------------

interface FulltextRow {
  id: string;
  rank: number;
}

async function fulltextSearch(
  userId: string,
  query: string,
  domain: string | undefined,
  types: MemoryType[] | undefined,
  limit: number,
  includeArchived: boolean
): Promise<FulltextRow[]> {
  // Sanitise query for tsquery: strip special chars, join with & for AND search
  const sanitised = query
    .replace(/[^a-zA-Z0-9\s]/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .join(" & ");

  if (!sanitised) return [];

  const domainClause = domain ? `AND domain = '${domain}'` : "";
  const typeClause =
    types && types.length > 0
      ? `AND type = ANY(ARRAY[${types.map((t) => `'${t}'`).join(",")}]::text[])`
      : "";
  const archivedClause = includeArchived ? "" : "AND archived = false";

  const rows = await prisma.$queryRawUnsafe<FulltextRow[]>(`
    SELECT
      id,
      ts_rank(to_tsvector('english', content), to_tsquery('english', $1)) AS rank
    FROM memory_records
    WHERE
      user_id = $2
      AND to_tsvector('english', content) @@ to_tsquery('english', $1)
      ${domainClause}
      ${typeClause}
      ${archivedClause}
    ORDER BY rank DESC
    LIMIT $3
  `, sanitised, userId, limit);

  return rows;
}

// ---------------------------------------------------------------------------
// RRF merge
// ---------------------------------------------------------------------------

function rrfScore(rank: number): number {
  return 1 / (RRF_K + rank);
}

function mergeRRF(
  vectorResults: Array<MemoryRecord & { similarity: number }>,
  fulltextResults: FulltextRow[],
  limit: number
): {
  scores: Map<string, {
    rrfScore: number;
    vectorRank: number | null;
    fulltextRank: number | null;
    vectorSimilarity: number | null;
    record: MemoryRecord | null;
  }>;
  needsHydration: string[];
} {
  const scores = new Map<string, {
    rrfScore: number;
    vectorRank: number | null;
    fulltextRank: number | null;
    vectorSimilarity: number | null;
    record: MemoryRecord | null;
  }>();

  // Index vector results
  vectorResults.forEach((r, i) => {
    const rank = i + 1;
    scores.set(r.id, {
      rrfScore: rrfScore(rank),
      vectorRank: rank,
      fulltextRank: null,
      vectorSimilarity: r.similarity,
      record: r,
    });
  });

  // Merge fulltext results
  fulltextResults.forEach((r, i) => {
    const rank = i + 1;
    const existing = scores.get(r.id);
    if (existing) {
      existing.rrfScore += rrfScore(rank);
      existing.fulltextRank = rank;
    } else {
      // fulltext-only hit — record not in vector results, will be fetched below
      scores.set(r.id, {
        rrfScore: rrfScore(rank),
        vectorRank: null,
        fulltextRank: rank,
        vectorSimilarity: null,
        record: null, // hydrated below
      });
    }
  });

  // Collect IDs that need hydration (fulltext-only hits)
  const needsHydration = Array.from(scores.entries())
    .filter(([, v]) => v.record === null)
    .map(([id]) => id);

  return { scores, needsHydration };
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

export async function hybridSearch(options: HybridSearchOptions): Promise<HybridSearchResult[]> {
  const {
    userId,
    query,
    queryEmbedding,
    domain,
    types,
    limit = 20,
    vectorThreshold = 0.65,
    includeArchived = false,
  } = options;

  const fetchLimit = limit * 3; // cast wide, trim after merge

  // Run both searches in parallel
  const [vectorResults, ftResults] = await Promise.all([
    vectorSearch({
      userId,
      embedding: queryEmbedding,
      domain,
      types: types as unknown as Parameters<typeof vectorSearch>[0]['types'],
      limit: fetchLimit,
      threshold: vectorThreshold,
      includeArchived,
    }),
    fulltextSearch(userId, query, domain, types, fetchLimit, includeArchived),
  ]);

  // Merge
  const { scores, needsHydration } = mergeRRF(vectorResults, ftResults, limit);

  // Hydrate fulltext-only hits
  if (needsHydration.length > 0) {
    const hydrated = await prisma.memoryRecord.findMany({
      where: { id: { in: needsHydration } },
    });
    for (const row of hydrated) {
      const entry = scores.get(row.id);
      if (entry) {
        entry.record = {
          id: row.id,
          userId: row.userId,
          type: row.type as MemoryType,
          domain: row.domain,
          content: row.content,
          importance: row.importance,
          embedding: JSON.parse(row.embedding) as number[],
          pinned: row.pinned,
          archived: row.archived,
          source: row.source as MemoryRecord["source"],
          supersededBy: row.supersededBy ?? null,
          createdAt: row.createdAt,
          lastAccessedAt: row.lastAccessedAt,
        };
      }
    }
  }

  // Sort by RRF score descending, filter nulls, trim to limit
  return Array.from(scores.values())
    .filter((v) => v.record !== null)
    .sort((a, b) => b.rrfScore - a.rrfScore)
    .slice(0, limit)
    .map((v) => ({
      ...v.record!,
      rrfScore: v.rrfScore,
      vectorRank: v.vectorRank,
      fulltextRank: v.fulltextRank,
      vectorSimilarity: v.vectorSimilarity,
    }));
}
