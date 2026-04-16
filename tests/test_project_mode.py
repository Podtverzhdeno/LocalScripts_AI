"""
Quick test script to debug project mode issues.
"""
import sys
import socket
import pytest
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

# Skip ALL tests in this module if Ollama not available
if not is_ollama_available():
    pytest.skip("Ollama service not available on localhost:11434", allow_module_level=True)

print("="*60)
print("Testing Architect Agent")
print("="*60)

try:
    print("\n1. Creating LLM for architect...")
    llm = get_llm("architect")
    print(f"   [OK] LLM created: {type(llm).__name__}")

    # ... rest of your test code ...
