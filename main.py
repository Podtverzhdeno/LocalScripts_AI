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
  Quick Mode (single file):
    python main.py --task "write a fibonacci function"
    python main.py --task "parse CSV and sum a column" --output ./out/
    python main.py --task "implement quicksort" --backend ollama
    python main.py --task-file examples/tasks/fibonacci.txt

  Project Mode (multi-file with evolution):
    python main.py --mode project --spec requirements.md
    python main.py --mode project --task "create REST API with auth"
    python main.py --mode project --spec requirements.md --evolutions 5
    python main.py --mode project --task "authentication system" --evolutions 0
        """
    )

    parser.add_argument(
        "--mode", type=str, choices=["quick", "project"], default="quick",
        help="Execution mode: quick (single file, fast) or project (multi-file with evolution)"
    )
    parser.add_argument("--task", type=str, help="Task description (for both modes)")
    parser.add_argument("--task-file", type=str, help="Path to .txt file with task (quick mode)")
    parser.add_argument(
        "--spec", type=str,
        help="Path to requirements.md file (project mode only)"
    )
    parser.add_argument(
        "--evolutions", type=int, default=3,
        help="Number of evolution iterations (project mode only, 0 = no evolution, -1 = until no improvements)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory (default: workspace/session_TIMESTAMP/ or workspace/project_TIMESTAMP/)"
    )
    parser.add_argument(
        "--backend", type=str, choices=["openai", "ollama"], default=None,
        help="LLM backend override (default: from settings.yaml)"
    )
    parser.add_argument(
        "--max-iterations", type=int, default=None,
        help="Max retry iterations per file (default: from settings.yaml)"
    )
    parser.add_argument(
        "--sandbox", type=str, choices=["lua", "docker", "none"], default="lua",
        help="Sandbox mode: lua (default, Lua-level isolation), docker (full container isolation), none (unsafe)"
    )

    args = parser.parse_args()

    # Validate arguments based on mode
    if args.mode == "project":
        # Project mode: need either --spec or --task
        if not args.spec and not args.task:
            print("Error: Project mode requires either --spec or --task")
            parser.print_help()
            sys.exit(1)

        # Read spec file if provided
        if args.spec:
            spec_path = Path(args.spec)
            if not spec_path.exists():
                print(f"Error: Spec file not found: {args.spec}")
                sys.exit(1)
            task = spec_path.read_text(encoding="utf-8").strip()
        else:
            task = args.task
    else:
        # Quick mode: need either --task-file or --task
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
    if args.sandbox:
        os.environ["SANDBOX_MODE"] = args.sandbox

    settings = load_settings()
    max_iterations = args.max_iterations or int(os.getenv(
        "MAX_ITERATIONS", settings["pipeline"]["max_iterations"]
    ))

    # Session directory (different naming for project mode)
    base_dir = args.output or settings["workspace"]["base_dir"]
    if args.mode == "project":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = str(Path(base_dir) / f"project_{timestamp}")
        Path(session_dir).mkdir(parents=True, exist_ok=True)
    else:
        session_dir = make_session_dir(base_dir)

    # Save task/spec
    if args.mode == "project" and args.spec:
        # Copy original spec file
        import shutil
        shutil.copy(args.spec, Path(session_dir) / "requirements.md")
    else:
        (Path(session_dir) / "task.txt").write_text(task, encoding="utf-8")

    # Print header
    mode_name = "Project Mode" if args.mode == "project" else "Quick Mode"
    print(f"\n{'='*60}")
    print(f"  LocalScript — {mode_name}")
    print(f"{'='*60}")
    print(f"  Task      : {task[:80]}{'...' if len(task) > 80 else ''}")
    print(f"  Backend   : {os.getenv('LLM_BACKEND', settings['llm']['backend'])}")
    print(f"  Sandbox   : {args.sandbox}")
    print(f"  Max iters : {max_iterations}")
    if args.mode == "project":
        print(f"  Evolutions: {args.evolutions if args.evolutions >= 0 else 'until no improvements'}")
    print(f"  Output    : {session_dir}")
    print(f"{'='*60}\n")

    # Route to appropriate pipeline
    if args.mode == "project":
        from graph.project_pipeline import run_project_pipeline
        try:
            final_state = run_project_pipeline(
                requirements=task,
                project_dir=session_dir,
                max_iterations=max_iterations,
                evolutions=args.evolutions,
            )
            print(f"\n{'='*60}")
            print(f"  SUCCESS - Project created")
            print(f"  Files: {len(final_state['files'])}")
            print(f"  Output: {final_state['project_dir']}")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")
            sys.exit(1)
        return

    # Quick mode - existing pipeline
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
        sys.exit(1)

    # Summary
    print(f"\n{'='*60}")
    status = final_state["status"]
    if status == "done":
        print(f"  SUCCESS in {final_state['iterations']} iteration(s)")
        print(f"  Output: {session_dir}/final.lua")
    else:
        print(f"  FAILED after {final_state['iterations']} iteration(s)")
        print(f"  Partial output: {session_dir}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
