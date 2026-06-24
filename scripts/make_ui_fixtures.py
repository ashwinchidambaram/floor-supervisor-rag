"""make_ui_fixtures.py — build the UI's playback fixtures from the REAL pipeline + corpus.

Outputs (all disk-safe, MemorySaver — no checkpoint bloat):
  ui/public/conversation_*.json   — 2 extra real recorded conversations (export_data_out shape)
  ui/public/kb_index.json         — the indexed corpus (docs → sections → chunks + verbatim tables),
                                    a seeded retrieval demo (real hybrid_search hits), + cache stats.
The existing mock_data/conversation_real.json is also copied to ui/public/ as a 3rd conversation.

Run: python -m scripts.make_ui_fixtures
"""

from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver

from src.graph import build_graph
from src.observability import export_data_out, reset_sink
from src.state import ConversationState, DocSource, Turn
from src.tools.chunker import chunk_markdown
from src.tools.hybrid_search import hybrid_search
from src.tools.redis_client import get_redis

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "ui" / "public"
CORPUS = sorted((ROOT / "knowledge_documents_rag").glob("*.md"))

# Two extra conversations (real pipeline). Each list = the turns of one conversation/thread.
CONVERSATIONS: dict[str, list[str]] = {
    # (safety + real already generated; regenerate only quality with groundable QC questions)
    "quality": [
        "What is required for a first article inspection?",
        "What torque do the VF-4 spindle housing bolts need?",
    ],
}


def _ask(app, config, supervisor_id, question):
    snap = app.get_state(config)
    state = (ConversationState.model_validate(snap.values) if snap.values
             else ConversationState(conversation_id=config["configurable"]["thread_id"], supervisor_id=supervisor_id))
    state.current_turn = Turn(turn_id=f"t{len(state.turns) + 1}", question_text=question)
    return ConversationState.model_validate(app.invoke(state, config=config))


def build_conversations() -> None:
    app = build_graph(checkpointer=MemorySaver())
    for key, questions in CONVERSATIONS.items():
        reset_sink()
        config = {"configurable": {"thread_id": f"conv-{key}"}}
        state = None
        for q in questions:
            state = _ask(app, config, f"sup-{key}", q)
            t = state.turns[-1]
            print(f"  [{key}] {q[:48]}… → {t.status.value}/{t.turn_confidence.value if t.turn_confidence else '-'}")
        out = PUBLIC / f"conversation_{key}.json"
        out.write_text(json.dumps(export_data_out(state), indent=2))
        print(f"  wrote {out.relative_to(ROOT)}")
    # 3rd conversation: reuse the smoke output if present
    real = ROOT / "mock_data" / "conversation_real.json"
    if real.exists():
        (PUBLIC / "conversation_real.json").write_text(real.read_text())
        print("  copied conversation_real.json")


def _doc_meta(path: Path) -> dict:
    """Parse doc_number / effective_date from the header metadata table."""
    text = path.read_text(encoding="utf-8")
    num = re.search(r"Document Number\s*\|\s*([^\|\n]+)", text)
    eff = re.search(r"Effective Date\s*\|\s*([^\|\n]+)", text)
    sup = re.search(r"Supersedes\s*\|\s*([^\|\n]+)", text)
    return {
        "doc_number": (num.group(1).strip() if num else None),
        "effective_date": (eff.group(1).strip() if eff else None),
        "supersedes": (sup.group(1).strip() if sup else None),
    }


def build_kb_index() -> None:
    documents = []
    totals = {"chunks": 0, "documents": 0, "sections": 0, "tables": 0, "prose": 0}
    for path in CORPUS:
        chunks = chunk_markdown(path)
        if not chunks:
            continue
        meta = _doc_meta(path)
        sections: "OrderedDict[str, list]" = OrderedDict()
        for c in chunks:
            sections.setdefault(c.section, []).append({
                "chunk_id": c.chunk_id,
                "element_type": c.element_type.value,
                "text": c.text[:240],
                "table_markdown": c.table_markdown,
            })
        n_tables = sum(1 for c in chunks if c.element_type.value == "TABLE")
        documents.append({
            "source": chunks[0].source.value,
            "doc_title": chunks[0].doc_title,
            "doc_number": meta["doc_number"],
            "doc_version": chunks[0].doc_version,
            "effective_date": meta["effective_date"],
            "supersedes": meta["supersedes"],
            "counts": {"chunks": len(chunks), "sections": len(sections),
                       "tables": n_tables, "prose": len(chunks) - n_tables},
            "sections": [{"section": s, "chunks": cs} for s, cs in sections.items()],
        })
        totals["chunks"] += len(chunks); totals["documents"] += 1
        totals["sections"] += len(sections); totals["tables"] += n_tables
        totals["prose"] += len(chunks) - n_tables

    # Seeded retrieval demo — real hybrid_search hits.
    demo_specs = [
        ("M12 vise jaw torque value", DocSource.MAINTENANCE_MANUALS),
        ("lockout tagout before maintenance", DocSource.SAFETY_PROCEDURES),
        ("Cpk acceptance criteria", DocSource.QUALITY_CONTROL),
    ]
    retrieval_demo = []
    for query, src in demo_specs:
        hits = hybrid_search(query, src, top_k=4)
        retrieval_demo.append({
            "query": query, "source": src.value,
            "results": [{"chunk_id": h.chunk_id, "section": h.section, "element_type": h.element_type.value,
                         "doc_version": h.doc_version, "score": round(h.score, 3), "snippet": h.text[:140],
                         "table_markdown": h.table_markdown} for h in hits],
        })

    # Embedding cache (LIVE) — real Redis key count; response cache (foreshadow) = nulls.
    try:
        emb_entries = sum(1 for _ in get_redis().scan_iter(match="cache:emb:*"))
    except Exception:
        emb_entries = None
    index = {
        "vector_store": {"backend": "Redis", "metric": "cosine", "embedding_model": "BAAI/bge-small-en-v1.5", "dim": 384},
        "totals": totals,
        "documents": documents,
        "retrieval_demo": retrieval_demo,
        "cache": {
            "embedding": {"status": "LIVE", "namespace": "cache:emb", "entries": emb_entries,
                          "ttl_seconds": 86400, "embedding_model": "BAAI/bge-small-en-v1.5",
                          "note": "Each unique string embedded once; reused for 24h."},
            "response": {"status": "PENDING_LIVE",
                         "namespaces": [{"key": "cache:llm", "purpose": "decompose · judge · assemble results", "entries": None},
                                        {"key": "cache:retrieval", "purpose": "source-filtered retrieval sets", "entries": None}],
                         "metrics_preview": {"hit_rate": None, "entries": None, "cost_avoided_usd": None},
                         "activation_note": "Populates as questions are asked once the Redis cache thread ships."},
        },
    }
    (PUBLIC / "kb_index.json").write_text(json.dumps(index, indent=2))
    print(f"  wrote ui/public/kb_index.json ({totals['chunks']} chunks, {totals['documents']} docs)")


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    print("Building UI fixtures…")
    build_conversations()
    build_kb_index()
    print("Done.")


if __name__ == "__main__":
    main()
