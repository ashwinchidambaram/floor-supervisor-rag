// ---------------------------------------------------------------------------
// ConfidenceBadge / ConfidenceDot — the one true confidence pill.
//
// Role:     Render the SAME badge for the SAME state everywhere on the Ask
//           surface. Pulls its colors from confidenceColor()/abstainTone in
//           lib/tokens.ts, so the terracotta accent is never a status color.
// Contract: <ConfidenceBadge tone={StatusTone} /> — a dot + label pill.
//           <ConfidenceDot tone={StatusTone} /> — the bare dot for rails/parts.
// Failure:  pure presentation; tone is always supplied by the caller.
// ---------------------------------------------------------------------------

import type { StatusTone } from "@/lib/tokens";
import { cn } from "@/lib/utils";

/** The bare confidence dot (conversation rail, per-part breakdown). */
export function ConfidenceDot({
  tone,
  className,
}: {
  tone: StatusTone;
  className?: string;
}) {
  return (
    <span
      className={cn("inline-block h-2 w-2 shrink-0 rounded-full", tone.dot, className)}
      aria-hidden
    />
  );
}

/** The full pill: dot + label, tinted by the confidence tone. */
export function ConfidenceBadge({ tone }: { tone: StatusTone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-micro font-medium uppercase tracking-[0.08em]",
        tone.bg,
        tone.border,
        tone.text
      )}
    >
      <ConfidenceDot tone={tone} className="h-1.5 w-1.5" />
      {tone.label}
    </span>
  );
}
