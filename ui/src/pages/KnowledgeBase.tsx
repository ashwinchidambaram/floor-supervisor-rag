// ---------------------------------------------------------------------------
// KnowledgeBase — Page C (what the system knows · where it's thin · what's cached).
//
// Role:     The documentation-team / operator surface over the corpus index. The
//           corpus is the spine: Band A glances the documents, Band B browses the
//           Document→Section→Chunk tree into a shared ChunkInspector, Band C replays
//           seeded retrieval with score meters, Band D shows the live embedding cache
//           and the (honest, not-yet-live) response cache, Band E surfaces coverage
//           gaps from the recorded conversations.
// Contract: reads getCorpus / getRetrievalDemo / getCacheStats / getKnowledgeGaps.
//           No model is called here — it renders the data-out KB index.
// Failure:  Pure render over the typed contract. Malformed table markdown falls back
//           to raw text in ChunkInspector; missing cache numbers render as em dashes,
//           never fabricated. Empty arrays render empty sections.
// ---------------------------------------------------------------------------

import { useMemo, useRef, useState } from "react";
import { ArrowUpRight, Database, FileText, Table2 } from "lucide-react";
import {
  getCacheStats,
  getCorpus,
  getKnowledgeGaps,
  getRetrievalDemo,
} from "@/lib/dataSource";
import { navigate } from "@/lib/router";
import { sourceLabel } from "@/components/qna/sourceLabel";
import type { KbChunk, KbDocument } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ChunkInspector } from "@/components/kb/ChunkInspector";
import { CorpusTree } from "@/components/kb/CorpusTree";
import { DocumentCard } from "@/components/kb/DocumentCard";
import { ScoreBar } from "@/components/kb/ScoreBar";
import { Band } from "@/components/observability/primitives";

interface ResolvedChunk {
  chunk: KbChunk;
  doc: KbDocument;
  section: string;
}

