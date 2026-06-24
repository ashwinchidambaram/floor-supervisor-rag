"""deploy_render.py — create/deploy the Render web service via the Render API.

Reads RENDER_API_KEY + OPENROUTER_API_KEY from .env, generates a DEMO_ACCESS_KEY (printed once),
creates a free Docker web service from the GitHub repo (or reuses it if it exists), sets env vars,
and triggers a deploy. Prints the service URL + the access key.

Run: python -m scripts.deploy_render
"""

from __future__ import annotations

import os
import secrets
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

API = "https://api.render.com/v1"
REPO = "https://github.com/ashwinchidambaram/floor-supervisor-rag"
NAME = "floor-supervisor-rag"
KEY = os.environ["RENDER_API_KEY"]
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Accept": "application/json"}


def main() -> None:
    demo_key = os.getenv("DEMO_ACCESS_KEY") or secrets.token_urlsafe(12)
    openrouter = os.environ["OPENROUTER_API_KEY"]

    with httpx.Client(timeout=60) as c:
        # owner id
        owners = c.get(f"{API}/owners", headers=H).json()
        owner_id = owners[0]["owner"]["id"]
        print("owner:", owner_id)

        # reuse if it already exists
        existing = c.get(f"{API}/services", headers=H, params={"name": NAME, "limit": 20}).json()
        svc = next((s["service"] for s in existing if s["service"]["name"] == NAME), None)

        if svc is None:
            body = {
                "type": "web_service",
                "name": NAME,
                "ownerId": owner_id,
                "repo": REPO,
                "branch": "main",
                "autoDeploy": "yes",
                "serviceDetails": {
                    "runtime": "docker",
                    "plan": "free",
                    "region": "oregon",
                    "healthCheckPath": "/health",
                    "envSpecificDetails": {"dockerfilePath": "./Dockerfile"},
                },
                "envVars": [
                    {"key": "OPENROUTER_API_KEY", "value": openrouter},
                    {"key": "DEMO_ACCESS_KEY", "value": demo_key},
                    {"key": "ALLOWED_ORIGIN", "value": "*"},
                ],
            }
            r = c.post(f"{API}/services", headers=H, json=body)
            if r.status_code >= 300:
                print("CREATE FAILED", r.status_code, r.text)
                sys.exit(1)
            svc = r.json()["service"]
            print("created service:", svc["id"])
        else:
            print("reusing service:", svc["id"])
            # ensure env vars
            c.put(f"{API}/services/{svc['id']}/env-vars", headers=H, json=[
                {"key": "OPENROUTER_API_KEY", "value": openrouter},
                {"key": "DEMO_ACCESS_KEY", "value": demo_key},
                {"key": "ALLOWED_ORIGIN", "value": "*"},
            ])
            c.post(f"{API}/services/{svc['id']}/deploys", headers=H, json={})

        url = svc.get("serviceDetails", {}).get("url") or f"https://{NAME}.onrender.com"
        print("\n=== RENDER ===")
        print("service id :", svc["id"])
        print("url        :", url)
        print("DEMO_ACCESS_KEY (share with the interviewer):", demo_key)


if __name__ == "__main__":
    main()
