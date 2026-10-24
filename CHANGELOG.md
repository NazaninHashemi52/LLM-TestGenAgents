# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased] — v2.1.0 (in development)

Builds on v2.0.0: the agents are also evaluated on real third-party Python
libraries, not only on modules written for this project.

### Added
- Three pinned PyPI libraries as Code Under Test modules: `inflection` 0.5.1
  (string inflection), `roman` 4.2 (Roman numerals) and `toposort` 1.10
  (topological sort).
- `impl/libraries.json` registry. Adding a library is one entry: package,
  version, wheel SHA-256, and the source file to test.
- `scripts/fetch_libraries.py`, which downloads each pinned wheel, checks
  its hash and copies the module into `impl/cut/`. `--check` verifies the
  copies against the registry without downloading.
- `run_all.py --libraries` to run only the third-party libraries.
- `run_all.py --dry-run` and an offline `mock` LLM provider, to check the
  whole pipeline without an LLM. Output goes to `impl/dry_run/`, so real
  results are never overwritten.
- `source` column in `summary.csv` (`built-in`, or `package==version`), and
  library versions in the summary headings.

### Changed
- The evaluation scripts accept a `RESULTS_DIR` environment variable to
  write results somewhere other than `impl/results/`.

## [2.0.0] — in development

Development of v2 started in October 2026. It is maintained independently
by Nazanin Hashemi on top of the v1.0.0 team release.

### Planned
- Five new Code Under Test modules of increasing difficulty: `string_utils`,
  `stack_queue`, `bank_account`, `date_parser`, `inventory`.
- Per-module result files (e.g. `inventory__collab__mutation.json`) so runs
  on different modules no longer overwrite each other.
- Evaluations scoped to each module's own generated test file.
- Two summary tables: per module, and per strategy averaged across modules.
- `scripts/run_all.py` to run the full experiment with one command.
- Unit tests for the framework itself and a GitHub Actions CI pipeline.
- Fresh results for all six modules (the v1.0.0 calculator numbers were
  measured before the last calculator edge-case tests were added).

## [1.0.0] — 2026-06-06

First complete release. Built as a 4-person team project at
Politecnico di Torino between March and June 2026.

### Added
- Project skeleton with the `calculator` Code Under Test module.
- Provider-agnostic LLM abstraction layer: Ollama (local), Groq, Gemini,
  OpenRouter.
- Three test generation strategies:
  - single-agent,
  - competitive multi-agent (adversarial / diversity / coverage modes),
  - collaborative multi-agent with role assignment.
- AST validation of generated code with up to 3 retries, and a merge
  pipeline that deduplicates imports and renames conflicting tests.
- Evaluation scripts for coverage (`coverage.py`), mutation score
  (`mutmut`), and AST-based test diversity.
- Result aggregation into a CSV / JSON / HTML summary, with example results
  for the `calculator` module.
- Extra edge-case tests for the calculator (zero exponent, competitive
  suite).
- MIT License.

[Unreleased]: https://github.com/NazaninHashemi52/LLM-TestGenAgents/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/NazaninHashemi52/LLM-TestGenAgents/releases/tag/v1.0.0
