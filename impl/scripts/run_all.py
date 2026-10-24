#!/usr/bin/env python3
"""Run every generation strategy and evaluation on every CUT module, then aggregate."""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from fetch_libraries import load_libraries

SCRIPTS_DIR = Path(__file__).parent
IMPL_DIR = SCRIPTS_DIR.parent
CUT_DIR = IMPL_DIR / "cut"
TESTS_DIR = IMPL_DIR / "tests_generated"
RESULTS_DIR = IMPL_DIR / "results"

# --dry-run uses the offline mock LLM and writes here, so real tests/results are untouched.
DRY_RUN_DIR = IMPL_DIR / "dry_run"

STRATEGIES = {
    "single": "generate_single.py",
    "competitive": "generate_competitive.py",
    "collab": "generate_collab.py",
}
EVALUATIONS = ("coverage", "mutation", "diversity")


def discover_modules() -> list:
    """Return the names of all CUT modules in impl/cut/ (excluding private files)."""
    return sorted(
        p.stem for p in CUT_DIR.glob("*.py") if not p.name.startswith("_")
    )


def _run_step(label: str, script: str, args: list, env: dict = None) -> bool:
    """Run one script as a subprocess. Returns True on success."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script)] + args
    print(f"\n[run_all] >>> {label}")
    start = time.time()
    result = subprocess.run(cmd, cwd=str(IMPL_DIR), env=env)
    elapsed = time.time() - start
    ok = result.returncode == 0
    status = "ok" if ok else f"FAILED (exit {result.returncode})"
    print(f"[run_all] <<< {label}: {status} in {elapsed:.1f}s")
    return ok


def run_all(
    modules: list,
    strategies: list,
    evaluations: list,
    skip_generate: bool = False,
    num_tests: int = 10,
    dry_run: bool = False,
) -> list:
    """
    Generate and evaluate tests for every (module, strategy) pair.

    Args:
        modules: CUT module names (files in impl/cut/).
        strategies: Generation strategies to run ('single', 'competitive', 'collab').
        evaluations: Evaluations to run ('coverage', 'mutation', 'diversity').
        skip_generate: Reuse existing tests in tests_generated/ instead of calling the LLM.
        num_tests: Number of tests per agent passed to the generation scripts.
        dry_run: Use the offline mock LLM and write tests/results under impl/dry_run/.

    Returns:
        List of labels of steps that failed.
    """
    failures = []

    tests_dir, results_dir = TESTS_DIR, RESULTS_DIR
    env = None
    if dry_run:
        tests_dir = DRY_RUN_DIR / "tests_generated"
        results_dir = DRY_RUN_DIR / "results"
        env = {**os.environ, "LLM_PROVIDER": "mock", "RESULTS_DIR": str(results_dir)}
        print(f"[run_all] Dry run: mock LLM, output under {DRY_RUN_DIR}")

    for module in modules:
        for strategy in strategies:
            test_dir = tests_dir / strategy
            test_file = test_dir / f"test_{module}.py"

            if not skip_generate:
                ok = _run_step(
                    f"{module} / {strategy} / generate",
                    STRATEGIES[strategy],
                    [
                        "--cut-module", module,
                        "--num-tests", str(num_tests),
                        "--output-dir", str(test_dir),
                    ],
                    env,
                )
                if not ok:
                    failures.append(f"{module}/{strategy}/generate")
                    continue

            if not test_file.exists():
                print(f"[run_all] No tests at {test_file}; skipping evaluation.")
                failures.append(f"{module}/{strategy}/missing-tests")
                continue

            for evaluation in evaluations:
                args = ["--test-dir", str(test_dir), "--cut-module", module]
                if evaluation == "coverage":
                    args += ["--report-format", "json"]
                ok = _run_step(
                    f"{module} / {strategy} / {evaluation}",
                    f"eval_{evaluation}.py",
                    args,
                    env,
                )
                if not ok:
                    failures.append(f"{module}/{strategy}/{evaluation}")

    _run_step("aggregate", "aggregate.py", ["--results-dir", str(results_dir)], env)
    return failures


def main():
    available = discover_modules()
    libraries = load_libraries()
    missing = [name for name in libraries if name not in available]
    if missing:
        print(
            f"[run_all] Libraries in libraries.json not yet in cut/: {', '.join(missing)}. "
            f"Run 'python scripts/fetch_libraries.py' to add them."
        )

    parser = argparse.ArgumentParser(
        description="Run every strategy and evaluation on every CUT module, then aggregate"
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--modules",
        nargs="+",
        default=available,
        choices=available,
        metavar="MODULE",
        help=f"CUT modules to run (default: all: {', '.join(available)})",
    )
    selection.add_argument(
        "--libraries",
        action="store_true",
        help="Run only the third-party libraries listed in libraries.json",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=list(STRATEGIES),
        choices=list(STRATEGIES),
        help="Generation strategies to run (default: all)",
    )
    parser.add_argument(
        "--evaluations",
        nargs="+",
        default=list(EVALUATIONS),
        choices=list(EVALUATIONS),
        help="Evaluations to run (default: all)",
    )
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Reuse existing generated tests instead of calling the LLM",
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=10,
        help="Number of test cases to generate per agent",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check the pipeline offline: mock LLM, output under impl/dry_run/ (scores not meaningful)",
    )

    args = parser.parse_args()
    modules = args.modules
    if args.libraries:
        modules = [name for name in libraries if name in available]
    failures = run_all(
        modules=modules,
        strategies=args.strategies,
        evaluations=args.evaluations,
        skip_generate=args.skip_generate,
        num_tests=args.num_tests,
        dry_run=args.dry_run,
    )

    if failures:
        print(f"\n[run_all] {len(failures)} step(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\n[run_all] All steps completed successfully.")


if __name__ == "__main__":
    main()
