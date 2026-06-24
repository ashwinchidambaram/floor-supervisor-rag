// ---------------------------------------------------------------------------
// QnaPortal — the Ask surface (the floor supervisor's home).
//
// Role:     A two-column portal: a left conversation rail (recorded history +
//           "New conversation"), and a right transcript with a pinned composer.
//           Selecting a rail item plays back a recorded conversation; "New"
//           starts a live session that calls ask(question, threadId) — mock today,
//           the real backend when VITE_API_URL is set. Honest, grounded, calm.
// Contract: reads getConversations/getTurns/getConversation via the data seam;
//           writes ?c=<id> (useHashParam) + selectConversation(id). ask() is the
//           only model touch and it goes through the seam. Live mode shows a login
//           gate first and clears the key on a 401.
// Failure:  ask() errors render an inline notice; a 401 re-shows the gate. Empty
//           selection / ?c=new → the calm new-conversation state with sample chips.
// ---------------------------------------------------------------------------

import { useEffect, useMemo, useRef, useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import {
  ask,
  getConversation,
  getSelectedId,
  getTurns,
  isLive,
  selectConversation,
} from "@/lib/dataSource";
import { useHashParam } from "@/lib/router";
import type { Turn } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ConversationRail } from "@/components/qna/conversationRail";
import { Composer } from "@/components/qna/composer";
import { LoginGate } from "@/components/qna/loginGate";
import { NewConversationState } from "@/components/qna/emptyState";
import { TurnView } from "@/components/qna/turnView";

const PIPELINE_KEY = "qna_show_pipeline";
const ACCESS_KEY = "demo_access_key";
const THREAD_KEY = "qna_thread_id";

/** A per-session thread id; a fresh one means a fresh "New conversation". */
function freshThreadId(): string {
  const id = crypto.randomUUID();
  sessionStorage.setItem(THREAD_KEY, id);
  return id;
}
function currentThreadId(): string {
  return sessionStorage.getItem(THREAD_KEY) ?? freshThreadId();
}

export function QnaPortal() {
  const live = isLive();

  // Live-mode access gate.
  const [authed, setAuthed] = useState<boolean>(() => !live || !!sessionStorage.getItem(ACCESS_KEY));
  const [authError, setAuthError] = useState<string | null>(null);

  // ?c=<id> selects a recorded conversation; ?c=new (or null) → live session.
  const [convParam, setConvParam] = useHashParam("c");
  const isNewSession = convParam === "new" || convParam === null;

  // Pipeline toggle persists across sessions (operator preference).
  const [showPipeline, setShowPipeline] = useState<boolean>(
    () => localStorage.getItem(PIPELINE_KEY) === "1"
  );
  useEffect(() => {
    localStorage.setItem(PIPELINE_KEY, showPipeline ? "1" : "0");
  }, [showPipeline]);

  // Live conversation state (the turns produced by ask() this session).
  const [liveTurns, setLiveTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [thinking, setThinking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  // Sync the read seam to the selected recorded conversation.
  useEffect(() => {
    if (convParam && convParam !== "new") selectConversation(convParam);
  }, [convParam]);

  // The transcript: recorded turns for a selected conversation, else the live ones.
  const recordedTurns = useMemo(
    () => (isNewSession ? [] : getTurns(convParam ?? getSelectedId())),
    [isNewSession, convParam]
  );
  const turns = isNewSession ? liveTurns : recordedTurns;

  // Auto-scroll the transcript to the newest turn.
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, thinking]);

  function startNewConversation() {
    freshThreadId();
    setLiveTurns([]);
    setDraft("");
    setAskError(null);
    setConvParam("new");
  }

  function selectRecorded(id: string) {
    selectConversation(id);
    setConvParam(id);
  }

  async function submit() {
    const question = draft.trim();
    if (!question || thinking) return;

    // Asking always happens in a live session — switch into one if needed.
    if (!isNewSession) setConvParam("new");
    setDraft("");
    setThinking(true);
    setAskError(null);

    try {
      const state = await ask(question, currentThreadId());
      const last = state.current_turn ?? state.turns[state.turns.length - 1];
      if (last) {
        setLiveTurns((prev) => [...prev, last]);
      } else {
        // A 200 with no turn — surface it rather than silently dropping the answer.
        setAskError("Something went wrong reaching the assistant. Please try again.");
        setDraft(question);
      }
    } catch (err) {
      if (err instanceof Error && err.message === "unauthorized") {
        sessionStorage.removeItem(ACCESS_KEY);
        setAuthed(false);
        setAuthError("That access key was rejected. Please try again.");
      } else {
        setAskError("Something went wrong reaching the assistant. Please try again.");
        setDraft(question); // give the supervisor their text back
      }
    } finally {
      setThinking(false);
    }
  }

  // Live-mode login gate, before the portal.
  if (live && !authed) {
    return (
      <LoginGate
        error={authError}
        onUnlock={(key) => {
          sessionStorage.setItem(ACCESS_KEY, key);
          setAuthError(null);
          setAuthed(true);
        }}
      />
    );
  }

  const showNewState = isNewSession && turns.length === 0 && !thinking;

  return (
    <div className="flex h-full min-h-0">
      <ConversationRail
        activeId={isNewSession ? null : convParam ?? getSelectedId()}
        onNew={startNewConversation}
        onSelect={selectRecorded}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Transcript header: title + the quiet operator pipeline toggle. */}
        <div className="flex items-center justify-between border-b border-border px-6 py-3.5">
          <div className="min-w-0">
            <span className="eyebrow">◦ ASK</span>
            <h1 className="truncate font-display text-lead font-semibold tracking-tight text-ink">
              {isNewSession
                ? "New conversation"
                : getConversation(convParam ?? getSelectedId()).conversation_id}
            </h1>
          </div>
          <PipelineToggle on={showPipeline} onToggle={() => setShowPipeline((v) => !v)} />
        </div>

        {/* Transcript. */}
        <div className="scroll-quiet min-h-0 flex-1 overflow-y-auto px-6 py-7">
          {showNewState ? (
            <NewConversationState onPick={(q) => setDraft(q)} />
          ) : (
            <div className="mx-auto w-full max-w-reading space-y-8">
              {turns.map((turn) => (
                <TurnView key={turn.turn_id} turn={turn} showPipeline={showPipeline} />
              ))}
              {askError && (
                <p className="rounded-lg border border-[rgba(216,86,80,0.40)] bg-danger-soft px-4 py-3 text-meta text-danger" role="alert">
                  {askError}
                </p>
              )}
              <div ref={endRef} />
            </div>
          )}
        </div>

        <Composer
          value={draft}
          onChange={setDraft}
          onSubmit={submit}
          thinking={thinking}
        />
      </div>
    </div>
  );
}

/** The persistent "Show pipeline" toggle — a quiet operator affordance. */
function PipelineToggle({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      onClick={onToggle}
      className={cn(
        "inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 font-mono text-micro font-medium uppercase tracking-[0.06em] transition-colors duration-150 ease-out-quart",
        on
          ? "border-accent/45 bg-[rgba(212,116,94,0.08)] text-accent"
          : "border-border text-ink-muted hover:border-border-subtle hover:text-ink"
      )}
    >
      <SlidersHorizontal className="h-3.5 w-3.5" strokeWidth={2} aria-hidden />
      Show pipeline
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          on ? "bg-accent" : "bg-ink-faint/40"
        )}
        aria-hidden
      />
    </button>
  );
}
