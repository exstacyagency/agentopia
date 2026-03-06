/**
 * @exstacyagency/agentopia
 * src/memory/ingest-pipeline.ts
 *
 * Watches per-user ingest/ directory in their container workspace.
 * On new file detection, chunks content, runs through Cortex extraction
 * prompt via Anthropic API, writes structured memories to memory_records,
 * and archives the processed file.
 *
 * Status is written to ingest_queue table — visible in the Ingest tab UI.
 *
 * Required additional deps (add to package.json):
 *   npm install @anthropic-ai/sdk chokidar openai uuid
 *   npm install -D @types/uuid @types/chokidar
 *
 * Depends on: lib/prisma.ts, types/index.ts, memory-store.ts
 */

import * as fs from "fs/promises";
import * as path from "path";
import { prisma } from "../lib/prisma.js";
import type { MemorySource, MemoryType } from "../types/index.js";

// ---------------------------------------------------------------------------
// Dependency interfaces
// Defined locally so the file typechecks without the packages installed.
// When the packages ARE installed their types satisfy these interfaces.
// ---------------------------------------------------------------------------

interface AnthropicClient {
  messages: {
    create(params: {
      model:     string;
      max_tokens: number;
      system:    string;
      messages:  Array<{ role: "user" | "assistant"; content: string }>;
    }): Promise<{
      content: Array<{ type: string; text?: string }>;
    }>;
  };
}

interface OpenAIClient {
  embeddings: {
    create(params: {
      model: string;
      input: string[];
    }): Promise<{
      data: Array<{ index: number; embedding: number[] }>;
    }>;
  };
}

interface ChokidarWatcher {
  on(event: "add",   handler: (filePath: string)  => void): this;
  on(event: "error", handler: (err: unknown) => void): this;
  close(): Promise<void>;
}

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export type IngestStatus =
  | "queued"
  | "processing"
  | "completed"
  | "failed";

export interface IngestQueueRecord {
  id:                string;
  userId:            string;
  fileName:          string;
  filePath:          string;
  status:            IngestStatus;
  memoriesExtracted: number;
  errorMessage:      string | null;
  createdAt:         Date;
  updatedAt:         Date;
  completedAt:       Date | null;
}

export interface ExtractedMemory {
  type:       MemoryType;
  content:    string;
  importance: number;
  domain:     string;
}

export interface IngestPipelineConfig {
  /** Initialised @anthropic-ai/sdk Anthropic instance */
  anthropicClient:  AnthropicClient;
  /** Initialised openai OpenAI instance */
  openaiClient:     OpenAIClient;
  /** Absolute path to cortex-extraction-prompt.md */
  cortexPromptPath: string;
  /** Base workspace path, e.g. /workspace */
  workspaceBasePath: string;
  /** Registered memory domains from platform init */
  registeredDomains: string[];
  /** Default: text-embedding-3-small */
  embeddingModel?:   string;
  /** Characters per chunk. Default: 6000 */
  chunkSize?:        number;
  /** Overlap between chunks. Default: 400 */
  chunkOverlap?:     number;
  /** Max concurrent extraction jobs. Default: 3 */
  maxConcurrentJobs?: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const INGEST_SUBDIR    = "ingest";
const PROCESSED_SUBDIR = "ingest/processed";

const SUPPORTED_EXTENSIONS = new Set([
  ".txt", ".md", ".csv", ".json", ".html", ".htm",
]);

const DEFAULT_CHUNK_SIZE      = 6_000;
const DEFAULT_CHUNK_OVERLAP   = 400;
const DEFAULT_CONCURRENCY     = 3;
const DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small";

// ---------------------------------------------------------------------------
// IngestPipeline
// ---------------------------------------------------------------------------

export class IngestPipeline {
  private watchers   = new Map<string, ChokidarWatcher>();
  private activeJobs = new Map<string, Promise<void>>();
  private cortexPromptCache: string | null = null;

  private readonly cfg: Required<IngestPipelineConfig>;

  constructor(config: IngestPipelineConfig) {
    this.cfg = {
      embeddingModel:    DEFAULT_EMBEDDING_MODEL,
      chunkSize:         DEFAULT_CHUNK_SIZE,
      chunkOverlap:      DEFAULT_CHUNK_OVERLAP,
      maxConcurrentJobs: DEFAULT_CONCURRENCY,
      ...config,
    };
  }

  // ── Public lifecycle ───────────────────────────────────────────────────

  /**
   * Start watching a user's ingest directory. Idempotent.
   * ignoreInitial: false → picks up files dropped while offline.
   */
  async watchUser(userId: string): Promise<void> {
    if (this.watchers.has(userId)) return;

    const ingestDir    = this.ingestPath(userId);
    const processedDir = this.processedPath(userId);

    await fs.mkdir(ingestDir,    { recursive: true });
    await fs.mkdir(processedDir, { recursive: true });

    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const chokidar = require("chokidar") as typeof import("chokidar");

    const watcher: ChokidarWatcher = chokidar.watch(ingestDir, {
      ignored:          [/(^|[/\\])\.\./, /processed/],
      persistent:       true,
      ignoreInitial:    false,
      awaitWriteFinish: { stabilityThreshold: 1500, pollInterval: 200 },
      depth:            0,
    });

    watcher.on("add", (filePath) => { void this.onFileAdded(userId, filePath); });
    watcher.on("error", (err)     => { console.error(`[IngestPipeline] watcher error uid=${userId}`, err); });

    this.watchers.set(userId, watcher);
    console.log(`[IngestPipeline] watching uid=${userId} path=${ingestDir}`);
  }

