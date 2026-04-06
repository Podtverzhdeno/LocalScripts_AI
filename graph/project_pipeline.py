"""
Project Mode Pipeline — orchestrates multi-file project generation with evolution.

Phases:
1. Architect: plan project structure
2. Generator: create files according to plan
3. Decomposer: analyze code and create manifest
4. Evolver: find improvements and iterate (optional)
"""

from pathlib import Path
from typing import Optional
import json

from agents.architect import ArchitectAgent
from agents.generator import GeneratorAgent
from agents.validator import ValidatorAgent
from agents.reviewer import ReviewerAgent
from agents.decomposer import DecomposerAgent
from agents.evolver import EvolverAgent
from llm.factory import get_llm
from tools.lua_runner import LuaRunner
from config.loader import load_settings


def run_project_pipeline(
    requirements: str,
    project_dir: str,
    max_iterations: int = 3,
    evolutions: int = 3,
) -> dict:
    """
    Run full project mode pipeline.

    Args:
        requirements: Project requirements (from --spec or --task)
        project_dir: Output directory (workspace/project_TIMESTAMP/)
        max_iterations: Max retries per file generation
        evolutions: Number of evolution cycles (0 = no evolution, -1 = auto)

    Returns:
        Final project state with all metadata
    """
    project_path = Path(project_dir)
    src_dir = project_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("  PHASE 1: Architecture Planning")
    print("="*60)

    # Phase 1: Architect plans the project
    architect = ArchitectAgent(get_llm("architect"))
    plan = architect.plan(requirements)

    print(f"[Architect] Planned {len(plan['files'])} files:")
    for file_info in plan['files']:
        print(f"  - {file_info['name']}: {file_info['purpose']}")

    # Save plan
    (project_path / "project_plan.json").write_text(
        json.dumps(plan, indent=2), encoding="utf-8"
    )

    print("\n" + "="*60)
    print("  PHASE 2: Code Generation")
    print("="*60)

    # Phase 2: Generate files in dependency order
    generator = GeneratorAgent(get_llm("generator"))
    validator = ValidatorAgent(get_llm("validator"), _get_runner(project_path))
    reviewer = ReviewerAgent(get_llm("reviewer"))

    generated_files = []
    file_metrics = {}

    for file_name in plan['order']:
        print(f"\n[Generator] Creating {file_name}...")

        # Find file info from plan
        file_info = next((f for f in plan['files'] if f['name'] == file_name), None)
        if not file_info:
            print(f"  Warning: {file_name} not in plan, skipping")
            continue

        # Generate file
        task = f"Create {file_name}: {file_info['purpose']}\n"
        if file_info['dependencies']:
            task += f"Dependencies: {', '.join(file_info['dependencies'])}\n"

        # Simple generation loop (similar to quick mode)
        code = generator.generate(task=task, errors=None, review=None)

        # Validate
        is_valid, error_explanation = validator.validate(
            code=code, task=task, iteration=1
        )

        if not is_valid:
            print(f"  [Validator] ERROR in {file_name}")
            # TODO: Retry with error feedback
            continue

        print(f"  [Validator] OK")

        # Review
        is_done, feedback = reviewer.review(
            code=code,
            task=task,
            profile_metrics=validator._last_result.__dict__ if validator._last_result else None
        )

        if is_done:
            print(f"  [Reviewer] APPROVED")
        else:
            print(f"  [Reviewer] Feedback: {feedback[:80]}...")

        # Save file
        file_path = src_dir / file_name
        file_path.write_text(code, encoding="utf-8")
        generated_files.append(file_name)

        # Store metrics
        if validator._last_result:
            file_metrics[file_name] = {
                "time": validator._last_result.execution_time,
                "memory": validator._last_result.memory_used
            }

    print("\n" + "="*60)
    print("  PHASE 3: Project Analysis")
    print("="*60)

    # Phase 3: Decomposer analyzes the project
    decomposer = DecomposerAgent(get_llm())
    manifest = decomposer.analyze(project_path, generated_files)

    # Save manifest
    (project_path / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    # Create README
    decomposer.create_readme(project_path, plan, manifest)

    print(f"[Decomposer] Analyzed {manifest['total_files']} files")
    print(f"  Total lines: {manifest['total_lines']}")

    # Phase 4: Evolution (if requested)
    if evolutions > 0:
        print("\n" + "="*60)
        print(f"  PHASE 4: Evolution ({evolutions} cycles)")
        print("="*60)

        evolver = EvolverAgent(get_llm())
        evolution_history = []

        for cycle in range(evolutions):
            print(f"\n[Evolution {cycle + 1}/{evolutions}]")

            analysis = evolver.analyze(manifest, file_metrics)

            if not analysis["should_evolve"]:
                print("  No improvements needed, stopping evolution")
                break

            print(f"  Found {len(analysis['improvements'])} improvements")
            for imp in analysis['improvements']:
                print(f"    - {imp['file']}: {imp['issue']}")

            # TODO: Apply improvements
            # For now, just log
            evolution_history.append({
                "cycle": cycle + 1,
                "improvements": analysis['improvements']
            })

        # Save evolution history
        (project_path / "evolution_history.json").write_text(
            json.dumps(evolution_history, indent=2), encoding="utf-8"
        )

    print("\n" + "="*60)
    print("  Project Complete!")
    print("="*60)
    print(f"  Files: {len(generated_files)}")
    print(f"  Output: {project_path}")

    return {
        "status": "done",
        "files": generated_files,
        "manifest": manifest,
        "project_dir": str(project_path)
    }


def _get_runner(project_path: Path) -> LuaRunner:
    """Create LuaRunner for project validation."""
    settings = load_settings()
    pipeline_cfg = settings["pipeline"]
    timeout = pipeline_cfg.get("execution_timeout", 10)

    import os
    sandbox_mode = os.getenv("SANDBOX_MODE", pipeline_cfg.get("sandbox_mode", "lua"))

    return LuaRunner(session_dir=project_path / "validation", timeout=timeout, sandbox=sandbox_mode)
