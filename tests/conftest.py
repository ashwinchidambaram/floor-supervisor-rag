"""Test-suite config.

The per-node response caches (retrieve_chunks / assemble_answer, spec §4b) are DISABLED for the
§11 forced-stub orchestration suite, so retrieval + assembly run deterministically and a local Redis
can never leak a cached result across tests. The dedicated cache test (test_cache.py) re-enables them
explicitly via monkeypatch. The embedding + table-summary caches are unaffected.
"""

import os

os.environ["RAG_DISABLE_NODE_CACHE"] = "1"
