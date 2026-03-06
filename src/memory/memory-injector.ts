/**
 * memory-injector.ts
 * @exstacyagency/agentopia
 *
 * Generates MEMORY.md fresh before every session start.
 * Uses hybrid search (RRF merge) for recall, pulls first-degree graph
 * neighbours for context, renders structured markdown by memory type,
 * and writes to the user's container workspace.
 *
 * OpenClaw injects workspace files into system context automatically —
 * this file just has to exist at the right path before session spawn.
 *
 * Depends on: hybrid-search, memory-store (getNeighbours), types/index.ts
 */

import * as fs from "fs/promises";
import * as path from "path";
import { hybridSearch, type HybridSearchResult } from "./hybrid-search.js";
import { getNeighbours } from "./memory-store.js";
import type { MemoryRecord, MemoryType } from "./memory-store.js";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

/** Max records to include in MEMORY.md after all filtering/merging */
const MAX_INJECTED_MEMORIES = 50;
/** Top N from hybrid search before graph expansion */
const HYBRID_SEARCH_LIMIT = 20;
/** Domain filter: always include general memories alongside job domain */
const GENERAL_DOMAIN = "general";

// Section order in the rendered file
const SECTION_ORDER: MemoryType[] = [
  "Identity",
  "Goal",
  "Preference",
  "Fact",
  "Decision",
  "Observation",
  "Event",
  "Todo",
];

// ---------------------------------------------------------------------------
// Input / output
// ---------------------------------------------------------------------------

export interface InjectorInput {
  userId: string;
  jobType: string;
  /** Domain for this job (e.g. 'research', 'creative', 'general') */
  domain: string;
  /** The incoming message — used as hybrid search query */
  incomingMessage: string;
  /** Pre-computed embedding for incomingMessage */
  queryEmbedding: number[];
  /** Workspace root for this user's container. Default: /workspace/{userId} */
  workspaceRoot?: string;
}

export interface InjectorResult {
  memoriesInjected: number;
  filePath: string;
  durationMs: number;
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

export async function injectMemory(input: InjectorInput): Promise<InjectorResult> {
  const start = Date.now();
  const {
    userId,
    domain,
    incomingMessage,
    queryEmbedding,
    workspaceRoot = `/workspace/${userId}`,
  } = input;

  // Step 1 — Domain filter: top 40 by importance for job domain + general
  const domainResults = await hybridSearch({
    userId,
    query: incomingMessage,
    queryEmbedding,
    domain,
    limit: HYBRID_SEARCH_LIMIT,
  });

  const generalResults =
    domain !== GENERAL_DOMAIN
      ? await hybridSearch({
          userId,
          query: incomingMessage,
          queryEmbedding,
          domain: GENERAL_DOMAIN,
          limit: HYBRID_SEARCH_LIMIT,
        })
      : [];

  // Step 2 — Merge domain + general, deduplicate by id
  const seen = new Set<string>();
  const merged: HybridSearchResult[] = [];
  for (const r of [...domainResults, ...generalResults]) {
    if (!seen.has(r.id)) {
      seen.add(r.id);
      merged.push(r);
    }
  }

  // Step 3 — Graph context: first-degree neighbours for top results
  const topIds = merged.slice(0, 10).map((r) => r.id);
  const neighbourRecords = await fetchNeighbours(userId, topIds, seen);

  // Step 4 — Combine, deduplicate, sort by importance desc
  const all: MemoryRecord[] = [...merged, ...neighbourRecords];
  all.sort((a, b) => b.importance - a.importance);

  // Step 5 — Trim to MAX_INJECTED_MEMORIES
  const final = all.slice(0, MAX_INJECTED_MEMORIES);

  // Step 6 — Render MEMORY.md
  const markdown = renderMemoryMd(final);

  // Step 7 — Write to workspace
  const filePath = path.join(workspaceRoot, "MEMORY.md");
  await fs.mkdir(workspaceRoot, { recursive: true });
  await fs.writeFile(filePath, markdown, "utf8");

  return {
    memoriesInjected: final.length,
    filePath,
    durationMs: Date.now() - start,
  };
}

// ---------------------------------------------------------------------------
// Graph neighbour fetch
// ---------------------------------------------------------------------------

async function fetchNeighbours(
  userId: string,
  seedIds: string[],
  alreadySeen: Set<string>
): Promise<MemoryRecord[]> {
  if (seedIds.length === 0) return [];

  const neighbours = await getNeighbours(seedIds, ["RelatedTo", "Updates"]);
  const results: MemoryRecord[] = [];

  for (const n of neighbours) {
    if (!alreadySeen.has(n.id) && n.userId === userId && !n.archived) {
      alreadySeen.add(n.id);
      results.push(n);
    }
  }

  return results;
}

// ---------------------------------------------------------------------------
// Renderer
// ---------------------------------------------------------------------------

function renderMemoryMd(records: MemoryRecord[]): string {
  const byType = new Map<MemoryType, MemoryRecord[]>();

  for (const r of records) {
    const type = r.type as MemoryType;
    if (!byType.has(type)) byType.set(type, []);
    byType.get(type)!.push(r);
  }

  const sections: string[] = [
    "# MEMORY",
    "",
    "> Auto-generated before session start. Do not edit — changes will be overwritten.",
    "",
  ];

  for (const type of SECTION_ORDER) {
    const entries = byType.get(type);
    if (!entries || entries.length === 0) continue;

    sections.push(`## ${type}`);
    sections.push("");

    for (const entry of entries) {
      const pinned = entry.pinned ? " 📌" : "";
      const importance = `[${(entry.importance * 100).toFixed(0)}%]`;
      sections.push(`- ${importance}${pinned} ${entry.content}`);
    }

    sections.push("");
  }

  if (records.length === 0) {
    sections.push("_No memories found for this session._");
    sections.push("");
  }

  sections.push(`---`);
  sections.push(`_Generated: ${new Date().toISOString()} · ${records.length} memories_`);

  return sections.join("\n");
}