  async unwatchUser(userId: string): Promise<void> {
    const w = this.watchers.get(userId);
    if (!w) return;
    await w.close();
    this.watchers.delete(userId);
  }

  async shutdown(): Promise<void> {
    await Promise.all([...this.watchers.keys()].map((uid) => this.unwatchUser(uid)));
  }

  /**
   * Manually queue a file (called from Ingest tab UI upload handler).
   * Returns the ingest_queue record id.
   */
  async ingestFile(userId: string, filePath: string): Promise<string> {
    const jobId = await this.enqueue(userId, filePath);
    this.dispatch(jobId, userId, filePath);
    return jobId;
  }

  async getQueueStatus(userId: string, limit = 20): Promise<IngestQueueRecord[]> {
    return prisma.ingestQueue.findMany({
      where:   { userId },
      orderBy: { createdAt: "desc" },
      take:    limit,
    }) as Promise<IngestQueueRecord[]>;
  }

  // ── File detection ─────────────────────────────────────────────────────

  private async onFileAdded(userId: string, filePath: string): Promise<void> {
    const ext = path.extname(filePath).toLowerCase();
    if (!SUPPORTED_EXTENSIONS.has(ext)) return;

    // Idempotency — don't re-queue already-seen files
    const existing = await prisma.ingestQueue.findFirst({
      where: { userId, filePath, status: { in: ["queued", "processing", "completed"] } },
    });
    if (existing) return;

    // Throttle
    if (this.activeJobs.size >= this.cfg.maxConcurrentJobs) {
      setTimeout(() => void this.onFileAdded(userId, filePath), 5_000);
      return;
    }

    const jobId = await this.enqueue(userId, filePath);
    this.dispatch(jobId, userId, filePath);
  }

  // ── Queue management ───────────────────────────────────────────────────

  private async enqueue(userId: string, filePath: string): Promise<string> {
    const record = await prisma.ingestQueue.create({
      data: {
        userId,
        fileName:          path.basename(filePath),
        filePath,
        status:            "queued",
        memoriesExtracted: 0,
        errorMessage:      null,
        completedAt:       null,
      },
    });
    return record.id;
  }

  private dispatch(jobId: string, userId: string, filePath: string): void {
    const job = this.runJob(jobId, userId, filePath).finally(() => {
      this.activeJobs.delete(jobId);
    });
    this.activeJobs.set(jobId, job);
  }

  // ── Core job ───────────────────────────────────────────────────────────

