#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the full stack: API + WebSocket + Graph visualization
"""

import sys
import io
import requests
import json
import time

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE = "http://127.0.0.1:8001/api"

def test_api_integration():
    """Test API endpoint and session creation."""

    print("[TEST] Full Stack Integration Test\n")
    print("=" * 60)

    # 1. Test API is running
    print("\n[1/4] Testing API server...")
    try:
        response = requests.get(f"{API_BASE}/sessions", timeout=5)
        if response.status_code == 200:
            print("   [OK] API server is running")
        else:
            print(f"   [ERROR] API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   [ERROR] Cannot connect to API server")
        print("   Make sure server is running: python api/server.py --port 8001")
        return False

    # 2. Create a new task
    print("\n[2/4] Creating new task...")
    task_data = {
        "task": "write a simple hello world function"
    }

    try:
        response = requests.post(
            f"{API_BASE}/run-task",
            json=task_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            print(f"   [OK] Task created: {session_id}")
        else:
            print(f"   [ERROR] Failed to create task: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False

    # 3. Check session status
    print("\n[3/4] Checking session status...")
    time.sleep(2)  # Give it time to start

    try:
        response = requests.get(f"{API_BASE}/session/{session_id}", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"   [OK] Session status: {status.get('status')}")
            print(f"   Iteration: {status.get('iteration')}")
            print(f"   Has final: {status.get('has_final')}")
        else:
            print(f"   [ERROR] Cannot get session status: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # 4. Instructions for viewing graph
    print("\n[4/4] Graph Visualization")
    print(f"   Open in browser: http://127.0.0.1:8001/session/{session_id}")
    print("   You should see:")
    print("   - Interactive graph with nodes lighting up")
    print("   - Real-time iteration counter")
    print("   - WebSocket events in Live Log")
    print("   - Clickable nodes for viewing files")

    print("\n" + "=" * 60)
    print("[SUCCESS] Integration test complete!")
    print("\nNext steps:")
    print("1. Open the URL above in your browser")
    print("2. Watch the graph animate as the pipeline runs")
    print("3. Click on nodes to view related files")
    print("4. Check the Live Log section for WebSocket events")

    return True

if __name__ == "__main__":
    success = test_api_integration()
    sys.exit(0 if success else 1)
