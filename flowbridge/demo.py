"""End-to-end demo: process sample_lead.json through the full pipeline.

No server and no network are required. Run with: python -m flowbridge.demo
"""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from .pipeline import process_lead

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "sample_lead.json"


def main() -> None:
    """Load the sample lead, process it, and print a readable summary."""
    load_dotenv()
    with SAMPLE_PATH.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    print("Incoming lead:")
    print(json.dumps(raw, indent=2))

    outcome = process_lead(raw)

    print("\nProcessed (canonical) lead:")
    print(json.dumps(outcome["lead"], indent=2))

    print("\nAction results:")
    for result in outcome["results"]:
        print(f"  - {json.dumps(result)}")

    print("\nDone. Check flowbridge.db and leads.csv for the stored lead.")


if __name__ == "__main__":
    main()
