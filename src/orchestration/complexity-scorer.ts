/**
 * complexity-scorer.ts
 * @exstacyagency/agentopia
 *
 * Prompt-level complexity scorer. Runs on raw user message only — not full context.
 * Outputs light | standard | heavy in under 1ms with zero external calls.
 *
 * Gates model selection before dispatch. Result consumed by model-router.ts.
 */

export type ComplexityScore = "light" | "standard" | "heavy";

export interface ScorerResult {
  score: ComplexityScore;
  /** Confidence 0.0–1.0. Low confidence = borderline case, model-router may bump up. */
  confidence: number;
  /** Debug: which signals fired. Stripped in production builds. */
  signals?: string[];
}

// ---------------------------------------------------------------------------
// Signal tables
// ---------------------------------------------------------------------------

/** Messages matching these patterns are almost always light. */
const LIGHT_PATTERNS: RegExp[] = [
  /^(hi|hey|hello|sup|yo|gm|good morning|good afternoon|good evening)\b/i,
  /^(thanks|thank you|thx|ty|cheers|ok|okay|got it|sounds good|perfect|great)\b/i,
  /^(yes|no|yep|nope|sure|nah|absolutely|correct|exactly)\b/i,
  /\b(what('?s| is) (the )?(status|progress|update))\b/i,
  /\b(are you (there|ready|done|finished|still))\b/i,
  /\b(how (long|much time))\b/i,
  /\bping\b/i,
];

/** Keyword lists scored additively. Each hit increments a weight bucket. */
const HEAVY_KEYWORDS: string[] = [
  "strategy",
  "strategic",
  "analyze",
  "analyse",
  "analysis",
  "synthesize",
  "synthesise",
  "synthesis",
  "cross-domain",
  "compare",
  "comparison",
  "comprehensive",
  "in-depth",
  "deep dive",
  "architecture",
  "recommend",
  "recommendation",
  "plan",
  "roadmap",
  "evaluate",
  "evaluation",
  "pros and cons",
  "trade-off",
  "tradeoff",
  "forecast",
  "projection",
  "model",
  "framework",
  "end-to-end",
  "holistic",
  "audit",
  "review everything",
  "full review",
];

const STANDARD_KEYWORDS: string[] = [
  "write",
  "draft",
  "generate",
  "create",
  "build",
  "list",
  "summarize",
  "summarise",
  "summary",
  "explain",
  "describe",
  "format",
  "convert",
  "translate",
  "find",
  "search",
  "look up",
  "extract",
  "parse",
  "update",
  "edit",
  "fix",
  "improve",
  "rewrite",
  "outline",
  "steps",
  "how to",
  "instructions",
  "script",
  "email",
  "report",
  "table",
  "schedule",
];

// ---------------------------------------------------------------------------
// Heuristics
// ---------------------------------------------------------------------------

/** Sentence count threshold — more sentences → more complex intent. */
const SENTENCE_COUNT_STANDARD = 2;
const SENTENCE_COUNT_HEAVY = 5;

/** Word count thresholds. */
const WORD_COUNT_LIGHT_MAX = 8;
const WORD_COUNT_STANDARD_MAX = 40;

/** Question count — multiple questions in one message → heavy. */
const MULTI_QUESTION_THRESHOLD = 2;

/** Structured markers: bullet lists, numbered steps, code fences. */
const STRUCTURED_CONTENT_RE = /(\n[-*•]\s|\n\d+\.\s|```)/;

/** Enumeration — "and ... and ... and" or comma-separated tasks. */
const ENUMERATION_RE = /\b(and|also|additionally|furthermore|moreover|plus)\b/gi;

// ---------------------------------------------------------------------------
// Scorer
// ---------------------------------------------------------------------------

export function scoreComplexity(
  message: string,
  debug = false
): ScorerResult {
  const signals: string[] = [];
  const raw = message.trim();

  if (!raw) {
    return { score: "light", confidence: 1.0, signals: debug ? ["empty_message"] : undefined };
  }

  const lower = raw.toLowerCase();

  // --- Fast-path: light pattern match ---
  for (const re of LIGHT_PATTERNS) {
    if (re.test(raw)) {
      signals.push("light_pattern_match");
      return {
        score: "light",
        confidence: 0.95,
        signals: debug ? signals : undefined,
      };
    }
  }

  // --- Word count fast-path ---
  const words = raw.split(/\s+/).filter(Boolean);
  const wordCount = words.length;

  if (wordCount <= WORD_COUNT_LIGHT_MAX) {
    // Short message but no light pattern — likely a quick command
    signals.push(`word_count_low(${wordCount})`);
    return {
      score: "light",
      confidence: 0.80,
      signals: debug ? signals : undefined,
    };
  }

  // --- Weighted scoring pass ---
  let heavyWeight = 0;
  let standardWeight = 0;

  // Keyword scoring
  for (const kw of HEAVY_KEYWORDS) {
    if (lower.includes(kw)) {
      heavyWeight += 2;
      if (debug) signals.push(`heavy_kw(${kw})`);
    }
  }
  for (const kw of STANDARD_KEYWORDS) {
    if (lower.includes(kw)) {
      standardWeight += 1;
      if (debug) signals.push(`std_kw(${kw})`);
    }
  }

  // Word count heuristic
  if (wordCount > WORD_COUNT_STANDARD_MAX) {
    standardWeight += 2;
    signals.push(`word_count_high(${wordCount})`);
  }

  // Sentence count
  const sentences = raw.split(/[.!?]+/).filter((s) => s.trim().length > 3);
  const sentenceCount = sentences.length;
  if (sentenceCount >= SENTENCE_COUNT_HEAVY) {
    heavyWeight += 2;
    signals.push(`sentence_count_heavy(${sentenceCount})`);
  } else if (sentenceCount >= SENTENCE_COUNT_STANDARD) {
    standardWeight += 1;
    signals.push(`sentence_count_std(${sentenceCount})`);
  }

  // Multiple questions
  const questionCount = (raw.match(/\?/g) || []).length;
  if (questionCount >= MULTI_QUESTION_THRESHOLD) {
    heavyWeight += questionCount >= 3 ? 3 : 2;
    signals.push(`multi_question(${questionCount})`);
  }

  // Structured content (bullets, numbered list, code fences)
  if (STRUCTURED_CONTENT_RE.test(raw)) {
    standardWeight += 2;
    signals.push("structured_content");
  }

  // Enumeration density
  const enumerationMatches = (lower.match(ENUMERATION_RE) || []).length;
  if (enumerationMatches >= 3) {
    heavyWeight += 2;
    signals.push(`enumeration_density(${enumerationMatches})`);
  } else if (enumerationMatches >= 1) {
    standardWeight += 1;
    signals.push(`enumeration(${enumerationMatches})`);
  }

  // --- Resolve score ---
  let score: ComplexityScore;
  let confidence: number;

  if (heavyWeight >= 4) {
    score = "heavy";
    confidence = Math.min(0.95, 0.70 + heavyWeight * 0.03);
  } else if (heavyWeight >= 2 || standardWeight >= 3) {
    score = "standard";
    confidence = Math.min(0.90, 0.65 + (heavyWeight + standardWeight) * 0.02);
  } else if (standardWeight >= 1) {
    score = "standard";
    confidence = 0.70;
  } else {
    score = "light";
    confidence = 0.75;
  }

  return {
    score,
    confidence,
    signals: debug ? signals : undefined,
  };
}
