/**
 * @exstacyagency/agentopia
 * src/memory/cortex-extractor.ts
 *
 * Harvests session history after job completion, extracts structured
 * memories via LLM, embeds them, reconciles against existing records
 * (Updates / Contradicts / RelatedTo edges), and writes to memory_records.
 *
 * Two-phase pipeline per session:
 *   1. Extract  — LLM reads transcript, outputs typed memory candidates
 *   2. Reconcile — compare candidates against existing store; create
 *                  edges, supersede stale records, skip duplicates
 *
 * Called by cortex-scheduler.ts after turn completion.
 * Never blocks the request path — always runs async post-job.
 *
 * Depends on: memory-store, gateway-ws-client, models/model-router, types
 */

import * as fs            from "fs/promises";
import { prisma }         from "../lib/prisma.js";
import { gatewayFleet, type GatewayFleetManager } from "../orchestration/gateway-ws-client.js";
import { getModelRouter, type ModelRouter } from "../models/model-router.js";
import {
  createMemory,
  updateMemory,
  createEdge,
  vectorSearch,
  getMemory,
}                         from "./memory-store.js";
import type {
  MemoryType,
  EdgeType,
  MemorySource,
  MemoryRecord,
}                         from "../types/index.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CortexExtractorConfig {
  /** Absolute path to cortex-extraction-prompt.md */
  cortexPromptPath: string;
  /** OpenAI-compatible client for text-embedding-3-small */
  openaiClient:     OpenAIEmbeddingClient;
  /** Memory domains registered for the platform */
  registeredDomains: string[];
}

export interface GatewayClientLike {
  getHistory(sessionId: string): Promise<{ turns: Array<{ role: string; content: string }> }>;
}

export interface CortexRunResult {
  userId: string;
  memoriesCreated: number;
  edgesWritten: number;
  patternsFound: number;
  durationMs: number;
}

/** Minimal interface — satisfied by openai SDK OpenAI instance */
interface OpenAIEmbeddingClient {
  embeddings: {
    create(params: { model: string; input: string[] }): Promise<{
      data: Array<{ index: number; embedding: number[] }>;
    }>;
  };
}

export interface ExtractionInput {
  userId:    string;
  sessionId: string;
  domain:    string;
  jobType:   string;
}

export interface ExtractionResult {
  userId:        string;
  sessionId:     string;
  memoriesAdded: number;
  edgesCreated:  number;
  superseded:    number;
  durationMs:    number;
  skipped:       number;
}

interface RawMemoryCandidate {
  type:       string;
  content:    string;
  importance: number;
  domain:     string;
}

