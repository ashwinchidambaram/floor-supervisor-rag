// ---------------------------------------------------------------------------
// primitives — small shared atoms for the Observability console.
//   Role:     Band (eyebrow-led section), Eyebrow, StatusDot, Pill, and number
//             formatters. Keeps every band visually consistent so the operator
//             scans by the same rhythm everywhere.
//   Contract: pure presentational. No data access.
//   Failure:  none — total over inputs.
// ---------------------------------------------------------------------------

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/** A page band: an `◦ EYEBROW` over generous whitespace, optional trailing slot. */
export function Band({
  eyebrow,
  title,
  trailing,
  children,
}: {
  eyebrow: string;
  title?: string;
  trailing?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="border-t border-subtle pt-8">
      <div className="flex items-end justify-between gap-4">
        <div>
          <span className="eyebrow">◦ {eyebrow}</span>
          {title && (
            <h2 className="mt-1.5 font-display text-lead font-semibold tracking-tight text-ink">
              {title}
            </h2>
          )}
        </div>
        {trailing && <div className="shrink-0">{trailing}</div>}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export type Tone = "sage" | "gold" | "danger" | "neutral";

const DOT: Record<Tone, string> = {
  sage: "bg-sage",
  gold: "bg-gold",
  danger: "bg-danger",
  neutral: "bg-ink-faint",
};

/** Status dot that also carries SHAPE, not color alone: ring for caution, square for bad. */
export function StatusDot({ tone, label }: { tone: Tone; label: string }) {
  return (
    <span
      role="img"
      aria-label={label}
      className={cn(
        "inline-block h-2.5 w-2.5 shrink-0",
        tone === "danger" ? "rounded-[2px]" : "rounded-full",
        tone === "gold" && "ring-2 ring-gold/40 ring-offset-1 ring-offset-surface",
        DOT[tone],
      )}
    />
  );
}

/** A compact pill. `tone` drives the tint; numbers/labels stay mono + tabular. */
export function Pill({
  tone,
  children,
  className,
}: {
  tone: Tone;
  children: ReactNode;
  className?: string;
}) {
  const tones: Record<Tone, string> = {
    sage: "text-[#5D6A53] bg-[rgba(139,157,131,0.14)] border-[rgba(139,157,131,0.40)]",
    gold: "text-[#835C39] bg-[rgba(212,165,116,0.16)] border-[rgba(212,165,116,0.42)]",
    danger: "text-danger bg-danger-soft border-[rgba(216,86,80,0.40)]",
    neutral: "text-ink-muted bg-surface-alt border-border",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 font-mono text-micro font-medium tabular-nums uppercase tracking-[0.06em]",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

/** Money formatter — deterministic nodes render the literal "$0", spend gets 4dp. */
export function money(v: number): string {
  return v === 0 ? "$0" : `$${v.toFixed(4)}`;
}

/** Latency formatter — ms under 1s, seconds above, always tabular-friendly. */
export function ms(v: number): string {
  if (v >= 1000) return `${(v / 1000).toFixed(2)}s`;
  return `${v.toFixed(0)}ms`;
}
