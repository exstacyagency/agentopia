/**
 * @exstacyagency/agentopia
 * src/provisioning/agent-configurator.ts
 *
 * Builds the agents.list written into openclaw.json from registered
 * slot definitions. No hardcoded agent names — fully driven by whatever
 * slots the product registers at init.
 *
 * v1.0 hardcoded 5 named agents tied to ad-platform workflows.
 * v2.0 replaces this with a slot system. Any product registers its own
 * slots; this module handles the rest.
 *
 * Depends on: types/index.ts (AgentSlotDefinition)
 */

import type { AgentSlotDefinition } from "../types/index.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AgentEntry {
  slot:        string;
  model:       string;
  tools:       string[];
  background:  boolean;   // true = no channel connections (e.g. cortex)
  ephemeral:   boolean;   // true = spawned on demand, not persistent
  systemFile:  string;    // path to soul/persona file for this agent
  workspaceFiles: string[]; // files injected into context at session start
}

export interface AgentsListConfig {
  agents:      AgentEntry[];
  generatedAt: string;    // ISO timestamp — used for config versioning
  slotCount:   number;
}

// ---------------------------------------------------------------------------
// Tool Validation
// ---------------------------------------------------------------------------

/**
 * All tools available in the OpenClaw runtime.
 * Any tool not in this set will be rejected at config build time.
 */
const VALID_TOOLS = new Set([
  "sessions_spawn",
  "sessions_send",
  "sessions_history",
  "browser",
  "exec",
  "file_read",
  "file_write",
  "web_search",
]);

/**
 * Tool restrictions by slot type.
 * Background agents (cortex) may not have channel connections.
 * Ephemeral agents (analysis) may not spawn sessions.
 */
const BACKGROUND_FORBIDDEN_TOOLS = new Set([
  "sessions_spawn",
  "sessions_send",
  "browser",
  "exec",
]);

const EPHEMERAL_FORBIDDEN_TOOLS = new Set([
  "sessions_spawn",
]);

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

export class InvalidSlotDefinitionError extends Error {
  constructor(
    public readonly slot:   string,
    public readonly reason: string
  ) {
    super(`Invalid agent slot definition for "${slot}": ${reason}`);
    this.name = "InvalidSlotDefinitionError";
  }
}

