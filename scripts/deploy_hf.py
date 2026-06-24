"""deploy_hf.py — deploy the FastAPI backend to a free Hugging Face Docker Space (no card).

Creates/updates the Space, sets secrets (OPENROUTER_API_KEY / DEMO_ACCESS_KEY / ALLOWED_ORIGIN),
uploads the backend (Dockerfile, requirements, src/, corpus) + a docker-SDK README, and prints the
URL + the demo access key. Uses the HF CLI's cached token.

Run: python -m scripts.deploy_hf
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import HfApi

load_dotenv(override=True)  # .env wins over any stale HF_TOKEN exported in the shell
ROOT = Path(__file__).resolve().parents[1]
REPO_ID = "axchidam/floor-supervisor-rag"

README = """---
title: Floor Supervisor RAG
emoji: 🏭
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---

Grounded-RAG floor-supervisor documentation Q&A — FastAPI backend (gated `POST /ask`, `GET /health`).
The UI lives on Vercel; this Space is the agentic backend (LangGraph + local fastembed retrieval).
"""


def main() -> None:
    api = HfApi(token=os.getenv("HF_TOKEN"))  # uses HF_TOKEN from .env if set, else the cached login
    demo_key = os.getenv("DEMO_ACCESS_KEY")
    if not demo_key:
        demo_key = secrets.token_urlsafe(12)
        with open(ROOT / ".env", "a") as f:
            f.write(f"\nDEMO_ACCESS_KEY={demo_key}\n")

    api.create_repo(REPO_ID, repo_type="space", space_sdk="docker", exist_ok=True)
    print("space repo ready:", REPO_ID)

    for key, val in [
        ("OPENROUTER_API_KEY", os.environ["OPENROUTER_API_KEY"]),
        ("DEMO_ACCESS_KEY", demo_key),
        ("ALLOWED_ORIGIN", "*"),
    ]:
        api.add_space_secret(repo_id=REPO_ID, key=key, value=val)
    print("secrets set")

    api.upload_file(path_or_fileobj=README.encode(), path_in_repo="README.md",
                    repo_id=REPO_ID, repo_type="space")
    api.upload_folder(
        folder_path=str(ROOT), repo_id=REPO_ID, repo_type="space",
        allow_patterns=["Dockerfile", "requirements.txt", ".dockerignore",
                        "src/**", "knowledge_documents_rag/**"],
        commit_message="Deploy backend",
    )

    url = f"https://{REPO_ID.replace('/', '-')}.hf.space"
    print("\n=== HUGGING FACE SPACE ===")
    print("dashboard:", f"https://huggingface.co/spaces/{REPO_ID}")
    print("API URL  :", url)
    print("DEMO_ACCESS_KEY (share with the interviewer):", demo_key)
    print("(the Space builds the Docker image now — ~3-6 min; first request also runs a one-time index build)")


if __name__ == "__main__":
    main()
