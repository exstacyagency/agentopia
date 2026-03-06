// ─── Model Tiers ────────────────────────────────────────────────
export type ModelTier = 'haiku' | 'sonnet' | 'opus'
export type RoutingProfile = 'eco' | 'balanced' | 'premium'
export type ComplexityScore = 'light' | 'standard' | 'heavy'

// ─── Tool Permissions ───────────────────────────────────────────
export type ToolPermission =
  | 'sessions_spawn'
  | 'sessions_send'
  | 'sessions_history'
  | 'browser'
  | 'exec'
  | 'file_read'
  | 'file_write'
  | 'web_search'

// ─── Memory ─────────────────────────────────────────────────────
export type MemoryType =
  | 'Fact'
  | 'Preference'
  | 'Decision'
  | 'Identity'
  | 'Event'
  | 'Observation'
  | 'Goal'
  | 'Todo'

export type EdgeType =
  | 'RelatedTo'
  | 'Updates'
  | 'Contradicts'
  | 'CausedBy'
  | 'PartOf'

export type MemorySource =
  | 'cortex'
  | 'user'
  | 'job_completion'
  | 'admin'
  | 'ingest'

export interface MemoryRecord {
  id: string
  userId: string
  type: MemoryType
  domain: string
  content: string
  importance: number
  embedding: number[]
  pinned: boolean
  archived: boolean
  source: MemorySource
  supersededBy: string | null
  createdAt: Date
  lastAccessedAt: Date
}

export interface MemoryEdge {
  id: string
  fromId: string
  toId: string
  type: EdgeType
  createdAt: Date
}

// ─── Job Registry ───────────────────────────────────────────────
export interface JobTypeDefinition {
  id: string
  domain: string
  agentSlot: string
  defaultModel: ModelTier
  timeoutSeconds: number
  tools: ToolPermission[]
}

export interface RegisteredJobType {
  id:                    string;
  domain:                string;
  agent:                 string;
  timeout:               number;
  modelOverride?:        string;   // forces a specific model regardless of routing profile
  estimatedInputTokens?: number;   // used by pricing-catalog for upfront cost estimate
  estimatedOutputTokens?: number;
}

export type JobTypeRegistry = Map<string, RegisteredJobType>;

// ─── Agent Slots ────────────────────────────────────────────────
export interface AgentSlotDefinition {
  slot: string
  model: string
  tools: string[]
  background?: boolean
  ephemeral?: boolean
  modelOverride?: string
}

export interface ProvisionedContainer {
  userId: string
  host: string
  port: number
  gatewayToken: string
  status: string
}

// ─── Routing ────────────────────────────────────────────────────
export interface RoutingConfig {
  profile: RoutingProfile
  coalesceWindowMs: number
}

export interface RoutingProfileMap {
  light: ModelTier
  standard: ModelTier
  heavy: ModelTier
}

export const ROUTING_PROFILES: Record<RoutingProfile, RoutingProfileMap> = {
  eco:      { light: 'haiku',  standard: 'haiku',  heavy: 'sonnet' },
  balanced: { light: 'haiku',  standard: 'sonnet', heavy: 'opus'   },
  premium:  { light: 'sonnet', standard: 'sonnet', heavy: 'opus'   },
}

// ─── Memory Config ──────────────────────────────────────────────
export interface DecayConfig {
  Fact: number
  Preference: number
  Decision: number
  Identity: number
  Goal: number
  Observation: number
  Event: number
  Todo: number
}

export interface MemoryConfig {
  domains: string[]
  decayConfig: DecayConfig
  embeddingModel: string
  hybridSearch: boolean
}

// ─── Compaction ─────────────────────────────────────────────────
export interface CompactionThresholds {
  background: number
  aggressive: number
  emergency: number
}

export interface CompactionConfig {
  enabled: boolean
  thresholds: CompactionThresholds
}

// ─── Cron ───────────────────────────────────────────────────────
export interface CronConfig {
  enabled: boolean
}

// ─── Jobs ───────────────────────────────────────────────────────
export type JobStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'dead_letter'

export interface RunningTurn {
  id: string
  userId: string
  agentSlot: string
  sessionId: string
  jobType: string
  startedAt: Date
  timeoutSeconds: number
  status: JobStatus
  retryCount: number
}

// ─── Channel Routing ────────────────────────────────────────────
export type Platform =
  | 'discord'
  | 'telegram'
  | 'whatsapp'
  | 'slack'
  | 'signal'

export interface ChannelRoute {
  id: string
  userId: string
  containerId: string
  platform: Platform
  platformUserId: string
  platformChannelId: string
  gatewayPort: number
  gatewayToken: string
  active: boolean
  lastMessageAt?: Date
}

// ─── Platform Config ────────────────────────────────────────────
export interface AgentPlatformConfig {
  database: string
  anthropicKeyPool: string[]
  containerHost: string
  agents: AgentSlotDefinition[]
  jobs: JobTypeDefinition[]
  memory: MemoryConfig
  routing: RoutingConfig
  compaction: CompactionConfig
  cron: CronConfig
  cortexPromptPath: string
  soulPath: string
}