interface MemoryCandidate {
  type:       MemoryType;
  content:    string;
  importance: number;
  domain:     string;
  embedding:  number[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const EMBEDDING_MODEL          = "text-embedding-3-small";
const SIMILARITY_DUPLICATE_THRESHOLD = 0.93; // above → skip (already known)
const SIMILARITY_UPDATE_THRESHOLD    = 0.82; // above → potential Update/Contradicts
const SIMILARITY_RELATED_THRESHOLD   = 0.70; // above → RelatedTo edge
const MAX_HISTORY_CHARS        = 40_000;     // truncate very long transcripts
const MAX_CANDIDATES_PER_RUN   = 60;

const VALID_TYPES: MemoryType[] = [
  "Fact", "Preference", "Decision", "Identity",
  "Event", "Observation", "Goal", "Todo",
];

// ---------------------------------------------------------------------------
// CortexExtractor
// ---------------------------------------------------------------------------

export class CortexExtractor {
  private cfg:           CortexExtractorConfig;
  private promptCache:   string | null = null;
  private gatewayFleet:  GatewayFleetManager;
  private modelRouter:   ModelRouter;

  constructor(
    cfg: CortexExtractorConfig,
    gatewayFleetManager: GatewayFleetManager = gatewayFleet,
    modelRouter: ModelRouter = getModelRouter(),
  ) {
    this.cfg = cfg;
    this.gatewayFleet = gatewayFleetManager;
    this.modelRouter = modelRouter;
  }

  // ── Public ─────────────────────────────────────────────────────────────

  async run(
    userId: string,
    clients: Map<string, GatewayClientLike>,
    domains: string[],
  ): Promise<CortexRunResult> {
    const start = Date.now();
    const domain = domains[0] ?? "general";
    let memoriesCreated = 0;
    let edgesWritten = 0;
    let patternsFound = 0;

    for (const [sessionId, client] of clients.entries()) {
      let transcript: string | null = null;
      try {
        const history = await client.getHistory(sessionId);
        if (history.turns && history.turns.length > 0) {
          transcript = history.turns
            .map((t) => `${t.role.toUpperCase()}: ${t.content}`)
            .join("\n\n")
            .slice(0, MAX_HISTORY_CHARS);
        }
      } catch {
        transcript = null;
      }
      if (!transcript) continue;

      const rawCandidates = await this._llmExtract(transcript, domain, "cortex_cycle");
      if (rawCandidates.length === 0) continue;

      const candidates = await this._embedCandidates(rawCandidates);
      const { added, edgesCreated, superseded } = await this._reconcile(userId, candidates, domain);
      memoriesCreated += added;
      edgesWritten += edgesCreated;
      patternsFound += superseded;
    }

    return {
      userId,
      memoriesCreated,
      edgesWritten,
      patternsFound,
      durationMs: Date.now() - start,
    };
  }

  async extract(input: ExtractionInput): Promise<ExtractionResult> {
    const start = Date.now();
    const { userId, sessionId, domain, jobType } = input;

    // 1. Pull session transcript from gateway
    const transcript = await this._fetchTranscript(userId, sessionId);
    if (!transcript) {
      return this._emptyResult(userId, sessionId, start);
    }

    // 2. LLM extraction
    const rawCandidates = await this._llmExtract(transcript, domain, jobType);
    if (rawCandidates.length === 0) {
      return this._emptyResult(userId, sessionId, start);
    }

    // 3. Embed all candidates in one batch
    const candidates = await this._embedCandidates(rawCandidates);

    // 4. Reconcile against existing store
    const { added, edgesCreated, superseded, skipped } =
      await this._reconcile(userId, candidates, domain);

    return {
      userId,
      sessionId,
      memoriesAdded: added,
      edgesCreated,
      superseded,
      skipped,
      durationMs: Date.now() - start,
    };
  }

  // ── Transcript fetch ────────────────────────────────────────────────────

  private async _fetchTranscript(
    userId:    string,
    sessionId: string
  ): Promise<string | null> {
    const client = this.gatewayFleet.get(userId);
    if (!client) return null;

    try {
      const history = await client.getHistory(sessionId);
      if (!history.turns || history.turns.length === 0) return null;

      const text = history.turns
        .map((t: { role: string; content: string }) => `${t.role.toUpperCase()}: ${t.content}`)
        .join("\n\n");

      return text.slice(0, MAX_HISTORY_CHARS);
    } catch {
      return null;
    }
  }

  // ── LLM extraction ──────────────────────────────────────────────────────

  private async _llmExtract(
    transcript: string,
    domain:     string,
    jobType:    string
  ): Promise<RawMemoryCandidate[]> {
    const prompt    = await this._loadPrompt();
    const router    = this.modelRouter;
    const { key, model } = router.pick("haiku"); // cortex always runs on Haiku

    const validDomains = this.cfg.registeredDomains.join(", ");

    const userMsg = [
      `Extract durable memories from the following session transcript.`,
      ``,
      `JOB TYPE: ${jobType}`,
      `DOMAIN: ${domain}`,
      `REGISTERED DOMAINS: ${validDomains}`,
      ``,
      `Return ONLY a JSON array — no preamble, no markdown fences.`,
      `Max ${MAX_CANDIDATES_PER_RUN} entries. Each element:`,
      `{`,
      `  "type": "<Fact|Preference|Decision|Identity|Event|Observation|Goal|Todo>",`,
      `  "content": "<self-contained, third-person memory statement>",`,
      `  "importance": <0.0-1.0 float>,`,
      `  "domain": "<one of the registered domains>"`,
      `}`,
      ``,
      `Only extract memories that are likely to be useful in future sessions.`,
      `Skip pleasantries, filler, and session-specific transient details.`,
      ``,
      `TRANSCRIPT:`,
      `---`,
      transcript,
      `---`,
    ].join("\n");

    // Use Anthropic SDK via model router
    const Anthropic = (await import("@anthropic-ai/sdk")).default;
    const client    = new Anthropic({ apiKey: key });

    const response = await client.messages.create({
      model,
      max_tokens: 4096,
      system:     prompt,
      messages:   [{ role: "user", content: userMsg }],
    });

    const raw = response.content[0].type === "text"
      ? response.content[0].text
      : "";

    try {
      const parsed = JSON.parse(raw.replace(/```json|```/g, "").trim()) as RawMemoryCandidate[];
      return parsed
        .filter((c) => typeof c.content === "string" && c.content.length > 0)
        .slice(0, MAX_CANDIDATES_PER_RUN)
        .map((c) => ({
          type:       VALID_TYPES.includes(c.type as MemoryType) ? c.type : "Fact",
          content:    c.content.slice(0, 2_000),
          importance: Math.max(0, Math.min(1, Number(c.importance) || 0.5)),
          domain:     this.cfg.registeredDomains.includes(c.domain) ? c.domain : domain,
        }));
    } catch {
      console.warn("[CortexExtractor] JSON parse failed — no memories extracted");
      return [];
    }
  }

  // ── Embedding ───────────────────────────────────────────────────────────

  private async _embedCandidates(
    raws: RawMemoryCandidate[]
  ): Promise<MemoryCandidate[]> {
    const response = await this.cfg.openaiClient.embeddings.create({
      model: EMBEDDING_MODEL,
      input: raws.map((r) => r.content),
    });

    const embeddings = response.data
      .sort((a, b) => a.index - b.index)
      .map((d) => d.embedding);

    return raws.map((r, i) => ({
      type:      r.type as MemoryType,
      content:   r.content,
      importance: r.importance,
      domain:    r.domain,
      embedding: embeddings[i]!,
    }));
  }

  // ── Reconciliation ──────────────────────────────────────────────────────

  private async _reconcile(
    userId:     string,
    candidates: MemoryCandidate[],
    domain:     string
  ): Promise<{ added: number; edgesCreated: number; superseded: number; skipped: number }> {
    let added = 0, edgesCreated = 0, superseded = 0, skipped = 0;

    for (const candidate of candidates) {
      // Vector search for near-neighbours in same domain
      const neighbours = await vectorSearch({
        userId,
        embedding:  candidate.embedding,
        domain:     candidate.domain,
        threshold:  SIMILARITY_RELATED_THRESHOLD,
        limit:      5,
      });

      if (neighbours.length === 0) {
        // Genuinely new — write directly
        await this._writeMemory(userId, candidate);
        added++;
        continue;
      }

      const top = neighbours[0]!;

      if (top.similarity >= SIMILARITY_DUPLICATE_THRESHOLD) {
        // Effectively identical — skip to avoid noise
        skipped++;
        continue;
      }

      if (top.similarity >= SIMILARITY_UPDATE_THRESHOLD) {
        // High overlap — determine Updates vs Contradicts
        const edgeType = this._classifyRelation(candidate, top);

        const newRecord = await this._writeMemory(userId, candidate);
        added++;

        await createEdge(newRecord.id, top.id, edgeType);
        edgesCreated++;

        if (edgeType === "Updates") {
          // Supersede the old record
          await updateMemory(top.id, { supersededBy: newRecord.id, archived: true });
          superseded++;
        }
        continue;
      }

      // Moderate overlap — RelatedTo edge only, both records kept
      const newRecord = await this._writeMemory(userId, candidate);
      added++;

      for (const neighbour of neighbours) {
        if (neighbour.similarity >= SIMILARITY_RELATED_THRESHOLD) {
          await createEdge(newRecord.id, neighbour.id, "RelatedTo").catch(() => {});
          edgesCreated++;
        }
      }
    }

    return { added, edgesCreated, superseded, skipped };
  }

  // ── Edge classification ─────────────────────────────────────────────────

  private _classifyRelation(
    candidate: MemoryCandidate,
    existing:  MemoryRecord & { similarity: number }
  ): EdgeType {
    // Heuristic: if same type and high similarity, it's an update.
    // Contradictions would require semantic negation detection —
    // use Updates as conservative default; Contradicts reserved for
    // explicit negation signals in the content.
    const negationSignals = [
      "no longer", "not ", "never ", "cancelled", "reversed",
      "changed", "decided against", "won't", "doesn't",
    ];

    const hasNegation = negationSignals.some((s) =>
      candidate.content.toLowerCase().includes(s)
    );

    if (hasNegation && candidate.type === existing.type) {
      return "Contradicts";
    }

    return "Updates";
  }

  // ── Memory write ────────────────────────────────────────────────────────

  private async _writeMemory(
    userId:    string,
    candidate: MemoryCandidate
  ): Promise<MemoryRecord> {
    return createMemory({
      userId,
      type:       candidate.type,
      domain:     candidate.domain,
      content:    candidate.content,
      importance: candidate.importance,
      embedding:  candidate.embedding,
      source:     "cortex" as MemorySource,
    });
  }

  // ── Prompt cache ────────────────────────────────────────────────────────

  private async _loadPrompt(): Promise<string> {
    if (this.promptCache) return this.promptCache;
    try {
      this.promptCache = await fs.readFile(this.cfg.cortexPromptPath, "utf-8");
    } catch {
      console.warn(`[CortexExtractor] cortex prompt not found at ${this.cfg.cortexPromptPath} — using fallback`);
      this.promptCache =
        "You are a memory extraction assistant. Extract durable, structured memories from conversation transcripts. Be precise and conservative — only extract genuinely useful long-term facts.";
    }
    return this.promptCache;
  }

  // ── Helpers ─────────────────────────────────────────────────────────────

  private _emptyResult(
    userId:    string,
    sessionId: string,
    start:     number
  ): ExtractionResult {
    return {
      userId,
      sessionId,
      memoriesAdded: 0,
      edgesCreated:  0,
      superseded:    0,
      skipped:       0,
      durationMs:    Date.now() - start,
    };
  }
}

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

let _instance: CortexExtractor | null = null;

export function initCortexExtractor(cfg: CortexExtractorConfig): CortexExtractor {
  _instance = new CortexExtractor(cfg);
  return _instance;
}

export function getCortexExtractor(): CortexExtractor {
  if (!_instance) throw new Error("CortexExtractor not initialised — call initCortexExtractor first");
  return _instance;
}
