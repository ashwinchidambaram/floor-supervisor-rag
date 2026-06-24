"""Retrieval tests over the built `kb` index. These are the `table_summarizer` eval_metric:
'top-table retrieval hit on the golden table-value questions'. Skipped if the index isn't
built (run `python -m src.ingest` first) or Redis is down — they assert on REAL retrieval,
offline (no LLM at query time)."""

import pytest

from src.state import DocSource, ElementType
from src.tools.hybrid_search import hybrid_search, _store
from src.tools.redis_client import ping

pytestmark = pytest.mark.skipif(
    not ping() or _store().count() == 0,
    reason="kb index not built (run `python -m src.ingest`) or Redis down",
)


def test_table_value_question_hits_the_table():
    """A torque-spec question returns the torque TABLE with the exact value in verbatim markdown."""
    hits = hybrid_search("torque spec for the CNC VF-4 vise jaw bolts", DocSource.MAINTENANCE_MANUALS, top_k=3)
    assert hits, "expected retrieval hits"
    table_hits = [h for h in hits if h.element_type == ElementType.TABLE]
    assert table_hits, "expected at least one TABLE chunk in the top-3"
    assert any("80 N" in (h.table_markdown or "") for h in table_hits), "exact value must be present verbatim"


def test_exact_identifier_uses_bm25_half():
    """An exact fault code ('Alarm 144') surfaces the fault-code table — the BM25 half of hybrid."""
    hits = hybrid_search("Alarm 144 way lube low", DocSource.MAINTENANCE_MANUALS, top_k=3)
    assert any("144" in (h.table_markdown or h.text) for h in hits)


def test_source_filter_is_enforced():
    """Retrieval never crosses sources — a QC query only returns QC chunks."""
    hits = hybrid_search("inspection sampling acceptance criteria", DocSource.QUALITY_CONTROL, top_k=5)
    assert hits
    assert all(h.source == DocSource.QUALITY_CONTROL for h in hits)


def test_doc_version_is_carried():
    """Every retrieved chunk carries its load-bearing doc_version (for citation + version guarding)."""
    hits = hybrid_search("lockout tagout before maintenance", DocSource.SAFETY_PROCEDURES, top_k=3)
    assert hits
    assert all(h.doc_version and h.doc_version != "UNKNOWN" for h in hits)
