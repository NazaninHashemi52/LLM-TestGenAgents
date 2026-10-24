#!/usr/bin/env python3
"""Aggregate evaluation results from multiple test generation runs."""

import argparse
import json
from pathlib import Path

from fetch_libraries import load_libraries

METHODS = ("single", "competitive", "collab")
EVAL_TYPES = ("coverage", "mutation", "diversity")

# Headline metrics shown first (and in the Markdown report), in this order.
KEY_METRICS = [
    "line_coverage",
    "branch_coverage",
    "function_coverage",
    "score_mutation",
    "diversity_score_diversity",
]


def _parse_result_name(stem: str):
    """
    Split a result file stem into (module, method, eval_type).

    Expected naming: {module}_{method}_{eval_type}, e.g. "bank_account_single_coverage".
    The module name may itself contain underscores. Returns None if the stem
    doesn't follow the convention.
    """
    parts = stem.rsplit("_", 2)
    if len(parts) != 3:
        return None
    module, method, eval_type = parts
    if method not in METHODS or eval_type not in EVAL_TYPES or not module:
        return None
    return module, method, eval_type


def _module_source(module: str, libraries: dict) -> str:
    """Return 'package==version' for a third-party library module, else 'built-in'."""
    entry = libraries.get(module)
    return f"{entry['package']}=={entry['version']}" if entry else "built-in"


def _to_markdown(df, float_fmt="{:.4f}") -> str:
    """Render a DataFrame as a GitHub-flavoured Markdown table (no extra deps)."""
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "|" + "|".join("---" for _ in cols) + "|",
    ]
    for _, row in df.iterrows():
        cells = [
            float_fmt.format(v) if isinstance(v, float) else str(v)
            for v in row.tolist()
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _write(df, path: Path, output_format: str) -> None:
    if output_format == "csv":
        df.to_csv(path, index=False)
    elif output_format == "json":
        df.to_json(path, orient="records", indent=2)
    elif output_format == "html":
        df.to_html(path, index=False)


def aggregate_results(
    results_dir: Path,
    output_file: Path = None,
    output_format: str = "csv",
) -> None:
    """
    Aggregate evaluation results from multiple test generation runs.

    Scans results_dir for JSON files named {module}_{method}_{eval_type}.json
    (e.g., calculator_single_coverage.json, bank_account_collab_mutation.json),
    and produces:

    - summary.<fmt>          one row per (module, method) with every metric
    - summary_overall.<fmt>  per-method mean of every metric across modules
    - summary.md             Markdown tables (one per module + overall)

    Args:
        results_dir: Directory containing evaluation result JSON files.
        output_file: File to save the per-module table (default: results_dir/summary.<fmt>).
            The overall table is saved next to it with an "_overall" suffix.
        output_format: Format for aggregated output ('csv', 'json', 'html').
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for aggregation. Install it with: pip install pandas"
        )

    results_dir = Path(results_dir)
    if not results_dir.exists():
        print(f"[aggregate] Results directory not found: {results_dir}")
        return

    rows = []
    for json_file in sorted(results_dir.glob("*.json")):
        parsed = _parse_result_name(json_file.stem)
        if parsed is None:
            if not json_file.stem.startswith("summary"):
                print(
                    f"[aggregate] Skipping {json_file.name}: expected "
                    f"{{module}}_{{method}}_{{eval_type}}.json"
                )
            continue
        module, method, eval_type = parsed

        try:
            data = json.loads(json_file.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[aggregate] Skipping {json_file.name}: {exc}")
            continue

        if not isinstance(data, dict):
            continue

        for metric, value in data.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                rows.append({
                    "module": module,
                    "method": method,
                    "metric": f"{metric}_{eval_type}",
                    "value": value,
                })

    if not rows:
        print(f"[aggregate] No valid result files found in {results_dir}")
        return

    df = pd.DataFrame(rows)

    # Wide format: one row per (module, method), columns are metric values
    wide = df.pivot_table(
        index=["module", "method"],
        columns="metric",
        values="value",
        aggfunc="mean",
    )
    ordered = [m for m in KEY_METRICS if m in wide.columns]
    ordered += sorted(c for c in wide.columns if c not in ordered)
    wide = wide[ordered].reset_index()
    wide.columns.name = None
    libraries = load_libraries()
    wide.insert(1, "source", wide["module"].map(lambda m: _module_source(m, libraries)))

    # Overall: mean of each metric per method across all modules
    overall = wide.groupby("method")[ordered].mean().round(4)
    overall.insert(0, "n_modules", wide.groupby("method")["module"].nunique())
    overall = overall.reset_index()

    # Keep a stable method order: single, competitive, collab
    method_rank = {m: i for i, m in enumerate(METHODS)}
    wide = wide.sort_values(
        ["module", "method"], key=lambda s: s.map(method_rank) if s.name == "method" else s
    ).reset_index(drop=True)
    overall = overall.sort_values("method", key=lambda s: s.map(method_rank)).reset_index(drop=True)

    if output_file is None:
        output_file = results_dir / f"summary.{output_format}"
    output_file = Path(output_file)
    overall_file = output_file.with_name(f"{output_file.stem}_overall{output_file.suffix}")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    _write(wide, output_file, output_format)
    _write(overall, overall_file, output_format)

    # Markdown report: headline metrics only, one table per module + overall
    md_cols = ["method"] + [m for m in KEY_METRICS if m in wide.columns]
    md_parts = ["# Results summary", ""]
    for module, group in wide.groupby("module", sort=True):
        md_parts += [
            f"## {module} ({group['source'].iloc[0]})", "", _to_markdown(group[md_cols]), ""
        ]
    md_parts += [
        "## Overall (mean across modules)",
        "",
        _to_markdown(overall[["method", "n_modules"] + md_cols[1:]]),
        "",
    ]
    md_file = output_file.with_suffix(".md")
    md_file.write_text("\n".join(md_parts))

    print(f"[aggregate] Per-module summary saved -> {output_file}")
    print(f"[aggregate] Overall summary saved    -> {overall_file}")
    print(f"[aggregate] Markdown report saved    -> {md_file}")
    for module, group in wide.groupby("module", sort=True):
        print(f"\n=== {module} ({group['source'].iloc[0]}) ===")
        print(group[md_cols].to_string(index=False))
    print(f"\n=== overall (mean across {wide['module'].nunique()} module(s)) ===")
    print(overall[["method", "n_modules"] + md_cols[1:]].to_string(index=False))


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate evaluation results from multiple test generation runs"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(__file__).parent.parent / "results",
        help="Directory containing evaluation result files",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="File to save aggregated per-module results",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        default="csv",
        choices=["csv", "json", "html"],
        help="Format for aggregated output",
    )

    args = parser.parse_args()
    aggregate_results(
        results_dir=args.results_dir,
        output_file=args.output_file,
        output_format=args.output_format,
    )


if __name__ == "__main__":
    main()
