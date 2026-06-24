// ---------------------------------------------------------------------------
// AuditTrail — section 5: the append-only attribution log, collapsed by default.
//   Role:     On open, the actor / action / detail list; each row expands to its
//             before -> after delta. This is the compliance-grade "who did what" view,
//             kept quiet so it never competes with the headline.
//   Contract: { entries }. Pure render over AuditEntry[].
//   Failure:  empty entries render a calm placeholder.
// ---------------------------------------------------------------------------

import { useState } from "react";
import type { AuditEntry } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ChevronRight } from "lucide-react";

export function AuditTrail({ entries }: { entries: AuditEntry[] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="overflow-hidden rounded-lg border border-subtle">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-2.5 bg-surface px-4 py-2.5 text-left"
      >
        <ChevronRight
          className={cn(
            "h-4 w-4 text-ink-faint transition-transform duration-150 ease-out-quart",
            open && "rotate-90",
          )}
          strokeWidth={2}
        />
        <span className="font-mono text-micro uppercase tracking-[0.08em] text-ink-muted">
          {entries.length} entries
        </span>
        <span className="ml-auto font-mono text-micro text-ink-faint">
          {open ? "hide" : "show"}
        </span>
      </button>

      {open && (
        <ul className="divide-y divide-subtle border-t border-subtle">
          {entries.map((e, i) => (
            <AuditRow key={i} entry={e} />
          ))}
          {entries.length === 0 && (
            <li className="px-4 py-3 font-mono text-micro text-ink-faint">no audit entries</li>
          )}
        </ul>
      )}
    </div>
  );
}

function AuditRow({ entry }: { entry: AuditEntry }) {
  const [open, setOpen] = useState(false);
  const hasDelta =
    Object.keys(entry.before ?? {}).length > 0 || Object.keys(entry.after ?? {}).length > 0;

  return (
    <li>
      <button
        type="button"
        onClick={() => hasDelta && setOpen((v) => !v)}
        aria-expanded={hasDelta ? open : undefined}
        className={cn(
          "flex w-full items-baseline gap-3 px-4 py-2 text-left",
          hasDelta && "hover:bg-surface-alt",
        )}
      >
        <span className="w-44 shrink-0 truncate font-mono text-micro text-ink-muted">
          {entry.actor}
        </span>
        <span className="w-40 shrink-0 truncate font-mono text-micro uppercase tracking-[0.06em] text-ink-faint">
          {entry.action}
        </span>
        <span className="min-w-0 flex-1 truncate text-meta text-ink-muted">{entry.detail}</span>
      </button>

      {open && hasDelta && (
        <div className="grid gap-3 px-4 pb-3 pl-[12.25rem] sm:grid-cols-2">
          <DeltaBlock label="before" data={entry.before} tone="text-ink-faint" />
          <DeltaBlock label="after" data={entry.after} tone="text-ink" />
        </div>
      )}
    </li>
  );
}

function DeltaBlock({
  label,
  data,
  tone,
}: {
  label: string;
  data: Record<string, unknown>;
  tone: string;
}) {
  const keys = Object.keys(data ?? {});
  return (
    <div className="rounded-md border border-subtle bg-surface-alt/50 p-2.5">
      <div className="mb-1 font-mono text-micro uppercase tracking-[0.08em] text-ink-faint">
        {label}
      </div>
      {keys.length === 0 ? (
        <div className="font-mono text-micro text-ink-faint">∅</div>
      ) : (
        <dl className="space-y-0.5">
          {keys.map((k) => (
            <div key={k} className="flex gap-2 font-mono text-micro">
              <dt className="text-ink-faint">{k}</dt>
              <dd className={cn("tabular-nums", tone)}>{String(data[k])}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
