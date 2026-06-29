"""FastAPI application exposing the flowbridge webhook endpoint.

Run with: uvicorn flowbridge.app:app --reload
"""

from __future__ import annotations

from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import ValidationError
from fastapi.responses import JSONResponse

from .models import IncomingLead
from .pipeline import process_lead

load_dotenv()

app = FastAPI(
    title="flowbridge",
    description="Automation bridge: receive an event, transform it, dispatch to actions.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok"}


@app.post("/webhook")
def webhook(lead: IncomingLead) -> dict[str, Any]:
    """Receive a lead, run it through the pipeline, and report action results.

    Args:
        lead: The incoming lead, validated by FastAPI against IncomingLead.

    Returns:
        A dict with the processed lead and per-action results.
    """
    return process_lead(lead.model_dump())
