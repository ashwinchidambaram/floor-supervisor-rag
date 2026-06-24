// ---------------------------------------------------------------------------
// TurnView — one Q→A exchange in the transcript.
//
// Role:     The supervisor's question as a warm right-aligned bubble (surface-alt,
//           ink — never terracotta), then ONE answer card: a confidence badge,
//           the verbatim answer body (prose + tables + ⚠︎ notices), citation chips,
//           a per-part breakdown for multi-part turns, and — when "Show pipeline"
//           is on — the quiet agentic spine. An ABSTAINED turn renders a calm
//           "no grounded answer" notice with no citations (never an error alarm).
// Contract: <TurnView turn={Turn} showPipeline={boolean} />.
// Failure:  null answer_text / empty citations are handled by the children.
// ---------------------------------------------------------------------------

import { Ban } from "lucide-react";
import type { Turn } from "@/lib/types";
import { abstainTone, confidenceColor } from "@/lib/tokens";
import { sourceLabel } from "@/components/qna/sourceLabel";
import { ConfidenceBadge, ConfidenceDot } from "@/components/qna/confidenceBadge";
import { AnswerBody } from "@/components/qna/answerBody";
import { CitationChip } from "@/components/qna/citationChip";
import { PipelineReveal } from "@/components/qna/pipelineReveal";

export function TurnView({ turn, showPipeline }: { turn: Turn; showPipeline: boolean }) {
  const abstained = turn.status === "ABSTAINED";

  return (
    <article className="space-y-3 animate-fade-up">
      {/* Supervisor question — warm right-aligned bubble, never the accent color. */}
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-md bg-surface-alt px-4 py-2.5 text-body leading-relaxed text-ink">
          {turn.question_text}
        </p>
      </div>

      {/* Assistant answer — one card. */}
      <div className="rounded-xl border border-border bg-surface px-5 py-4 shadow-card">
        {abstained ? (
          <AbstainNotice />
        ) : (
          <>
            <div className="mb-3.5">
              <ConfidenceBadge tone={confidenceColor(turn.turn_confidence)} />
            </div>

            <AnswerBody text={turn.answer_text} />

            {turn.citations.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2 border-t border-subtle pt-3.5">
                {turn.citations.map((c, i) => (
                  <CitationChip key={`${c.chunk_id}-${i}`} citation={c} />
                ))}
              </div>
            )}

            {turn.sub_questions.length > 1 && <PartsBreakdown turn={turn} />}
          </>
        )}

        {showPipeline && <PipelineReveal turn={turn} />}
      </div>
    </article>
  );
}

/** ABSTAINED → a calm danger notice. No citations, no alarm, never terracotta. */
function AbstainNotice() {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-[rgba(216,86,80,0.40)] bg-danger-soft px-4 py-3.5">
      <Ban className="mt-0.5 h-4 w-4 shrink-0 text-danger" strokeWidth={2} aria-hidden />
      <div>
        <p className="font-mono text-micro font-semibold uppercase tracking-[0.08em] text-danger">
          {abstainTone.label}
        </p>
        <p className="mt-1 text-meta leading-relaxed text-ink-muted">
          The documentation does not cover this. Please consult your subject-matter expert
          directly rather than rely on an unverified answer.
        </p>
      </div>
    </div>
  );
}

/** Multi-part turns: each sub_question with its confidence dot, text (wrapped), and routed source. */
function PartsBreakdown({ turn }: { turn: Turn }) {
  return (
    <div className="mt-4 border-t border-subtle pt-3.5">
      <p className="mb-2.5 font-mono text-micro font-semibold uppercase tracking-[0.1em] text-ink-faint">
        {turn.sub_questions.length} parts · confidence = lowest part
      </p>
      <ul className="space-y-2.5">
        {turn.sub_questions.map((sq) => {
          const tone = confidenceColor(sq.confidence);
          return (
            <li key={sq.id} className="flex items-start gap-2.5">
              <ConfidenceDot tone={tone} className="mt-1.5" />
              <span className="min-w-0 flex-1 text-meta leading-relaxed text-ink-muted">
                {sq.text}
              </span>
              <span className="shrink-0 pt-0.5 font-mono text-micro text-ink-faint">
                {sourceLabel(sq.routed_source)}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