export function KnowledgeBase() {
  const corpus = getCorpus();
  const demos = getRetrievalDemo();
  const cache = getCacheStats();
  const gaps = getKnowledgeGaps();
  const { totals } = corpus;

  // Flat index: chunk_id → { chunk, doc, section } for the detail pane + retrieval clicks.
  const chunkIndex = useMemo(() => {
    const map = new Map<string, ResolvedChunk>();
    for (const doc of corpus.documents) {
      for (const sec of doc.sections) {
        for (const chunk of sec.chunks) {
          map.set(chunk.chunk_id, { chunk, doc, section: sec.section });
        }
      }
    }
    return map;
  }, [corpus]);

  const firstChunkId = corpus.documents[0]?.sections[0]?.chunks[0]?.chunk_id ?? null;
  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(firstChunkId);
  const [focusDocSource, setFocusDocSource] = useState<string | null>(null);
  const browseRef = useRef<HTMLDivElement>(null);

  const selected = selectedChunkId ? chunkIndex.get(selectedChunkId) ?? null : null;

  const openDocInBrowse = (doc: KbDocument) => {
    setFocusDocSource(doc.source);
    // Select the doc's first chunk so the detail pane reflects the jump.
    const first = doc.sections[0]?.chunks[0]?.chunk_id ?? null;
    if (first) setSelectedChunkId(first);
    browseRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const selectFromRetrieval = (chunkId: string) => {
    if (chunkIndex.has(chunkId)) {
      setSelectedChunkId(chunkId);
      const doc = chunkIndex.get(chunkId)!.doc;
      setFocusDocSource(doc.source);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-border px-8 py-5">
        <div className="eyebrow">◦ Knowledge Base</div>
        <h1 className="mt-1 font-display text-display font-semibold tracking-tight text-ink">
          What the system knows
        </h1>
        <p className="mt-1 font-mono text-meta tabular-nums text-ink-muted">
          {totals.chunks} chunks · {totals.documents} documents · {totals.sections} sections
          <span className="text-ink-faint">
            {"  ·  "}
            {corpus.vector_store.backend} / {corpus.vector_store.metric} · {corpus.vector_store.dim}-dim{" "}
            {corpus.vector_store.embedding_model}
          </span>
        </p>
      </header>

      <div className="scroll-quiet flex-1 space-y-14 overflow-y-auto px-8 py-9">
        {/* ── Band A · Corpus at a glance ─────────────────────────────── */}
        <Band eyebrow="A · Corpus" title="Corpus at a glance">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {corpus.documents.map((doc) => (
              <DocumentCard key={doc.source} doc={doc} onOpen={() => openDocInBrowse(doc)} />
            ))}
          </div>
          <ElementRibbon prose={totals.prose} tables={totals.tables} />
        </Band>

        {/* ── Band B · Browse ─────────────────────────────────────────── */}
        <div ref={browseRef}>
          <Band eyebrow="B · Browse" title="Browse the corpus">
            <div className="grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-border bg-border lg:grid-cols-[20rem_1fr]">
              <div className="bg-surface">
                <CorpusTree
                  documents={corpus.documents}
                  selectedChunkId={selectedChunkId}
                  onSelectChunk={setSelectedChunkId}
                  focusDocSource={focusDocSource}
                />
              </div>
              <div className="scroll-quiet max-h-[34rem] overflow-y-auto bg-surface-alt/40 p-5">
                {selected ? (
                  <DetailPane resolved={selected} />
                ) : (
                  <div className="grid h-full place-items-center text-meta text-ink-faint">
                    Select a chunk from the tree to inspect it.
                  </div>
                )}
              </div>
            </div>
          </Band>
        </div>

        {/* ── Band C · Retrieval demo ─────────────────────────────────── */}
        <Band eyebrow="C · Retrieval" title="Retrieval demo">
          <RetrievalDemo demos={demos} onOpenChunk={selectFromRetrieval} chunkIndex={chunkIndex} />
        </Band>

        {/* ── Band D · Cache ──────────────────────────────────────────── */}
        <Band eyebrow="D · Cache" title="Cache">
          <CacheBand cache={cache} />
        </Band>

        {/* ── Band E · Coverage gaps ──────────────────────────────────── */}
        <Band eyebrow="E · Coverage" title="Where documentation is thin">
          <CoverageGaps gaps={gaps} />
        </Band>
      </div>
    </div>
  );
}

/* ───────────────────────────── Band A ribbon ─────────────────────────── */

function ElementRibbon({ prose, tables }: { prose: number; tables: number }) {
  const total = Math.max(prose + tables, 1);
  const prosePct = (prose / total) * 100;
  return (
    <div className="mt-5 rounded-xl border border-border-subtle bg-surface px-5 py-4">
      <div className="flex items-center justify-between text-micro">
        <span className="label-micro flex items-center gap-1.5 text-ink-muted">
          <FileText className="h-3.5 w-3.5" strokeWidth={1.75} /> Prose
          <span className="font-mono tabular-nums text-ink-faint">{prose}</span>
        </span>
        <span className="label-micro flex items-center gap-1.5 text-[#5D6A53]">
          <Table2 className="h-3.5 w-3.5" strokeWidth={2} /> Table
          <span className="font-mono tabular-nums text-ink-faint">{tables}</span>
        </span>
      </div>
      <div className="mt-2.5 flex h-2.5 overflow-hidden rounded-full bg-surface-alt ring-1 ring-inset ring-border-subtle">
        <div className="h-full bg-sage" style={{ width: `${prosePct}%` }} aria-hidden />
        <div className="h-full bg-[rgba(139,157,131,0.4)]" style={{ width: `${100 - prosePct}%` }} aria-hidden />
      </div>
    </div>
  );
}

/* ───────────────────────────── Band B detail pane ────────────────────── */

function DetailPane({ resolved }: { resolved: ResolvedChunk }) {
  const { chunk, doc, section } = resolved;
  return (
    <div className="space-y-4">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="eyebrow">◦ {sourceLabel(doc.source)}</span>
          <span className="rounded-md border border-accent/40 bg-accent/10 px-1.5 py-0.5 font-mono text-micro font-semibold tabular-nums text-accent">
            v{doc.doc_version}
          </span>
        </div>
        <h3 className="mt-1.5 font-display text-lead font-semibold tracking-tight text-ink">{section}</h3>
        <p className="mt-0.5 font-mono text-micro text-ink-faint">{doc.doc_number ?? "—"}</p>
      </div>
      <ChunkInspector
        chunkId={chunk.chunk_id}
        elementType={chunk.element_type}
        text={chunk.text}
        tableMarkdown={chunk.table_markdown}
      />
    </div>
  );
}

/* ───────────────────────────── Band C retrieval ──────────────────────── */

function RetrievalDemo({
  demos,
  onOpenChunk,
  chunkIndex,
}: {
  demos: ReturnType<typeof getRetrievalDemo>;
  onOpenChunk: (chunkId: string) => void;
  chunkIndex: Map<string, ResolvedChunk>;
}) {
  const [active, setActive] = useState(0);
  const query = demos[active];

  if (!demos.length) {
    return (
      <p className="rounded-xl border border-dashed border-border bg-surface-alt/50 px-5 py-6 text-center text-meta text-ink-faint">
        No seeded queries — retrieval activates against live hybrid_search in the deployed build.
      </p>
    );
  }

  const topScore = Math.max(...query.results.map((r) => r.score), 0);

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[16rem_1fr]">
      {/* seeded-query selector */}
      <div role="tablist" aria-label="Seeded retrieval queries" className="flex flex-col gap-1.5">
        {demos.map((d, i) => {
          const on = i === active;
          return (
            <button
              key={d.query}
              type="button"
              role="tab"
              aria-selected={on}
              onClick={() => setActive(i)}
              className={cn(
                "rounded-lg border px-3 py-2.5 text-left transition-colors",
                on
                  ? "border-accent/45 bg-accent/10 text-ink"
                  : "border-border bg-surface text-ink-muted hover:border-accent/30 hover:text-ink"
              )}
            >
              <div className="text-meta font-medium leading-snug">{d.query}</div>
              <div className="mt-1 font-mono text-micro text-ink-faint">{sourceLabel(d.source)}</div>
            </button>
          );
        })}
      </div>

      {/* ranked results */}
      <div className="min-w-0">
        <ol className="space-y-2">
          {query.results.map((r, i) => {
            const inCorpus = chunkIndex.has(r.chunk_id);
            const isTop = r.score === topScore;
            return (
              <li key={r.chunk_id}>
                <button
                  type="button"
                  onClick={() => inCorpus && onOpenChunk(r.chunk_id)}
                  disabled={!inCorpus}
                  className={cn(
                    "flex w-full flex-col gap-2 rounded-lg border bg-surface px-4 py-3 text-left transition-colors sm:flex-row sm:items-center",
                    inCorpus ? "border-border hover:border-accent/40" : "cursor-default border-border-subtle",
                    isTop && "ring-1 ring-inset ring-accent/40"
                  )}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-micro tabular-nums text-ink-faint">#{i + 1}</span>
                      <span
                        className={cn(
                          "label-micro rounded border px-1 py-px",
                          r.element_type === "TABLE"
                            ? "border-[rgba(139,157,131,0.5)] bg-[rgba(139,157,131,0.12)] text-[#5D6A53]"
                            : "border-border-subtle text-ink-faint"
                        )}
                      >
                        {r.element_type}
                      </span>
                      <span className="truncate text-meta text-ink">{r.section}</span>
                    </div>
                    <p className="mt-1 line-clamp-2 max-w-reading text-micro leading-relaxed text-ink-muted">
                      {r.snippet}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3 sm:flex-col sm:items-end sm:gap-1.5">
                    <ScoreBar score={r.score} isTop={isTop} />
                    <span className="font-mono text-micro text-ink-faint">v{r.doc_version}</span>
                  </div>
                </button>
              </li>
            );
          })}
        </ol>
        <p className="mt-3 text-micro text-ink-faint">
          Replayed retrieval — wires to live hybrid_search in the deployed build.
        </p>
      </div>
    </div>
  );
}

/* ───────────────────────────── Band D cache ──────────────────────────── */

function CacheBand({ cache }: { cache: ReturnType<typeof getCacheStats> }) {
  const { embedding, response } = cache;
  const ttlHours = Math.round(embedding.ttl_seconds / 3600);
  const m = response.measured;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Embedding cache — LIVE: a solid sage stat block. */}
        <div className="rounded-xl border border-[rgba(139,157,131,0.45)] bg-[rgba(139,157,131,0.08)] p-5">
          <div className="flex items-center justify-between">
            <span className="label-micro flex items-center gap-1.5 text-[#5D6A53]">
              <Database className="h-3.5 w-3.5" strokeWidth={2} /> Embedding cache
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-[rgba(139,157,131,0.5)] bg-surface px-2 py-0.5 text-micro font-semibold text-[#5D6A53]">
              <span className="h-1.5 w-1.5 rounded-full bg-sage" /> LIVE
            </span>
          </div>
          <div className="mt-4 flex items-end gap-2">
            <span className="font-display text-display font-semibold tabular-nums text-ink">
              {embedding.entries ?? "—"}
            </span>
            <span className="pb-1 text-meta text-ink-muted">entries cached</span>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-micro">
            <CacheStat label="TTL" value={`${ttlHours}h`} />
            <CacheStat label="Namespace" value={embedding.namespace} mono />
            <CacheStat label="Model" value={embedding.embedding_model} mono span2 />
          </dl>
          <p className="mt-3 border-t border-[rgba(139,157,131,0.3)] pt-3 text-micro text-ink-muted">
            {embedding.note}
          </p>
        </div>

        {/* Response cache — measured locally, no-op in the public demo. */}
        <div className="rounded-xl border border-border bg-surface p-5">
          <div className="flex items-center justify-between">
            <span className="label-micro flex items-center gap-1.5 text-ink-muted">
              <FileText className="h-3.5 w-3.5" strokeWidth={1.75} /> Response cache
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-border bg-surface-alt px-2 py-0.5 font-mono text-micro text-ink-faint">
              ⟳ local Redis only
            </span>
          </div>

          {m ? (
            <dl className="mt-4 grid grid-cols-3 gap-3 text-micro">
              <CacheStat label="Cold miss" value={`$${m.miss_cost_usd.toFixed(4)}`} mono />
              <CacheStat label="Cache hit" value={`$${m.hit_cost_usd.toFixed(4)}`} mono />
              <CacheStat label="Saved / hit" value={`~${m.saved_pct}%`} />
              <CacheStat label="Latency miss" value={`${(m.latency_miss_ms / 1000).toFixed(1)}s`} mono />
              <CacheStat label="Latency hit" value={`${(m.latency_hit_ms / 1000).toFixed(1)}s`} mono />
              <CacheStat label="Cost avoided" value={`$${m.cost_avoided_usd.toFixed(4)}`} mono />
            </dl>
          ) : (
            <p className="mt-4 text-micro text-ink-faint">Measured figures not available.</p>
          )}

          <ul className="mt-4 space-y-1.5">
            {response.namespaces.map((ns) => (
              <li
                key={ns.key}
                className="flex items-center justify-between gap-3 rounded-lg border border-border-subtle bg-surface/60 px-3 py-2"
              >
                <div className="min-w-0">
                  <div className="font-mono text-micro text-ink-muted">{ns.key}</div>
                  <div className="truncate text-micro text-ink-faint">{ns.purpose}</div>
                </div>
                <span className="shrink-0 font-mono text-micro tabular-nums text-ink-faint">
                  {ns.entries ?? "—"}
                </span>
              </li>
            ))}
          </ul>

          <p className="mt-3 border-t border-border-subtle pt-3 text-micro text-ink-faint">
            {response.activation_note}
          </p>
        </div>
      </div>

      {/* Measured economics band — only shown when measured figures are present. */}
      {m && (
        <div className="rounded-xl border border-border-subtle bg-surface-alt/50 p-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="label-micro text-ink-muted">Effective cost vs. hit rate (measured, local Redis)</span>
            <span className="font-mono text-micro text-ink-faint">judge always re-runs</span>
          </div>

          {/* Effective cost rows at 0 / 50 / 80 % hit rates + floor. */}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {[
              { label: "0% hits", value: m.effective_cost_0pct },
              { label: "50% hits", value: m.effective_cost_50pct },
              { label: "80% hits", value: m.effective_cost_80pct },
              { label: "floor", value: m.effective_cost_floor },
            ].map(({ label, value }) => (
              <div
                key={label}
                className="rounded-lg border border-border-subtle bg-surface px-3 py-2.5"
              >
                <div className="label-micro text-ink-faint">{label}</div>
                <div className="mt-1 font-mono text-meta tabular-nums text-ink">
                  ${value.toFixed(4)}
                </div>
              </div>
            ))}
          </div>

          {/* Why the judge always re-runs. */}
          <p className="mt-3 text-micro text-ink-muted">
            <span className="font-semibold">Why the judge re-runs:</span> grounding is never served stale.
            The judge (~{Math.round(m.judge_share * 100)}% of answer cost) verifies retrieved chunks against
            each question on every call — even a cache hit — so grounded answers are always fresh.
            Cost savings ({m.saved_pct}%) come from skipping the assemble step only.
          </p>

          {/* Honest framing note. */}
          <p className="mt-2 rounded-lg border border-border-subtle bg-surface/60 px-3 py-2 text-micro italic text-ink-faint">
            {m.note}
          </p>
        </div>
      )}
    </div>
  );
}