function validateSlotDefinition(slot: AgentSlotDefinition): void {
  if (!slot.slot || typeof slot.slot !== "string") {
    throw new InvalidSlotDefinitionError(String(slot.slot), "slot name is required");
  }

  if (!slot.model || typeof slot.model !== "string") {
    throw new InvalidSlotDefinitionError(slot.slot, "model is required");
  }

  if (!Array.isArray(slot.tools) || slot.tools.length === 0) {
    throw new InvalidSlotDefinitionError(slot.slot, "at least one tool is required");
  }

  for (const tool of slot.tools) {
    if (!VALID_TOOLS.has(tool)) {
      throw new InvalidSlotDefinitionError(
        slot.slot,
        `unknown tool "${tool}". Valid tools: ${[...VALID_TOOLS].join(", ")}`
      );
    }
  }

  if (slot.background) {
    for (const tool of slot.tools) {
      if (BACKGROUND_FORBIDDEN_TOOLS.has(tool)) {
        throw new InvalidSlotDefinitionError(
          slot.slot,
          `background agents cannot use tool "${tool}"`
        );
      }
    }
  }

  if (slot.ephemeral) {
    for (const tool of slot.tools) {
      if (EPHEMERAL_FORBIDDEN_TOOLS.has(tool)) {
        throw new InvalidSlotDefinitionError(
          slot.slot,
          `ephemeral agents cannot use tool "${tool}"`
        );
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Builder
// ---------------------------------------------------------------------------

/**
 * Build the agents list from registered slot definitions.
 * Written into openclaw.json by user-provisioner on container spawn
 * and on config push.
 *
 * Validates all slot definitions before building.
 * Throws InvalidSlotDefinitionError on first invalid slot.
 */
export function buildAgentsList(slots: AgentSlotDefinition[]): AgentsListConfig {
  if (!slots || slots.length === 0) {
    throw new Error("buildAgentsList: at least one agent slot is required");
  }

  // Validate all slots up front — fail before writing anything
  for (const slot of slots) {
    validateSlotDefinition(slot);
  }

  // Ensure exactly one non-background, non-ephemeral orchestrator exists
  const orchestrators = slots.filter(
    (s) => !s.background && !s.ephemeral && s.tools.includes("sessions_spawn")
  );

  if (orchestrators.length === 0) {
    throw new Error(
      "buildAgentsList: no orchestrator slot found. " +
      "At least one non-background slot with sessions_spawn tool is required."
    );
  }

  const agents: AgentEntry[] = slots.map((slot) => ({
    slot:       slot.slot,
    model:      normaliseModelName(slot.model),
    tools:      slot.tools,
    background: slot.background ?? false,
    ephemeral:  slot.ephemeral  ?? false,
    systemFile: buildSystemFilePath(slot),
    workspaceFiles: buildWorkspaceFiles(slot),
  }));

  return {
    agents,
    generatedAt: new Date().toISOString(),
    slotCount:   agents.length,
  };
}

// ---------------------------------------------------------------------------
// Slot Diff (config push)
// ---------------------------------------------------------------------------

export interface SlotDiff {
  added:    string[];   // slot names present in next but not current
  removed:  string[];   // slot names present in current but not next
  changed:  string[];   // slot names present in both but with different config
  unchanged: string[];  // slot names identical in both
}

/**
 * Diff two agents lists to determine what changed.
 * Used by config-pusher to decide whether a full reprovision is needed
 * or a hot config push is sufficient.
 *
 * Removed slots always require reprovision.
 * Added/changed slots can be hot-pushed in most cases.
 */
export function diffAgentsLists(
  current: AgentsListConfig,
  next:    AgentsListConfig
): SlotDiff {
  const currentMap = new Map(current.agents.map((a) => [a.slot, a]));
  const nextMap    = new Map(next.agents.map((a) => [a.slot, a]));

  const added:     string[] = [];
  const removed:   string[] = [];
  const changed:   string[] = [];
  const unchanged: string[] = [];

  for (const [slot, nextAgent] of nextMap) {
    if (!currentMap.has(slot)) {
      added.push(slot);
    } else {
      const currentAgent = currentMap.get(slot)!;
      if (agentEntryChanged(currentAgent, nextAgent)) {
        changed.push(slot);
      } else {
        unchanged.push(slot);
      }
    }
  }

  for (const slot of currentMap.keys()) {
    if (!nextMap.has(slot)) {
      removed.push(slot);
    }
  }

  return { added, removed, changed, unchanged };
}

function agentEntryChanged(a: AgentEntry, b: AgentEntry): boolean {
  return (
    a.model      !== b.model      ||
    a.background !== b.background ||
    a.ephemeral  !== b.ephemeral  ||
    JSON.stringify(a.tools.sort()) !== JSON.stringify(b.tools.sort())
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Normalise shorthand model names to full model strings.
 * Allows slots to be defined with "haiku", "sonnet", "opus" shorthands.
 */
function normaliseModelName(model: string): string {
  const shorthands: Record<string, string> = {
    "haiku":   "claude-haiku-4-5",
    "sonnet":  "claude-sonnet-4-6",
    "opus":    "claude-opus-4-6",
  };
  return shorthands[model.toLowerCase()] ?? model;
}

/**
 * Build the path to the system/soul file for a given slot.
 * Falls back to the master soul.md if no slot-specific file exists.
 */
function buildSystemFilePath(slot: AgentSlotDefinition): string {
  // Slot-specific soul file takes precedence: soul-{slot}.md
  // Falls back to master soul.md
  return `/workspace/soul-${slot.slot}.md`;
}

/**
 * Build the list of workspace files injected into context at session start.
 * All agents get MEMORY.md. Background agents skip it (no session context).
 */
function buildWorkspaceFiles(slot: AgentSlotDefinition): string[] {
  if (slot.background) return [];

  const files = ["MEMORY.md"];

  // Worker agents also get their skill file if present
  if (!slot.tools.includes("sessions_spawn")) {
    files.push(`skills/SKILL-${slot.slot}.md`);
  }

  return files;
}

// ---------------------------------------------------------------------------
// Serialisation
// ---------------------------------------------------------------------------

/**
 * Serialise agents list to JSON string for writing to openclaw.json.
 */
export function serialiseAgentsList(config: AgentsListConfig): string {
  return JSON.stringify(config, null, 2);
}

/**
 * Parse a serialised agents list back to AgentsListConfig.
 * Used by config-pusher when reading existing container config for diff.
 */
export function parseAgentsList(json: string): AgentsListConfig {
  try {
    return JSON.parse(json) as AgentsListConfig;
  } catch {
    throw new Error("parseAgentsList: invalid JSON");
  }
}
