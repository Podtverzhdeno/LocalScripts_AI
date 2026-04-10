"""
Quick test script to debug project mode issues.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from agents.architect import ArchitectAgent
from llm.factory import get_llm

print("="*60)
print("Testing Architect Agent")
print("="*60)

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
    import traceback
    traceback.print_exc()
    sys.exit(1)
