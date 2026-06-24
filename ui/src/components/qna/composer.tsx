// ---------------------------------------------------------------------------
// Composer — the pinned ask box at the bottom of the transcript.
//
// Role:     A real text input + send button. Enter submits (Shift+Enter newline).
//           While the ask() promise is in flight it shows a quiet "thinking…"
//           state and disables submit. The parent owns the ask() call + transcript.
// Contract: <Composer value onChange onSubmit thinking disabled />.
// Failure:  empty/whitespace input never submits; thinking blocks re-entry.
// ---------------------------------------------------------------------------

import { useEffect, useRef } from "react";
import { ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";

export function Composer({
  value,
  onChange,
  onSubmit,
  thinking,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  thinking: boolean;
  disabled?: boolean;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-grow the textarea up to a calm ceiling.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const canSend = value.trim().length > 0 && !thinking && !disabled;

  const submit = () => {
    if (canSend) onSubmit();
  };

  return (
    <div className="border-t border-border bg-canvas/80 px-6 py-4 backdrop-blur-sm">
      <div className="mx-auto w-full max-w-reading">
        {thinking && (
          <div className="mb-2 flex items-center gap-2 px-1 font-mono text-micro text-ink-muted" aria-live="polite">
            <span className="flex gap-1" aria-hidden>
              <span className="h-1.5 w-1.5 rounded-full bg-accent animate-dot-pulse" style={{ animationDelay: "0ms" }} />
              <span className="h-1.5 w-1.5 rounded-full bg-accent animate-dot-pulse" style={{ animationDelay: "160ms" }} />
              <span className="h-1.5 w-1.5 rounded-full bg-accent animate-dot-pulse" style={{ animationDelay: "320ms" }} />
            </span>
            thinking…
          </div>
        )}

        <div
          className={cn(
            "flex items-end gap-2 rounded-xl border bg-surface px-3.5 py-2.5 shadow-composer transition-colors duration-150",
            "border-border focus-within:border-accent/50"
          )}
        >
          <textarea
            ref={ref}
            rows={1}
            value={value}
            disabled={disabled}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Ask the floor docs…"
            aria-label="Ask a question"
            className="scroll-quiet max-h-40 flex-1 resize-none bg-transparent py-1.5 text-body leading-relaxed text-ink outline-none placeholder:text-ink-faint disabled:opacity-50"
          />
          <button
            type="button"
            onClick={submit}
            disabled={!canSend}
            aria-label="Send question"
            className={cn(
              "grid h-9 w-9 shrink-0 place-items-center rounded-lg transition-all duration-150 ease-out-quart",
              canSend
                ? "bg-accent text-[#F4EFE6] shadow-glow-accent hover:bg-accent-hover"
                : "bg-surface-alt text-ink-faint"
            )}
          >
            <ArrowUp className="h-4 w-4" strokeWidth={2.5} aria-hidden />
          </button>
        </div>
      </div>
    </div>
  );
}
