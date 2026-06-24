"""api.py — FastAPI service wrapping the grounded-RAG graph.

Role:     HTTP gateway for the UI + demo clients. Builds the LangGraph once at import,
          builds the RAG index on first boot if the Redis store is empty, then serves
          POST /ask (auth-gated) and GET /health (open).
Contract:
  POST /ask  — Authorization: Bearer <DEMO_ACCESS_KEY>
               Body: { question: str, thread_id: str | null }
               Returns: export_data_out(ConversationState) — same JSON shape the UI reads.
  GET /health — { "status": "ok", "index_loaded": bool }  (no model call)
Failure:  node-level exceptions are already caught by @traced_node (safe-degrade to FAILED).
          A top-level try/except in /ask is the final backstop; 500 with error detail.
"""

from __future__ import annotations

import logging
import os
import secrets
from contextlib import asynccontextmanager
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from src.graph import build_graph
from src.ingest import ingest
from src.observability import export_data_out
from src.state import ConversationState, Turn
from src.tools.hybrid_search import _store

# ---------------------------------------------------------------------------
# Module-level graph (built once; all requests share the MemorySaver)
# ---------------------------------------------------------------------------
app_graph = build_graph(checkpointer=MemorySaver())

# ---------------------------------------------------------------------------
# Lifespan: build the index if the Redis store is empty
# ---------------------------------------------------------------------------
@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Build the RAG index in-process on first boot.

    Requires OPENROUTER_API_KEY for the table-summary LLM calls (~20 s).
    If the store already has chunks (e.g., a warm Redis), this is a no-op.
    """
    if _store().count() == 0:
        print("[api] Redis index empty — building from knowledge_documents_rag/…")
        ingest()
        print("[api] Index build complete.")
    else:
        print(f"[api] Index already loaded ({_store().count()} chunks).")
    yield  # application runs here


# ---------------------------------------------------------------------------
# FastAPI app + CORS
# ---------------------------------------------------------------------------
app = FastAPI(title="Grounded-RAG API", version="1.0.0", lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGIN", "*")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer(auto_error=False)


def _require_auth(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> None:
    """Compare the bearer token to DEMO_ACCESS_KEY with constant-time compare."""
    expected = os.environ.get("DEMO_ACCESS_KEY", "")
    token = creds.credentials if creds else ""
    if not expected or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class AskRequest(BaseModel):
    question: str
    thread_id: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    """Unauth liveness + index-loaded check. No model call."""
    return {"status": "ok", "index_loaded": _store().count() > 0}


@app.post("/ask", dependencies=[Depends(_require_auth)])
def ask(req: AskRequest) -> dict:
    """Run one conversational turn through the graph and return export_data_out(state).

    Multi-turn memory: if a prior checkpointed state exists for this thread_id,
    it is loaded and only current_turn is replaced (the integration_smoke continuation
    pattern). For a new thread_id a fresh ConversationState is created.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="question must not be blank")

    cid = req.thread_id or uuid4().hex
    config = {"configurable": {"thread_id": cid}}

    try:
        # Multi-turn: load prior state from the checkpointer if it exists.
        snap = app_graph.get_state(config)
        if snap.values:
            state = ConversationState.model_validate(snap.values)
        else:
            state = ConversationState(
                conversation_id=cid,
                supervisor_id="demo-user",
            )

        # Replace working turn (sub_questions empty → decomposer runs for real).
        state.current_turn = Turn(
            turn_id=f"t{len(state.turns) + 1}",
            question_text=req.question,
            sub_questions=[],
        )

        result = app_graph.invoke(state, config=config)
        final = ConversationState.model_validate(result)
        return export_data_out(final)

    except HTTPException:
        raise
    except Exception as exc:
        # Final backstop — the node template already degrades safely, but just in case.
        # Log the real error server-side only; return a generic body so we don't leak
        # internal paths / infra detail to the caller.
        logging.getLogger("api").exception("unhandled error in /ask (thread=%s)", cid)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
