"""
Project Mode Pipeline — orchestrates multi-file project generation with evolution.

Phases:
1. Architect: plan project structure
2. Specification: create detailed specs for each file
3. Generator: create files according to specs
4. Integrator: test that all files work together
5. Decomposer: analyze code and create manifest
6. Evolver: find improvements and iterate (optional)
"""

from pathlib import Path
from typing import Optional
import json

from agents.architect import ArchitectAgent
from agents.specification import SpecificationAgent
from agents.generator import GeneratorAgent
from agents.validator import ValidatorAgent
from agents.reviewer import ReviewerAgent
from agents.integrator import IntegratorAgent
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
    node_callback=None,
) -> dict:
    """
    Run full project mode pipeline.

    Args:
        requirements: Project requirements (from --spec or --task)
        project_dir: Output directory (workspace/project_TIMESTAMP/)
        max_iterations: Max retries per file generation
        evolutions: Number of evolution cycles (0 = no evolution, -1 = auto)
        node_callback: Callback for node events (for frontend visualization)

    Returns:
        Final project state with all metadata
    """
    project_path = Path(project_dir)
    src_dir = project_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("  PHASE 1: Architecture Planning")
    print("="*60)

    # Notify frontend: architect node
    if node_callback:
        node_callback("architect", {"iteration": 0})

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
    print("  PHASE 2: Specification Creation")
    print("="*60)

    # Phase 2: Create detailed specifications for each file
    specification_agent = SpecificationAgent(get_llm("specification"))
    file_specs = {}
    existing_files = {}

    for file_name in plan['order']:
        file_info = next((f for f in plan['files'] if f['name'] == file_name), None)
        if not file_info:
            continue

        print(f"\n[Specification] Creating spec for {file_name}...")
        spec = specification_agent.create_spec(file_info, plan, existing_files)
        file_specs[file_name] = spec

        # Save spec
        spec_path = project_path / f"{file_name}.spec.json"
        spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        print(f"  Functions: {len(spec.get('functions', []))}")
        print(f"  Edge cases: {len(spec.get('edge_cases', []))}")

    print("\n" + "="*60)
    print("  PHASE 3: Code Generation")
    print("="*60)

    # Notify frontend: decomposer node
    if node_callback:
        node_callback("decomposer", {"iteration": 0})

    # Initialize RAG if enabled
    rag_system = None
    settings = load_settings()
    rag_config = settings.get("rag", {})
    if rag_config.get("enabled", False):
        try:
            from rag import create_rag_system, initialize_rag_with_examples
            rag_system = create_rag_system(rag_config)
            initialize_rag_with_examples(rag_system)
            print(f"[RAG] Enabled with {rag_system.get_stats()['total_documents']} documents")
        except Exception as e:
            print(f"[RAG] Failed to initialize: {e}")
            rag_system = None

    # Phase 2: Generate files in dependency order
    generator = GeneratorAgent(get_llm("generator"), rag_system=rag_system)
    validator = ValidatorAgent(get_llm("validator"), _get_runner(project_path))
    reviewer = ReviewerAgent(get_llm("reviewer"))

    generated_files = []
    file_metrics = {}

    for file_name in plan['order']:
        print(f"\n[Generator] Creating {file_name}...")

        # Notify frontend: generator node
        if node_callback:
            node_callback("generate", {"iteration": len(generated_files) + 1})

        # Find file info and spec
        file_info = next((f for f in plan['files'] if f['name'] == file_name), None)
        if not file_info:
            print(f"  Warning: {file_name} not in plan, skipping")
            continue

        spec = file_specs.get(file_name, {})

        # Build enhanced task description with specification
        task = f"Create {file_name}: {file_info['purpose']}\n\n"

        if spec.get('functions'):
            task += "Required functions:\n"
            for func in spec['functions']:
                params = ', '.join(func.get('params', []))
                task += f"  - {func['name']}({params}) -> {func.get('returns', 'void')}\n"
                task += f"    {func.get('description', '')}\n"
            task += "\n"

        if spec.get('dependencies_api'):
            task += "Available from dependencies:\n"
            for dep, apis in spec['dependencies_api'].items():
                task += f"  {dep}: {', '.join(apis)}\n"
            task += "\n"

        if spec.get('edge_cases'):
            task += f"Handle edge cases: {', '.join(spec['edge_cases'])}\n\n"

        if spec.get('example_usage'):
            task += f"Example usage:\n{spec['example_usage']}\n"

        # Retry loop with max_iterations
        code = None
        errors = None
        review_feedback = None

        for iteration in range(1, max_iterations + 1):
            try:
                print(f"  Iteration {iteration}/{max_iterations}")

                # Generate code
                code = generator.generate(task=task, errors=errors, review=review_feedback)

                if not code or not code.strip():
                    print(f"  [Generator] ERROR: Empty response from LLM")
                    if iteration < max_iterations:
                        errors = "Previous attempt returned empty code. Please generate valid Lua code."
                        continue
                    else:
                        break

                print(f"  [Generator] Generated {len(code)} chars")

                # Notify frontend: validator node
                if node_callback:
                    node_callback("validate", {"iteration": iteration})

                # Validate
                is_valid, error_explanation = validator.validate(
                    code=code, task=task, iteration=iteration
                )

                if not is_valid:
                    print(f"  [Validator] ERROR: {error_explanation[:100]}...")
                    if iteration < max_iterations:
                        errors = error_explanation
                        continue
                    else:
                        print(f"  [Validator] Max iterations reached, saving anyway")
                        break

                print(f"  [Validator] OK")

                # Notify frontend: reviewer node
                if node_callback:
                    node_callback("review", {"iteration": iteration})

                # Review
                is_done, feedback = reviewer.review(
                    code=code,
                    task=task,
                    profile_metrics=validator._last_result.__dict__ if validator._last_result else None
                )

                if is_done:
                    print(f"  [Reviewer] APPROVED")
                    break
                else:
                    print(f"  [Reviewer] Feedback: {feedback[:80]}...")
                    if iteration < max_iterations:
                        review_feedback = feedback
                        continue
                    else:
                        print(f"  [Reviewer] Max iterations reached, saving anyway")
                        break

            except Exception as e:
                print(f"  [ERROR] Exception during generation: {e}")
                if iteration < max_iterations:
                    errors = f"Previous attempt failed with error: {str(e)}"
                    continue
                else:
                    print(f"  [ERROR] Max iterations reached, skipping {file_name}")
                    code = None
                    break

        # Save file if we got any code
        if code and code.strip():
            file_path = src_dir / file_name
            file_path.write_text(code, encoding="utf-8")
            generated_files.append(file_name)
            existing_files[file_name] = code  # Add to context for next files
            print(f"  [SUCCESS] Saved {file_name}")

            # Store metrics
            if validator._last_result:
                file_metrics[file_name] = {
                    "time": validator._last_result.execution_time,
                    "memory": validator._last_result.memory_used
                }
        else:
            print(f"  [FAILED] Could not generate {file_name}")

    print("\n" + "="*60)
    print("  PHASE 3: Project Analysis")
    print("="*60)

    # Phase 3: Decomposer analyzes the project
    if not generated_files:
        print("\n[WARNING] No files were generated successfully")
        return {
            "status": "failed",
            "files": [],
            "manifest": None,
            "project_dir": str(project_path),
            "error": "No files generated"
        }

    # PHASE 3.5: Integration Testing (NEW!)
    print("\n" + "="*60)
    print("  PHASE 3.5: Integration Testing")
    print("="*60)

    integrator = IntegratorAgent(get_llm("integrator"), _get_runner(project_path))

    # Build files dict for integrator
    files_dict = {}
    for file_name in generated_files:
        file_path = src_dir / file_name
        if file_path.exists():
            files_dict[file_name] = file_path.read_text(encoding="utf-8")

    integration_result = integrator.test_integration(files_dict, plan, project_path)

    if integration_result["success"]:
        print("[Integrator] ✓ All modules integrated successfully")
    else:
        print(f"[Integrator] ✗ Found {len(integration_result['issues'])} integration issues:")
        for issue in integration_result['issues']:
            print(f"  - {issue['file']}: {issue['problem']}")

    # Save integration report
    integration_report_path = project_path / "integration_report.json"
    integration_report_path.write_text(
        json.dumps(integration_result, indent=2), encoding="utf-8"
    )

    print("\n" + "="*60)
    print("  PHASE 4: Code Analysis")
    print("="*60)

    decomposer = DecomposerAgent(get_llm("decomposer"))
    manifest = decomposer.analyze(project_path, generated_files)

    # Save manifest
    (project_path / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    # Create README
    decomposer.create_readme(project_path, plan, manifest)

    print(f"[Decomposer] Analyzed {manifest['total_files']} files")
    print(f"  Total lines: {manifest['total_lines']}")

    # Phase 4: Evolution (if requested and we have files)
    if evolutions > 0 and generated_files:
        print("\n" + "="*60)
        print(f"  PHASE 5: Evolution ({evolutions} cycles)")
        print("="*60)

        # Notify frontend: evolver node
        if node_callback:
            node_callback("evolver", {"iteration": 0})

        evolver = EvolverAgent(get_llm("evolver"))
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
        "integration": integration_result,
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
