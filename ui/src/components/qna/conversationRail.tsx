// ---------------------------------------------------------------------------
// ConversationRail — the left navigation column on the Ask surface.
//
// Role:     A terracotta "New conversation" action, then the recorded
//           conversations from getConversations(): each a title + a confidence
//           dot (worst_confidence) + a turn count. Selecting one sets ?c=<id> and
//           tells the read seam to load that conversation.
// Contract: <ConversationRail activeId selectedConvId onNew onSelect />.
// Failure:  empty list → a quiet placeholder line. Pure presentation otherwise.
// ---------------------------------------------------------------------------

import { Plus } from "lucide-react";
import { getConversations } from "@/lib/dataSource";
import { confidenceColor } from "@/lib/tokens";
import { cn } from "@/lib/utils";
import { ConfidenceDot } from "@/components/qna/confidenceBadge";

export function ConversationRail({
  activeId,
  onNew,
  onSelect,
}: {
  activeId: string | null;
  onNew: () => void;
  onSelect: (id: string) => void;
}) {
  const conversations = getConversations();

  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-border bg-surface-alt">
      <div className="px-4 pb-3 pt-5">
        <span className="eyebrow">◦ CONVERSATIONS</span>
        <button
          type="button"
          onClick={onNew}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-3 py-2.5 text-ui font-medium text-[#F4EFE6] shadow-glow-accent transition-colors duration-150 ease-out-quart hover:bg-accent-hover"
        >
          <Plus className="h-4 w-4" strokeWidth={2.25} aria-hidden />
          New conversation
        </button>
      </div>

      <nav className="scroll-quiet min-h-0 flex-1 overflow-y-auto px-2 pb-4" aria-label="Conversations">
        <ul className="space-y-0.5">
          {conversations.map((c) => {
            const active = c.id === activeId;
            const tone = confidenceColor(c.worst_confidence);
            return (
              <li key={c.id}>
                <button
                  type="button"
                  onClick={() => onSelect(c.id)}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "group flex w-full items-start gap-2.5 rounded-lg px-3 py-2.5 text-left transition-colors duration-150 ease-out-quart",
                    active
                      ? "bg-surface shadow-card"
                      : "hover:bg-surface/70"
                  )}
                >
                  <ConfidenceDot tone={tone} className="mt-1.5" />
                  <span className="min-w-0 flex-1">
                    <span
                      className={cn(
                        "line-clamp-2 text-ui leading-snug",
                        active ? "font-semibold text-ink" : "font-medium text-ink"
                      )}
                    >
                      {c.title}
                    </span>
                    <span className="mt-1 block font-mono text-micro text-ink-faint">
                      {c.turn_count} turn{c.turn_count === 1 ? "" : "s"}
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
