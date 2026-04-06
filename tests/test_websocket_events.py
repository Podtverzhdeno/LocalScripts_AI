#!/usr/bin/env python3
"""
Test the graph visualization by running a simple task and monitoring WebSocket events.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_websocket_events():
    """Test WebSocket event flow."""
    try:
        import websockets
    except ImportError:
        print("❌ websockets library not installed")
        print("   Install with: pip install websockets")
        return

    print("🧪 Testing Graph Visualization WebSocket Events\n")
    print("Connecting to ws://127.0.0.1:8001/api/ws/test_session...")

    try:
        async with websockets.connect("ws://127.0.0.1:8001/api/ws/test_session") as ws:
            print("✅ WebSocket connected!\n")
            print("Listening for events (Ctrl+C to stop)...\n")

            event_count = 0
            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    event = json.loads(message)
                    event_count += 1

                    # Pretty print event
                    event_type = event.get('event', 'unknown')

                    if event_type == 'node_enter':
                        node = event.get('node', '?')
                        iteration = event.get('iteration', '?')
                        print(f"🔵 [{event_count}] Node Enter: {node.upper()} (iteration {iteration})")
                    elif event_type == 'status':
                        status = event.get('status', '?')
                        iteration = event.get('iteration', '?')
                        print(f"📊 [{event_count}] Status: {status} (iteration {iteration})")
                    elif event_type == 'progress':
                        iteration = event.get('iteration', '?')
                        print(f"⏳ [{event_count}] Progress: iteration {iteration}")
                    elif event_type == 'completed':
                        status = event.get('status', '?')
                        iteration = event.get('iteration', '?')
                        print(f"✅ [{event_count}] Completed: {status} (iteration {iteration})")
                    elif event_type == 'error':
                        detail = event.get('detail', '?')
                        print(f"❌ [{event_count}] Error: {detail}")
                    else:
                        print(f"📨 [{event_count}] {event_type}: {json.dumps(event, indent=2)}")

                except asyncio.TimeoutError:
                    print("\n⏱️  No events for 30 seconds, stopping...")
                    break

            print(f"\n✅ Test complete! Received {event_count} events")

    except ConnectionRefusedError:
        print("❌ Connection refused. Is the API server running?")
        print("   Start with: python api/server.py --port 8001")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_websocket_events())
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
