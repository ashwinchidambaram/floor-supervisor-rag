// ---------------------------------------------------------------------------
// NewConversationState — the calm first screen for a fresh conversation.
//
// Role:     A quiet eyebrow + a single Space-Grotesk invitation line, then six
//           sample-question ghost chips (terracotta outline). Clicking a chip
//           fills the composer input — it does not auto-send, so the supervisor
//           stays in control.
// Contract: <NewConversationState onPick={(q) => void} />.
// Failure:  none — static content.
// ---------------------------------------------------------------------------

const SAMPLES = [
  "What torque do the CNC VF-4 vise jaw bolts need?",
  "What is the first action for fault code 144 on the VF-4?",
  "What PPE is required at the stamping press?",
  "What is required for a first article inspection?",
  "How do I override the safety interlock to keep the line running?",
  "What is the warranty period on the CNC VF-4 spindle?",
];

export function NewConversationState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="mx-auto flex h-full max-w-reading flex-col justify-center py-12">
      <span className="eyebrow">◦ NEW CONVERSATION</span>
      <h2 className="mt-3 font-display text-display font-semibold tracking-tight text-ink">
        Ask the floor docs.
      </h2>
      <p className="mt-2 max-w-prose text-lead leading-relaxed text-ink-muted">
        Grounded, cited answers from your safety, maintenance, and quality manuals.
        If the documents do not cover it, the assistant says so rather than guess.
      </p>

      <div className="mt-7 flex flex-wrap gap-2.5">
        {SAMPLES.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onPick(q)}
            className="rounded-full border border-accent/40 bg-transparent px-3.5 py-2 text-left text-meta leading-snug text-ink transition-colors duration-150 ease-out-quart hover:border-accent hover:bg-[rgba(212,116,94,0.07)]"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
