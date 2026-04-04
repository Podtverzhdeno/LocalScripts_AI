"""
LocalScript CLI — multi-agent Lua code generation system.
Usage:
  python main.py --task "write fibonacci in Lua"
  python main.py --task "write fibonacci" --output ./my_project/
  python main.py --task "sort a table" --backend ollama
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

import yaml

# Load .env from project root (not cwd) so it works regardless of launch directory
try:
    from dotenv import load_dotenv
    _ENV_FILE = Path(__file__).resolve().parent / ".env"
    load_dotenv(_ENV_FILE)
except ImportError:
    pass  # dotenv optional — env vars can be set directly


def load_settings() -> dict:
    from config.loader import load_settings as _load
    return _load()


def make_session_dir(base_dir: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session = Path(base_dir) / f"session_{timestamp}"
    session.mkdir(parents=True, exist_ok=True)
    return str(session)


def main():
    parser = argparse.ArgumentParser(
        description="LocalScript — multi-agent Lua code generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --task "write a fibonacci function"
  python main.py --task "parse CSV and sum a column" --output ./out/
  python main.py --task "implement quicksort" --backend ollama
  python main.py --task-file examples/tasks/fibonacci.txt
        """
    )

    parser.add_argument("--task", type=str, help="Lua task description")
    parser.add_argument("--task-file", type=str, help="Path to .txt file with task")
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory (default: workspace/session_TIMESTAMP/)"
    )
    parser.add_argument(
        "--backend", type=str, choices=["openai", "ollama"], default=None,
        help="LLM backend override (default: from settings.yaml)"
    )
    parser.add_argument(
        "--max-iterations", type=int, default=None,
        help="Max retry iterations (default: from settings.yaml)"
    )

    args = parser.parse_args()

    # Resolve task
    if args.task_file:
        task = Path(args.task_file).read_text(encoding="utf-8").strip()
    elif args.task:
        task = args.task
    else:
        parser.print_help()
        sys.exit(1)

    # Apply overrides
    if args.backend:
        os.environ["LLM_BACKEND"] = args.backend

    settings = load_settings()
    max_iterations = args.max_iterations or int(os.getenv(
        "MAX_ITERATIONS", settings["pipeline"]["max_iterations"]
    ))

    # Session directory
    base_dir = args.output or settings["workspace"]["base_dir"]
    session_dir = make_session_dir(base_dir)

    # Save task
    (Path(session_dir) / "task.txt").write_text(task, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  LocalScript — Multi-Agent Lua Generator")
    print(f"{'='*60}")
    print(f"  Task      : {task[:80]}{'...' if len(task) > 80 else ''}")
    print(f"  Backend   : {os.getenv('LLM_BACKEND', settings['llm']['backend'])}")
    print(f"  Max iters : {max_iterations}")
    print(f"  Session   : {session_dir}")
    print(f"{'='*60}\n")

    # Run pipeline
    from graph.pipeline import run_pipeline
    try:
        final_state = run_pipeline(
            task=task,
            session_dir=session_dir,
            max_iterations=max_iterations,
        )
    except Exception as e:
        err = str(e)
        print(f"\n  ✗ Pipeline error: {err}\n")
        if "api_key" in err.lower() or "authentication" in err.lower() or "401" in err:
            print("  Hint: Check OPENAI_API_KEY in your .env file")
        elif "not found" in err.lower() or "404" in err or "does not exist" in err.lower():
            print("  Hint: Model not available. Try setting in .env:")
            print("        LLM_MODEL=gpt-3.5-turbo")
            print("        LLM_MODEL=gpt-4o-mini")
            print("        LLM_MODEL=gpt-4o")
        elif "quota" in err.lower() or "429" in err or "rate" in err.lower():
            print("  Hint: Rate limit exceeded. Wait and retry.")
        elif "connect" in err.lower() or "timeout" in err.lower():
            print("  Hint: Connection failed. Check your internet.")
        import sys; sys.exit(1)

    # Summary
    print(f"\n{'='*60}")
    status = final_state["status"]
    if status == "done":
        print(f"  ✓ SUCCESS in {final_state['iterations']} iteration(s)")
        print(f"  Output: {session_dir}/final.lua")
    else:
        print(f"  ✗ FAILED after {final_state['iterations']} iteration(s)")
        print(f"  Partial output: {session_dir}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
