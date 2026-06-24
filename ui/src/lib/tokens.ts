// ---------------------------------------------------------------------------
// tokens.ts — the confidence/status palette (separate from the terracotta accent).
//   Role:     one typed source for confidence presentation, so every surface renders
//             the SAME badge for the SAME state.
//   THE HARD RULE: HIGH=sage, MEDIUM=gold, LOW/abstain=danger (#D85650). The terracotta
//             accent (#D4745E) is interactive/brand ONLY and is NEVER a status color.
// ---------------------------------------------------------------------------

import type { ConfidenceLevel } from "./types";

export interface StatusTone {
  label: string;
  text: string;   // AA-safe text color on the tint
  bg: string;
  border: string;
  dot: string;
}

const HIGH: StatusTone = {
  label: "High confidence",
  text: "text-[#5D6A53]",
  bg: "bg-[rgba(139,157,131,0.14)]",
  border: "border-[rgba(139,157,131,0.40)]",
  dot: "bg-sage",
};
const MEDIUM: StatusTone = {
  label: "Medium confidence",
  text: "text-[#835C39]",
  bg: "bg-[rgba(212,165,116,0.16)]",
  border: "border-[rgba(212,165,116,0.42)]",
  dot: "bg-gold",
};
const LOW: StatusTone = {
  label: "Low confidence",
  text: "text-danger",
  bg: "bg-danger-soft",
  border: "border-[rgba(216,86,80,0.40)]",
  dot: "bg-danger",
};

/** Map a confidence level to its tone. `null` (no answer / abstained) → the muted-danger read. */
export function confidenceColor(level: ConfidenceLevel | null): StatusTone {
  switch (level) {
    case "HIGH": return HIGH;
    case "MEDIUM": return MEDIUM;
    case "LOW":
    case null:
    default: return LOW;
  }
}

/** Abstain/error tone (same danger family as LOW). */
export const abstainTone: StatusTone = { ...LOW, label: "No grounded answer" };

/** Brand role names (resolve to Tailwind tokens). */
export const brandTokens = {
  structural: "ink",
  brandPop: "accent",
  canvas: "canvas",
  surface: "surface",
  border: "border",
  ink: "ink",
} as const;
