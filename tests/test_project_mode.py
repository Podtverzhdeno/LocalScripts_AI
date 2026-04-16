"""
Quick test script to debug project mode issues.
"""
import sys
import socket
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from agents.architect import ArchitectAgent
from llm.factory import get_llm

def is_ollama_available():
    """Check if Ollama is running."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 11434))
        sock.close()
        return result == 0
    except Exception:
        return False

print("="*60)
print("Testing Architect Agent")
print("="*60)

# Check Ollama availability first
if not is_ollama_available():
    print("\n⚠️  Ollama service not available on localhost:11434")
    print("   This test requires Ollama to be running.")
    print("   To fix: install and start Ollama, or run in an environment with Ollama.")
    sys.exit(0)  # Exit gracefully, not as error

try:
    print("\n1. Creating LLM for architect...")
    llm = get_llm("architect")
    print(f"   [OK] LLM created: {type(llm).__name__}")

    print("\n2. Creating ArchitectAgent...")
    architect = ArchitectAgent(llm)
    print(f"   [OK] Agent created")
    print(f"   System prompt length: {len(architect.system_prompt)} chars")

    print("\n3. Calling architect.plan()...")
    requirements = "create hello world program"
    print(f"   Requirements: {requirements}")

    plan = architect.plan(requirements)

    print("\n4. Plan received:")
    print(f"   Files: {len(plan.get('files', []))}")
    for f in plan.get('files', []):
        print(f"     - {f['name']}: {f['purpose']}")
    print(f"   Order: {plan.get('order', [])}")
    print(f"   Structure: {plan.get('structure', 'N/A')[:100]}...")

    print("\n[SUCCESS] Architect works correctly!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    if "Connection refused" in str(e) or "Errno 111" in str(e):
        print("\n[INFO] This appears to be an Ollama connection issue.")
        print("       The test will be skipped, not failed.")
        sys.exit(0)  # Graceful exit for CI
    else:
        import traceback
        traceback.print_exc()
        sys.exit(1)  # Real error
