// ---------------------------------------------------------------------------
// Observability — Page B (monitor + explain the system), the TECHNICAL OPERATOR view.
//
// Role:     Deterministic playback of the recorded run, read top-to-bottom: an executive
//           summary ribbon (healthy? cost? where thin?), cost & latency, the per-turn
//           THREADS list with full drill-down (node trace · grounding evidence · the
//           answer/abstain), the knowledge-gaps table, and a collapsed audit trail.
// Contract: reads getTurns / getEvents / getMetrics / getKnowledgeGaps / getAuditLog /
//           getState. No model is ever called here — it replays the data-out feed.
//           Deep-links the open thread via ?thread=<turn_id> (useHashParam).
// Failure:  pure render over the typed contract; no turns → a calm empty band.
// ---------------------------------------------------------------------------

import { useMemo } from "react";
import {
  getEvents,
  getMetrics,
  getKnowledgeGaps,
  getAuditLog,
  getTurns,
  getState,
} from "@/lib/dataSource";
import { useHashParam } from "@/lib/router";
import { groupEventsByTurn } from "@/lib/observability";
import { ExecutiveSummary } from "@/components/observability/ExecutiveSummary";
import { CostLatency } from "@/components/observability/CostLatency";
import { ThreadRow } from "@/components/observability/ThreadRow";
import { KnowledgeGaps } from "@/components/observability/KnowledgeGaps";
import { AuditTrail } from "@/components/observability/AuditTrail";
import { Band } from "@/components/observability/primitives";

export function Observability() {
  const events = getEvents();
  const metrics = getMetrics();
  const gaps = getKnowledgeGaps();
  const audit = getAuditLog();
  const turns = getTurns();
  const config = getState().config;

  const [openThread, setOpenThread] = useHashParam("thread");

  const { groups, falsePassCount } = useMemo(
    () => groupEventsByTurn(events, turns),
    [events, turns],
  );

  const { topCostNode, topCostValue } = useMemo(() => {
    const entries = Object.entries(metrics.cost_by_agent);
    if (!entries.length) return { topCostNode: "—", topCostValue: 0 };
    const [node, value] = entries.reduce((a, b) => (b[1] > a[1] ? b : a));
    return { topCostNode: node, topCostValue: value };
  }, [metrics]);

  // Accordion: clicking a row toggles ?thread=<turn_id>; one open at a time.
  const toggle = (turnId: string) =>
    setOpenThread(openThread === turnId ? null : turnId);

  return (
    <div className="scroll-quiet h-full overflow-y-auto">
      <div className="mx-auto max-w-wide space-y-10 px-8 py-9">
        {/* 1 — EXECUTIVE SUMMARY (scanned first) */}
        <ExecutiveSummary
          metrics={metrics}
          falsePassCount={falsePassCount}
          topCostNode={topCostNode}
          topCostValue={topCostValue}
        />

        {/* 2 — Cost & latency */}
        <Band eyebrow="COST & LATENCY" title="Where the run spent">
          <CostLatency metrics={metrics} />
        </Band>

        {/* 3 — THREADS */}
        <Band
          eyebrow="THREADS"
          title="Per-turn trace"
          trailing={
            <span className="font-mono text-micro tabular-nums text-ink-faint">
              {groups.length} turn{groups.length === 1 ? "" : "s"}
            </span>
          }
        >
          {groups.length === 0 ? (
            <p className="font-mono text-meta uppercase tracking-[0.08em] text-ink-faint">
              ◦ NO RECORDED CONVERSATION
            </p>
          ) : (
            <div className="space-y-2">
              {groups.map((g) => (
                <ThreadRow
                  key={g.turn.turn_id}
                  group={g}
                  config={config}
                  open={openThread === g.turn.turn_id}
                  onToggle={() => toggle(g.turn.turn_id)}
                />
              ))}
            </div>
          )}
        </Band>

        {/* 4 — Knowledge gaps */}
        <Band eyebrow="DOCUMENTATION GAPS" title="Where the docs are thin">
          <KnowledgeGaps gaps={gaps} onView={setOpenThread} />
        </Band>

        {/* 5 — Audit trail (collapsed) */}
        <Band eyebrow="AUDIT TRAIL" title="Who did what">
          <AuditTrail entries={audit} />
        </Band>
      </div>
    </div>
  );
}