function CacheStat({ label, value, mono, span2 }: { label: string; value: string; mono?: boolean; span2?: boolean }) {
  return (
    <div className={cn(span2 && "col-span-2")}>
      <dt className="label-micro text-ink-faint">{label}</dt>
      <dd className={cn("mt-0.5 truncate text-ink", mono ? "font-mono text-micro" : "text-meta tabular-nums")}>
        {value}
      </dd>
    </div>
  );
}

/* ───────────────────────────── Band E coverage gaps ──────────────────── */

function CoverageGaps({ gaps }: { gaps: ReturnType<typeof getKnowledgeGaps> }) {
  if (!gaps.length) {
    return (
      <p className="rounded-xl border border-border bg-surface px-5 py-6 text-center text-meta text-ink-faint">
        No coverage gaps recorded — every answered part found grounded support.
      </p>
    );
  }
  return (
    <div className="rounded-xl border border-border bg-surface">
      <ul className="divide-y divide-border-subtle">
        {gaps.map((g, i) => (
          <li key={`${g.sub_question_id}-${i}`} className="flex items-center gap-3 px-4 py-3">
            <span className="min-w-0 flex-1">
              <span className="text-meta text-ink">{g.question_text}</span>
              <span className="ml-2 font-mono text-micro text-ink-faint">{sourceLabel(g.attempted_source)}</span>
            </span>
            <span className="shrink-0 rounded-full border border-[rgba(216,86,80,0.4)] bg-danger-soft px-2 py-0.5 font-mono text-micro text-danger">
              {g.reason}
            </span>
          </li>
        ))}
      </ul>
      <div className="flex items-center justify-between border-t border-border-subtle px-4 py-2.5">
        <span className="font-mono text-micro tabular-nums text-ink-faint">
          {gaps.length} part{gaps.length === 1 ? "" : "s"} could not be grounded
        </span>
        <button
          type="button"
          onClick={() => navigate("/observability")}
          className="inline-flex items-center gap-1 text-micro font-semibold text-accent transition-colors hover:text-accent-hover"
        >
          See all in Observe <ArrowUpRight className="h-3.5 w-3.5" strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}
