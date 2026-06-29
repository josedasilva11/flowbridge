"""Pluggable actions and the dispatcher that runs them.

Every action implements the Action protocol: a run method that takes the
processed lead dict and its own config, and returns a status dict. Actions
are looked up by their config 'type' via the ACTION_REGISTRY.
"""

from __future__ import annotations

import csv
import os
import sqlite3
from pathlib import Path
from typing import Any, Protocol

import httpx


class Action(Protocol):
    """Structural interface every action must satisfy."""

    def run(self, lead: dict[str, str], config: dict[str, Any]) -> dict[str, Any]:
        """Execute the action for one processed lead."""
        ...


class SqliteAction:
    """Append the lead as a row in a local SQLite table."""

    def run(self, lead: dict[str, str], config: dict[str, Any]) -> dict[str, Any]:
        """Insert the lead, creating the database and table if needed."""
        db_path = config.get("db_path", "flowbridge.db")
        table = config.get("table", "leads")
        columns = list(lead.keys())
        col_defs = ", ".join(f"{c} TEXT" for c in columns)
        placeholders = ", ".join("?" for _ in columns)
        col_names = ", ".join(columns)
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {table} ("
                f"id INTEGER PRIMARY KEY AUTOINCREMENT, {col_defs})"
            )
            conn.execute(
                f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})",
                [lead[c] for c in columns],
            )
            conn.commit()
        return {"action": "sqlite", "status": "ok", "db_path": db_path, "table": table}


class OutgoingWebhookAction:
    """POST a formatted message to an outgoing webhook (Slack or Discord style).

    The target URL is read from the OUTGOING_WEBHOOK_URL environment variable.
    If it is unset, the action is skipped gracefully instead of failing.
    """

    def run(self, lead: dict[str, str], config: dict[str, Any]) -> dict[str, Any]:
        """Send the lead to the configured outgoing webhook."""
        url = os.environ.get("OUTGOING_WEBHOOK_URL", "").strip()
        if not url:
            return {
                "action": "outgoing_webhook",
                "status": "skipped",
                "reason": "OUTGOING_WEBHOOK_URL not set",
            }
        template = config.get("template", "New lead: {name} <{email}>")
        message = template.format(**{**{"name": "", "email": "", "company": "", "source": ""}, **lead})
        response = httpx.post(url, json={"text": message}, timeout=10.0)
        response.raise_for_status()
        return {
            "action": "outgoing_webhook",
            "status": "ok",
            "http_status": response.status_code,
        }


class CsvAction:
    """Append the lead as a row to a CSV file, writing a header if new."""

    def run(self, lead: dict[str, str], config: dict[str, Any]) -> dict[str, Any]:
        """Append one CSV row for the lead."""
        file_path = config.get("file_path", "leads.csv")
        path = Path(file_path)
        write_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(lead.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(lead)
        return {"action": "csv", "status": "ok", "file_path": file_path}


ACTION_REGISTRY: dict[str, Action] = {
    "sqlite": SqliteAction(),
    "outgoing_webhook": OutgoingWebhookAction(),
    "csv": CsvAction(),
}


def dispatch(
    lead: dict[str, str], action_configs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Run every configured action for one processed lead.

    Each action is isolated: if one raises, its failure is recorded and the
    remaining actions still run.

    Args:
        lead: The processed, canonical lead.
        action_configs: The list of action config dicts from config.yaml.

    Returns:
        A list of per-action status dicts.
    """
    results: list[dict[str, Any]] = []
    for cfg in action_configs:
        action_type = cfg.get("type")
        action = ACTION_REGISTRY.get(action_type) if action_type else None
        if action is None:
            results.append(
                {"action": action_type, "status": "error", "reason": "unknown action type"}
            )
            continue
        try:
            results.append(action.run(lead, cfg))
        except Exception as exc:  # isolate one action's failure from the rest
            results.append(
                {"action": action_type, "status": "error", "reason": str(exc)}
            )
    return results
