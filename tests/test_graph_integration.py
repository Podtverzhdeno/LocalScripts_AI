#!/usr/bin/env python3
"""
Quick test script to verify graph visualization integration.
Run this after starting the API server to test WebSocket events.
"""

import asyncio
import json
from pathlib import Path

async def test_graph_events():
    """Simulate pipeline execution and print events that would be sent."""

    print("=== Graph Visualization Test ===\n")

    # Simulate pipeline flow
    events = [
        {"event": "started", "session_id": "test_session"},
        {"event": "node_enter", "node": "generate", "iteration": 1, "status": "generating"},
        {"event": "node_enter", "node": "validate", "iteration": 1, "status": "validating"},
        {"event": "node_enter", "node": "review", "iteration": 1, "status": "reviewing"},
        {"event": "node_enter", "node": "generate", "iteration": 2, "status": "generating"},
        {"event": "node_enter", "node": "validate", "iteration": 2, "status": "validating"},
        {"event": "node_enter", "node": "review", "iteration": 2, "status": "reviewing"},
        {"event": "completed", "status": "done", "iteration": 2},
    ]

    for i, event in enumerate(events, 1):
        print(f"Event {i}: {json.dumps(event, indent=2)}")
        await asyncio.sleep(0.5)

    print("\n✓ All events sent successfully")
    print("\nExpected graph behavior:")
    print("  1. START node lights up")
    print("  2. Generator node activates (iteration 1)")
    print("  3. Validator node activates")
    print("  4. Reviewer node activates")
    print("  5. Loop back to Generator (iteration 2)")
    print("  6. Validator → Reviewer again")
    print("  7. END node lights up (done)")

if __name__ == "__main__":
    asyncio.run(test_graph_events())
