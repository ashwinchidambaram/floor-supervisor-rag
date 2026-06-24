// ---------------------------------------------------------------------------
// observability.ts — pure derivations for the Observability console.
//
// Role:     Turn the flat data-out feed (ordered Events + Turns) into the shapes the
//           console renders: one event group per turn, per-turn rollups (cost / latency
//           / error / gap-count), and the aggregate false-PASS watch. No I/O, no React.
// Contract: groupEventsByTurn(events, turns) -> { groups, falsePassCount }. Each group is
//           1:1 with a turn in order, split at every `ingest_question` event. Divide-by-zero
//           guarded; a feed with no ingest events yields no groups (callers render empty).
// Failure:  total over the union — never throws; missing fields fall back to 0 / false.
// ---------------------------------------------------------------------------

import type { Event, Turn } from "./types";

/** The boundary marker: each turn's event run begins at its `ingest_question` node. */
const TURN_BOUNDARY = "ingest_question";

/** One turn's slice of the ordered event feed, paired with its Turn and a rollup. */
export interface TurnEventGroup {
  turn: Turn;
  events: Event[];
  cost: number;       // Σ cost_usd over the group
  latencyMs: number;  // Σ latency_ms over the group (wall-ish; nodes run in sequence here)
  hasError: boolean;  // any event in the group carries an error
  gapCount: number;   // sub-questions in this turn that the judge could not ground
}

export interface GroupedRun {
  groups: TurnEventGroup[];
  /** Aggregate watch: a sub_question the judge PASSed inside a turn that resolved LOW. */
  falsePassCount: number;
}

/**
 * Count sub-questions whose judge said PASS while the turn as a whole resolved LOW.
 * A non-zero count means the judge's per-part verdict disagreed with the turn outcome —
 * the signal the operator most wants surfaced (a "clean PASS" that didn't hold up).
 */
function countFalsePass(turn: Turn): number {
  if (turn.turn_confidence !== "LOW") return 0;
  return turn.sub_questions.reduce(
    (n, sq) => (sq.judge_verdict === "PASS" ? n + 1 : n),
    0,
  );
}

/** A turn's documentation-gap count = sub-questions the judge FAILed (could not ground). */
function gapCountFor(turn: Turn): number {
  return turn.sub_questions.reduce(
    (n, sq) => (sq.judge_verdict === "FAIL" ? n + 1 : n),
    0,
  );
}

/**
 * Split the ordered event feed into one group per turn, starting a new group at each
 * `ingest_question`. Groups are zipped to `turns` by position (the feed is 1:1 with turns
 * in order). Any events before the first boundary are dropped (there are none in practice).
 */
export function groupEventsByTurn(events: Event[], turns: Turn[]): GroupedRun {
  const slices: Event[][] = [];
  for (const ev of events) {
    if (ev.node === TURN_BOUNDARY) slices.push([ev]);
    else if (slices.length > 0) slices[slices.length - 1].push(ev);
  }

  const count = Math.min(slices.length, turns.length);
  const groups: TurnEventGroup[] = [];
  for (let i = 0; i < count; i += 1) {
    const evs = slices[i];
    const turn = turns[i];
    groups.push({
      turn,
      events: evs,
      cost: evs.reduce((s, e) => s + (e.cost_usd ?? 0), 0),
      latencyMs: evs.reduce((s, e) => s + (e.latency_ms ?? 0), 0),
      hasError: evs.some((e) => e.error != null && e.error !== ""),
      gapCount: gapCountFor(turn),
    });
  }

  // If the feed has fewer ingest markers than turns, still surface every turn (events empty).
  for (let i = count; i < turns.length; i += 1) {
    const turn = turns[i];
    groups.push({
      turn,
      events: [],
      cost: 0,
      latencyMs: 0,
      hasError: turn.status === "FAILED",
      gapCount: gapCountFor(turn),
    });
  }

  const falsePassCount = turns.reduce((n, t) => n + countFalsePass(t), 0);
  return { groups, falsePassCount };
}

/** Safe percentage helper — guards divide-by-zero, clamps to [0,100]. */
export function pct(part: number, whole: number): number {
  if (!whole) return 0;
  return Math.max(0, Math.min(100, (part / whole) * 100));
}
