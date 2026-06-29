"""Pydantic models describing the incoming lead payload and processed output.

The incoming model uses the raw field names sent by upstream tools; the
processed model holds the canonical, transformed fields ready for actions.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class IncomingLead(BaseModel):
    """Raw lead payload as received from an upstream tool."""

    full_name: str = Field(min_length=1)
    email_address: str = Field(min_length=1)
    company_name: str | None = None
    source: str | None = None


class ProcessedLead(BaseModel):
    """Canonical lead after mapping and transforms have been applied."""

    name: str
    email: str
    company: str = ""
    source: str = "web"
