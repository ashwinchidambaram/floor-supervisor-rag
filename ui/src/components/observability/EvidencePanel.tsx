// ---------------------------------------------------------------------------
// EvidencePanel — per-sub-question grounding evidence (drill-down body part b).
//   Role:     For one sub-question show: routed source, judge verdict + failure mode
//             (PASS=sage / FAIL=danger), retrieval attempts, and every retrieved chunk
//             with a terracotta score bar carrying the high/min floor threshold ticks +
//             a sage check on judge-supported chunks. TABLE chunks render verbatim.
//   Contract: { sq, config }. Reuses parseMarkdownTable + sourceLabel.
//   Failure:  non-table markdown falls back to raw text; missing verdict reads neutral.
// ---------------------------------------------------------------------------

import type { RetrievedChunk, RunConfig, SubQuestion } from "@/lib/types";
import { parseMarkdownTable } from "@/components/qna/markdownTable";
import { sourceLabel } from "@/components/qna/sourceLabel";
import { Check } from "lucide-react";
import { Pill } from "./primitives";

export function EvidencePanel({ sq, config }: { sq: SubQuestion; config: RunConfig }) {
  const verdict = sq.judge_verdict;
  const supported = new Set(sq.supporting_chunk_ids);

  return (
    <div className="rounded-lg border border-subtle bg-surface-alt/60 p-4">
      {/* Sub-question header: text + the judge's verdict row. */}
      <p className="text-meta leading-snug text-ink">{sq.text}</p>

      <div className="mt-2.5 flex flex-wrap items-center gap-2">
        <Pill tone="neutral">{sourceLabel(sq.routed_source)}</Pill>
        {verdict === "PASS" && <Pill tone="sage">judge pass</Pill>}
        {verdict === "FAIL" && (
          <Pill tone="danger">
            judge fail{sq.judge_failure_mode ? ` · ${sq.judge_failure_mode}` : ""}
          </Pill>
        )}
        {verdict == null && <Pill tone="neutral">unjudged</Pill>}
        <span className="font-mono text-micro tabular-nums text-ink-faint">
          {sq.retrieval_attempts} retrieval{sq.retrieval_attempts === 1 ? "" : "s"}
        </span>
        {sq.confidence && (
          <span className="font-mono text-micro tabular-nums text-ink-faint">
            · {sq.confidence.toLowerCase()} confidence
          </span>
        )}
      </div>

      {/* Retrieved chunks, each with a score bar + threshold ticks. */}
      <ul className="mt-4 space-y-3">
        {sq.retrieved.map((chunk) => (
          <ChunkRow
            key={chunk.chunk_id}
            chunk={chunk}
            config={config}
            isSupporting={supported.has(chunk.chunk_id)}
          />
        ))}
        {sq.retrieved.length === 0 && (
          <li className="font-mono text-micro text-ink-faint">no chunks retrieved</li>
        )}
      </ul>
    </div>
  );
}

function ChunkRow({
  chunk,
  config,
  isSupporting,
}: {
  chunk: RetrievedChunk;
  config: RunConfig;
  isSupporting: boolean;
}) {
  const table = chunk.element_type === "TABLE" ? parseMarkdownTable(chunk.table_markdown) : null;
  return (
    <li className="rounded-md border border-subtle bg-surface px-3 py-2.5">
      <div className="flex items-center gap-2">
        {isSupporting && (
          <span
            className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-[rgba(139,157,131,0.18)]"
            aria-label="judge-supported chunk"
            title="Judge approved this chunk for citation"
          >
            <Check className="h-2.5 w-2.5 text-[#5D6A53]" strokeWidth={3} />
          </span>
        )}
        <span className="min-w-0 flex-1 truncate font-mono text-micro text-ink-muted">
          {chunk.section}
        </span>
        {chunk.element_type === "TABLE" && (
          <span className="shrink-0 font-mono text-micro uppercase tracking-[0.08em] text-ink-faint">
            table
          </span>
        )}
        <span className="shrink-0 font-mono text-micro tabular-nums text-ink">
          {chunk.score.toFixed(3)}
        </span>
      </div>

      <ScoreBar
        score={chunk.score}
        highFloor={config.high_score_floor}
        minFloor={config.min_score_floor}
      />

      {/* TABLE chunks render verbatim; prose shows a trimmed snippet. */}
      {table ? (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full border-collapse font-mono text-micro">
            <thead>
              <tr className="border-b border-border text-left text-ink-faint">
                {table.headers.map((h, i) => (
                  <th key={i} className="px-2 py-1 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, ri) => (
                <tr key={ri} className="border-b border-subtle last:border-b-0">
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-2 py-1 tabular-nums text-ink-muted">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        chunk.text && (
          <p className="mt-1.5 line-clamp-2 text-micro leading-snug text-ink-faint">
            {chunk.text}
          </p>
        )
      )}
    </li>
  );
}

/**
 * Score bar: terracotta fill (chart use, not status), with the run's high/min floors
 * drawn as vertical threshold ticks so the operator sees where this score sits relative
 * to the deterministic confidence gates. Scores assumed in [0,1].
 */
function ScoreBar({
  score,
  highFloor,
  minFloor,
}: {
  score: number;
  highFloor: number;
  minFloor: number;
}) {
  const clamp = (v: number) => Math.max(0, Math.min(1, v)) * 100;
  return (
    <div className="relative mt-1.5 h-2 w-full rounded-full bg-surface-alt">
      <div
        className="absolute inset-y-0 left-0 rounded-full bg-accent"
        style={{ width: `${clamp(score)}%` }}
      />
      <Tick at={clamp(minFloor)} label={`min floor ${minFloor}`} />
      <Tick at={clamp(highFloor)} label={`high floor ${highFloor}`} />
    </div>
  );
}

function Tick({ at, label }: { at: number; label: string }) {
  return (
    <span
      className="absolute inset-y-[-2px] w-px bg-ink/45"
      style={{ left: `${at}%` }}
      role="img"
      aria-label={label}
      title={label}
    />
  );
}
