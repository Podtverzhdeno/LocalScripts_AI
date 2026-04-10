"""
Test ArchitectAgent - plan project structure from requirements.
"""

from agents.architect import ArchitectAgent
from llm.factory import get_llm


def test_architect():
    llm = get_llm("architect")
    architect = ArchitectAgent(llm)

    requirements = """
Create an authentication system with the following features:
- User registration with username and password
- Login/logout functionality
- Session management
- Password hashing for security
"""

    print("Testing ArchitectAgent...")
    print(f"Requirements:\n{requirements}\n")

    plan = architect.plan(requirements)

    print("Generated Plan:")
    print(f"Files: {len(plan['files'])}")
    for file in plan['files']:
        print(f"  - {file['name']}: {file['purpose']}")
        if file['dependencies']:
            print(f"    Dependencies: {', '.join(file['dependencies'])}")

    print(f"\nArchitecture: {plan['structure']}")
    print(f"\nBuild order: {' -> '.join(plan['order'])}")


if __name__ == "__main__":
    test_architect()