  private async runJob(jobId: string, userId: string, filePath: string): Promise<void> {
    console.log(`[IngestPipeline] start jobId=${jobId} file=${path.basename(filePath)}`);
    await this.setStatus(jobId, "processing");

    try {
      const text     = await fs.readFile(filePath, "utf-8");
      const chunks   = this.chunk(text);
      const prompt   = await this.loadCortexPrompt();
      const memories = await this.extractAll(chunks, prompt);
      const deduped  = this.deduplicate(memories);

      await this.writeMemories(userId, deduped);
      await this.archiveFile(filePath, userId);

      await prisma.ingestQueue.update({
        where: { id: jobId },
        data:  {
          status:            "completed",
          memoriesExtracted: deduped.length,
          completedAt:       new Date(),
        },
      });

      console.log(`[IngestPipeline] done jobId=${jobId} memories=${deduped.length}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(`[IngestPipeline] failed jobId=${jobId}`, err);
      await this.setStatus(jobId, "failed", msg);
    }
  }

  // ── Chunking ───────────────────────────────────────────────────────────

  private chunk(text: string): string[] {
    const { chunkSize, chunkOverlap } = this.cfg;
    const chunks: string[] = [];
    let start = 0;

    while (start < text.length) {
      const end   = Math.min(start + chunkSize, text.length);
      const slice = text.slice(start, end);
      if (slice.trim().length > 50) chunks.push(slice);
      if (end === text.length) break;
      start = end - chunkOverlap;
    }

    return chunks;
  }

  // ── Extraction ─────────────────────────────────────────────────────────

  private async extractAll(chunks: string[], prompt: string): Promise<ExtractedMemory[]> {
    const all: ExtractedMemory[] = [];
    for (const c of chunks) {
      const extracted = await this.extractChunk(c, prompt);
      all.push(...extracted);
    }
    return all;
  }

  private async extractChunk(chunk: string, prompt: string): Promise<ExtractedMemory[]> {
    const validDomains = this.cfg.registeredDomains.join(", ");

    const userMsg = [
      "Extract structured memories from the content below.",
      "",
      `REGISTERED DOMAINS: ${validDomains}`,
      'Assign each memory to the most relevant domain, or "general" if none fit.',
      "",
      "Return ONLY a JSON array — no preamble, no markdown fences. Each element:",
      "{",
      '  "type": "<Fact|Preference|Decision|Identity|Event|Observation|Goal|Todo>",',
      '  "content": "<concise, self-contained memory statement>",',
      '  "importance": <0.0–1.0 float>,',
      '  "domain": "<one of the registered domains>"',
      "}",
      "",
      "CONTENT:",
      "---",
      chunk,
      "---",
    ].join("\n");

    const response = await this.cfg.anthropicClient.messages.create({
      model:      "claude-haiku-4-5",
      max_tokens: 2048,
      system:     prompt,
      messages:   [{ role: "user", content: userMsg }],
    });

    const raw = response.content[0].type === "text"
      ? (response.content[0].text ?? "")
      : "";

    try {
      const cleaned = raw.replace(/```json|```/g, "").trim();
      const parsed  = JSON.parse(cleaned) as Array<{
        type:       string;
        content:    string;
        importance: number;
        domain:     string;
      }>;

      return parsed
        .filter((m) => typeof m.content === "string" && m.content.length > 0)
        .map((m) => ({
          type:       this.sanitiseType(m.type),
          content:    m.content.slice(0, 2_000),
          importance: Math.max(0, Math.min(1, Number(m.importance) || 0.5)),
          domain:     this.cfg.registeredDomains.includes(m.domain) ? m.domain : "general",
        }));
    } catch {
      console.warn("[IngestPipeline] extraction parse failed — skipping chunk");
      return [];
    }
  }

  // ── Deduplication ──────────────────────────────────────────────────────

  private deduplicate(memories: ExtractedMemory[]): ExtractedMemory[] {
    const seen = new Set<string>();
    return memories.filter((m) => {
      const key = `${m.type}:${m.content.toLowerCase().trim()}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  // ── Write to memory_records ────────────────────────────────────────────

  private async writeMemories(userId: string, memories: ExtractedMemory[]): Promise<void> {
    if (memories.length === 0) return;

    const embeddings = await this.embedBatch(memories.map((m) => m.content));

    const records = memories.map((m, i) => ({
      userId,
      type:           m.type    as MemoryType,
      domain:         m.domain,
      content:        m.content,
      importance:     m.importance,
      embedding:      JSON.stringify(embeddings[i]),
      source:         "ingest" as MemorySource,
      pinned:         false,
      archived:       false,
      lastAccessedAt: new Date(),
    }));

    await prisma.memoryRecord.createMany({ data: records });
    console.log(`[IngestPipeline] wrote ${records.length} memories uid=${userId}`);
  }

  // ── Embeddings ─────────────────────────────────────────────────────────

  private async embedBatch(texts: string[]): Promise<number[][]> {
    const response = await this.cfg.openaiClient.embeddings.create({
      model: this.cfg.embeddingModel,
      input: texts,
    });

    return response.data
      .sort((a, b) => a.index - b.index)
      .map((d) => d.embedding);
  }

  // ── File archival ──────────────────────────────────────────────────────

  private async archiveFile(filePath: string, userId: string): Promise<void> {
    const dest = path.join(
      this.processedPath(userId),
      `${Date.now()}_${path.basename(filePath)}`
    );
    await fs.mkdir(path.dirname(dest), { recursive: true });
    await fs.rename(filePath, dest);
    console.log(`[IngestPipeline] archived → ${path.basename(dest)}`);
  }

  // ── Cortex prompt (cached) ─────────────────────────────────────────────

  private async loadCortexPrompt(): Promise<string> {
    if (this.cortexPromptCache) return this.cortexPromptCache;

    try {
      this.cortexPromptCache = await fs.readFile(this.cfg.cortexPromptPath, "utf-8");
    } catch {
      console.warn(`[IngestPipeline] cortex prompt not found at ${this.cfg.cortexPromptPath} — using fallback`);
      this.cortexPromptCache =
        "You are a memory extraction assistant. Extract structured, factual memories from the provided content. Be precise and concise.";
    }

    return this.cortexPromptCache;
  }

  // ── Path helpers ───────────────────────────────────────────────────────

  private ingestPath(userId: string): string {
    return path.join(this.cfg.workspaceBasePath, userId, INGEST_SUBDIR);
  }

  private processedPath(userId: string): string {
    return path.join(this.cfg.workspaceBasePath, userId, PROCESSED_SUBDIR);
  }

  // ── Status helper ──────────────────────────────────────────────────────

  private async setStatus(
    jobId:        string,
    status:       IngestStatus,
    errorMessage: string | null = null
  ): Promise<void> {
    await prisma.ingestQueue.update({
      where: { id: jobId },
      data:  { status, errorMessage },
    });
  }

  private sanitiseType(raw: string): MemoryType {
    const valid: MemoryType[] = [
      "Fact", "Preference", "Decision", "Identity",
      "Event", "Observation", "Goal", "Todo",
    ];
    return (valid as string[]).includes(raw) ? (raw as MemoryType) : "Fact";
  }
}
