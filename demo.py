"""Offline upload demonstration using only fixed, synthetic key events."""

from __future__ import annotations

import json


def run_sample_upload_demo() -> dict[str, object]:
    """Show a request/receipt exchange without reading files or using a network."""
    request = {
        "demo": True,
        "source": "synthetic_sample",
        "destination": "in_memory_demo_receiver",
        "events": [
            {"kind": "character", "value": "h"},
            {"kind": "character", "value": "i"},
            {"kind": "special", "value": "enter"},
        ],
    }

    # A JSON round trip models the payload crossing a transport boundary. The
    # receiver exists only in this process and cannot access recorded sessions.
    received = json.loads(json.dumps(request, ensure_ascii=False))
    receipt = {
        "status": "accepted_in_memory",
        "received_events": len(received["events"]),
        "network_sent": False,
    }
    return {"request": request, "receipt": receipt}
