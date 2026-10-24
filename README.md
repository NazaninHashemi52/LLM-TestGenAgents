# LLM Agents for Collaborative Test Case Generation

> Started as a 4-person team project at Politecnico di Torino. This repository is maintained and extended independently by Nazanin Hashemi.

A research framework for comparing three LLM-based test case generation strategies — single-agent, competitive multi-agent, and collaborative multi-agent — evaluated against code coverage, mutation testing, and test diversity metrics.

---

## Versions

| Version | Status | Date | Summary |
|---|---|---|---|
| [v1.0.0](https://github.com/NazaninHashemi52/LLM-TestGenAgents/releases/tag/v1.0.0) | Released | June 2026 | Team project release: three strategies, four LLM providers, `calculator` module |
| v2.0.0 | In development | Since October 2026 | Multi-module evaluation, CI, and unit tests for the framework |
| v2.1.0 | In development | October 2026 | Real third-party libraries (`inflection`, `roman`, `toposort`) as evaluation targets, offline dry run |

The documentation below describes the latest development version (v2.1.0). See [CHANGELOG.md](CHANGELOG.md) for details.

---

## Project Description

This project investigates how different multi-agent architectures affect the quality of automatically generated pytest test suites. A pluggable LLM abstraction layer routes requests to one of four supported providers (Ollama, Groq, Gemini, OpenRouter), making the framework model-agnostic.

Generated test suites are evaluated across three axes:

| Metric | Tool | Description |
|---|---|---|
| Coverage | `coverage.py` | Line, branch, and function coverage |
| Mutation score | `mutmut` | Ratio of killed mutations to total mutations |
| Diversity | Custom AST analysis | Structural and semantic variety among tests |

---

## Main Features

- **Three test generation strategies:**
  - **Single-agent** — one LLM call generates all tests
  - **Competitive** — agents see prior tests and compete (adversarial / diversity / coverage modes)
  - **Collaborative** — agents are assigned specialized roles (edge-case, boundary, error testing)
- **LLM abstraction layer** supporting Ollama (local), Groq, Gemini, and OpenRouter
- **AST-based code validation and retry logic** — generated code is parsed and retried up to 3 times
- **Multi-agent merge pipeline** — deduplicates imports and renames conflicting test functions
- **Three evaluation scripts** producing structured JSON output
- **Six CUT modules** of increasing difficulty, from simple string functions to collaborating classes
- **Three real third-party libraries** as extra targets (`inflection`, `roman`, `toposort`), pinned in `libraries.json`; adding another is one JSON entry
- **Aggregation script** that builds one comparison table per module plus an overall average (CSV/JSON/HTML + Markdown)
- **`run_all.py`** to run every strategy and evaluation on every module in one command, with an offline `--dry-run`

---

## Project Structure

```
.
├── README.md
└── impl/
    ├── pyproject.toml              # Project metadata and dependencies
    ├── libraries.json              # Third-party libraries used as CUT modules (pinned)
    ├── cut/                        # Code Under Test (CUT) modules
    │   ├── __init__.py
    │   ├── calculator.py           # Stateless functions + Calculator class
    │   ├── string_utils.py         # Simple string functions (baseline)
    │   ├── stack_queue.py          # Stateful data structures (Stack, circular-buffer Queue)
    │   ├── bank_account.py         # Class with custom exceptions, limits and edge cases
    │   ├── date_parser.py          # Date parsing/arithmetic with many boundary cases
    │   ├── inventory.py            # Several collaborating classes (hardest)
    │   ├── inflection.py           # vendored: inflection 0.5.1 (MIT) — string inflection
    │   ├── roman.py                # vendored: roman 4.2 (ZPL-2.1) — Roman numerals
    │   └── toposort.py             # vendored: toposort 1.10 (Apache-2.0) — topological sort
    ├── src/                        # Core utilities
    │   ├── __init__.py
    │   └── llm.py                  # LLM abstraction layer (Ollama, Groq, Gemini, OpenRouter, mock)
    ├── scripts/                    # Generation and evaluation scripts
    │   ├── fetch_libraries.py      # Vendor the libraries in libraries.json into cut/
    │   ├── generate_single.py      # Single-agent test generation
    │   ├── generate_competitive.py # Competitive multi-agent generation
    │   ├── generate_collab.py      # Collaborative multi-agent generation
    │   ├── run_pytest.py           # Run pytest with correct PYTHONPATH
    │   ├── eval_coverage.py        # Coverage evaluation (coverage.py)
    │   ├── eval_mutation.py        # Mutation evaluation (mutmut)
    │   ├── eval_diversity.py       # Diversity evaluation (AST-based)
    │   ├── aggregate.py            # Aggregate results: per-module tables + overall average
    │   └── run_all.py              # Run every strategy + evaluation on every module
    ├── tests_generated/            # Output from generation scripts
    │   ├── single/                 # one test_<module>.py per CUT module
    │   ├── competitive/
    │   └── collab/
    └── results/                    # Evaluation outputs (JSON + CSV + Markdown)
        ├── <module>_<method>_<metric>.json   # e.g. bank_account_collab_mutation.json
        ├── summary.csv             # one row per (module, method)
        ├── summary_overall.csv     # per-method mean across all modules
        └── summary.md              # Markdown tables, one per module + overall
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Test framework | pytest |
| Coverage | coverage.py |
| Mutation testing | mutmut 3.x |
| Data aggregation | pandas |
| LLM communication | requests (raw HTTP, no AI SDK required) |
| Supported LLM providers | Ollama (local), Groq, Gemini, OpenRouter |

---

## Requirements

```
pytest>=7.0.0
coverage>=7.0.0
mutmut>=2.4.0
pandas>=1.5.0
requests>=2.28.0
```

For local inference, [Ollama](https://ollama.com) must be installed and running with a supported model (default: `qwen2.5-coder:7b`).

For cloud providers, the corresponding API key is required (see Configuration).

---

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd LLM-Agents-for-Collaborative-Test-Case-Generations

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install the project and its dependencies
cd impl
pip install -e .
```

---

## Configuration

The LLM provider and credentials are configured via environment variables.

### Select a provider

```bash
export LLM_PROVIDER=ollama        # default — local Ollama server
export LLM_PROVIDER=groq
export LLM_PROVIDER=gemini
export LLM_PROVIDER=openrouter
export LLM_PROVIDER=mock          # offline stub used by run_all.py --dry-run
```

### Provider-specific variables

**Ollama (default)**
```bash
export OLLAMA_MODEL=qwen2.5-coder:7b          # default
export OLLAMA_API_URL=http://localhost:11434/api/generate   # default
```

**Groq**
```bash
export GROQ_API_KEY=<your-groq-api-key>
export GROQ_MODEL=llama-3.3-70b-versatile     # default
```

**Gemini**
```bash
export GEMINI_API_KEY=<your-gemini-api-key>
export GEMINI_MODEL=gemini-2.0-flash          # default
```

**OpenRouter**
```bash
export OPENROUTER_API_KEY=<your-openrouter-api-key>
export OPENROUTER_MODEL=qwen/qwen3-8b:free    # default
```

---

## How to Run

All commands are run from the `impl/` directory.

### Quick start: run everything

`run_all.py` runs every generation strategy and every evaluation on every module in
`cut/`, then aggregates the results:

```bash
python scripts/run_all.py                                   # all modules, all strategies
python scripts/run_all.py --modules bank_account inventory  # only some modules
python scripts/run_all.py --skip-generate                   # re-evaluate existing tests (no LLM calls)
python scripts/run_all.py --evaluations coverage diversity  # skip slow mutation testing
python scripts/run_all.py --libraries                       # only the third-party libraries
python scripts/run_all.py --libraries --dry-run             # offline pipeline check, no LLM
```

`--dry-run` swaps in a mock LLM (`LLM_PROVIDER=mock`) that returns one trivial test per
module, and writes tests and results under `impl/dry_run/` (git-ignored), so real
results are never overwritten. Use it to check that a new module or library goes
through generation, evaluation and aggregation; its scores mean nothing.

A failing step (for example, the LLM returning invalid code) is reported at the end
but does not stop the remaining runs.

The steps below run each stage by hand for a single module.

### 1. Generate tests

**Single-agent**
```bash
python scripts/generate_single.py --cut-module calculator --num-tests 10
```

**Competitive multi-agent**
```bash
python scripts/generate_competitive.py \
  --cut-module calculator \
  --num-agents 2 \
  --competition-mode adversarial   # or: diversity | coverage
```

**Collaborative multi-agent**
```bash
python scripts/generate_collab.py \
  --cut-module calculator \
  --num-agents 3
  # optional: --prompt-roles roles.json  (custom role definitions)
```

Generated test files are saved to `tests_generated/{single,competitive,collab}/test_<module>.py`.

### 2. Run the generated tests

```bash
python scripts/run_pytest.py --test-dir tests_generated/single -v
```

### 3. Evaluate

**Coverage**
```bash
python scripts/eval_coverage.py \
  --test-dir tests_generated/single \
  --cut-module calculator
```

**Mutation score**
```bash
python scripts/eval_mutation.py \
  --test-dir tests_generated/single \
  --cut-module calculator
```

**Diversity**
```bash
python scripts/eval_diversity.py \
  --test-dir tests_generated/single \
  --cut-module calculator \
  --diversity-metric syntactic   # or: semantic | coverage
```

Each script evaluates only `test_<module>.py` inside the test directory and writes
`results/<module>_<method>_<metric>.json` (e.g. `calculator_single_coverage.json`),
so results for different modules never overwrite each other.

### 4. Aggregate results

```bash
python scripts/aggregate.py \
  --results-dir results \
  --output-format csv     # or: json | html
```

Outputs:
- `results/summary.csv` — one row per (module, method), one column per metric, plus a `source` column (`built-in`, or `package==version` for a third-party library)
- `results/summary_overall.csv` — per-method mean of every metric across all modules
- `results/summary.md` — Markdown tables (one per module plus the overall average), ready to paste into this README

---

## Example Results

Results from running all three strategies on the `calculator` CUT module.
Results for the five new modules (`string_utils`, `stack_queue`, `bank_account`,
`date_parser`, `inventory`) and the three libraries (`inflection`, `roman`, `toposort`)
will be added after running `python scripts/run_all.py`;
`results/summary.md` then contains one table per module plus the overall average.

| Method | Line Coverage | Branch Coverage | Mutation Score | Diversity Score |
|---|---|---|---|---|
| single | 0.624 | 0.333 | **0.405** | **0.325** |
| competitive | 0.706 | 0.500 | 0.310 | 0.248 |
| collab | 0.706 | **0.583** | 0.071 | 0.169 |

Key observations:
- Single-agent produces the most diverse tests and highest mutation score, but the lowest coverage.
- Collaborative agents achieve the best branch coverage but lowest mutation score — role specialization increases coverage at the cost of test strength.
- Competitive agents offer a middle ground across all metrics.

---

## Current Limitations

- **No LLM response caching** — every run makes fresh API calls; repeated evaluation is slow and may incur API costs.
- **One test file per module per strategy** — each run overwrites `tests_generated/<strategy>/test_<module>.py`; repeated runs (for variance) are not kept.
- **Function coverage is approximate** — estimated from executed line numbers in the AST, not actual function entry tracking.
- **Retry logic is provider-specific** — rate-limit retries are implemented only for OpenRouter; other providers do not retry on transient failures.
- **CalculatorError is defined but unused** — the custom exception class in `calculator.py` is dead code in the current version.
- **No cross-strategy deduplication** — the single, competitive, and collab test suites may contain overlapping test logic.
- **Mutation testing is slow** — `mutmut` runs can take several minutes on larger CUT modules.
- **conftest.py workaround** — `eval_mutation.py` writes a temporary `conftest.py` to isolate test subdirectories; this is a known workaround for a pytest path resolution issue.

---

## Development Notes

### Adding a new LLM provider

Edit `impl/src/llm.py`:
1. Add a new `_call_<provider>()` function following the pattern of existing providers.
2. Register the new provider name in the `call_local_llm()` dispatcher.
3. Document the required environment variables.

### Adding a new CUT module

1. Place the module in `impl/cut/`, e.g. `impl/cut/my_module.py`.
2. Run `python scripts/run_all.py --modules my_module` (or pass `--cut-module my_module`
   to the individual scripts). `run_all.py` picks up every non-underscore file in `cut/` automatically.

### Adding a third-party library

Good targets are small, pure-Python libraries whose code lives in one self-contained
file (standard-library imports only, no relative imports), so it can be copied into
`cut/` and imported as `impl.cut.<name>`.

1. Add an entry to `impl/libraries.json`. The key becomes the CUT module name:
   ```json
   "pytimeparse": {
     "package": "pytimeparse",
     "version": "1.1.8",
     "sha256": "<sha256 of the .whl file>",
     "source_file": "pytimeparse/timeparse.py",
     "license": "MIT",
     "description": "Parse '1h 30m' style durations"
   }
   ```
   `source_file` is the file's path inside the wheel. To get the hash and the paths, run
   `pip download --no-deps --only-binary :all: pytimeparse==1.1.8`, then
   `sha256sum *.whl` and `unzip -l *.whl`.
2. Run `python scripts/fetch_libraries.py pytimeparse`. It downloads the pinned wheel,
   checks the hash, and writes `cut/pytimeparse.py` with a "vendored from" header.
   `python scripts/fetch_libraries.py --check` checks every vendored file against the
   registry.
3. Run `python scripts/run_all.py --modules pytimeparse --dry-run` to check the pipeline,
   then run it without `--dry-run`. In the summary tables the library shows as
   `pytimeparse (pytimeparse==1.1.8)`, and the `source` column of `summary.csv` holds
   the pinned version (built-in modules show `built-in`).

### Adding a new evaluation metric

1. Create `impl/scripts/eval_<metric>.py` following the structure of existing eval scripts.
2. Output results as `results/<module>_<method>_<metric>.json` with a flat numeric dict,
   and add `<metric>` to `EVAL_TYPES` in `aggregate.py` and `EVALUATIONS` in `run_all.py`.
3. The `aggregate.py` script will automatically pick up the new JSON files on the next run.

### Custom collaboration roles

Pass a JSON file to `generate_collab.py` with `--prompt-roles`:

```json
[
  {"name": "security_tester", "description": "Focus on injection, overflow, and unsafe input handling"},
  {"name": "performance_tester", "description": "Focus on large inputs, timing, and resource usage"}
]
```

---

## License

Released under the [MIT License](LICENSE).
