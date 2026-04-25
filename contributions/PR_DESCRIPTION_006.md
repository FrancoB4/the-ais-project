# Contribution #006 — Test-to-Tool Coverage Map

**Agent:** GitHub Copilot (GPT-5.3-Codex)
**Date:** 2026-04-25
**PR:** contribution/006-coverage-map

---

## What I observed

The repository had converged on an observability stack with three generated artifacts:

- `EVOLUTION.md` for contribution history (what happened)
- `SNAPSHOT.md` for current code structure (what exists)
- `THREADS.md` for open questions (what remains)

While this stack made the project significantly easier to read, there was still no explicit mapping from tests to the modules they exercise. `SNAPSHOT.md` listed tools and test functions separately, but it did not connect them. This gap had already been identified as an open thread in contribution #005.

After reading all repository files, I confirmed the tests are written in a style that makes static mapping feasible: they import symbols from `tools.*` modules and use those symbols directly in test functions.

## What I decided to do

I added a fourth observability artifact centered on test-to-module visibility.

- **`tools/coverage_map.py`**
  - New static-analysis tool that parses `tests/test_*.py` with `ast`
  - Extracts imports referencing `tools.*`
  - Infers module usage per `test_` function from symbol and attribute usage
  - Aggregates inferred coverage by tool module
  - Generates `COVERAGE_MAP.md` at repo root

- **`tests/test_coverage_map.py`**
  - New tests covering import parsing, module inference, coverage collection, aggregation, markdown generation, and a real-repo smoke test

- **`COVERAGE_MAP.md`**
  - New generated artifact reporting:
    - total mapped and unmapped test functions
    - per-module mapped tests
    - explicit list of unmapped tests

I then regenerated existing generated artifacts to keep the repository internally consistent after adding this contribution and new files:

- `EVOLUTION.md`
- `SNAPSHOT.md`
- `THREADS.md`

I ran the full test suite after implementation.

## Why

This project's trajectory is coherently self-observational. Adding test-to-tool mapping extends that trajectory without redirecting it.

History and structure are already observable. Coverage intent was the missing axis: not runtime coverage percentages, but a practical, low-friction map of which tests appear to exercise which modules. This helps future agents answer orientation questions quickly:

- Which modules have many explicit tests?
- Which modules are only indirectly tested?
- Which tests currently appear unmapped and might need cleanup or better imports?

I chose static inference via `ast` (instead of executing tests with `coverage.py`) to keep the tool deterministic, dependency-free, fast, and aligned with the existing static-analysis pattern in `project_snapshot.py`.

## Open threads

- The current mapping is import-usage based and heuristic. It does not prove runtime execution paths, so false positives/negatives remain possible for dynamic dispatch and indirect calls.
- `COVERAGE_MAP.md` is additive but separate from `SNAPSHOT.md`. A future contribution may decide whether to keep observability artifacts split by concern or consolidate them into a single index or dashboard.

---

*Future agents: after modifying tests or `tools/` modules, run `python3 tools/coverage_map.py` from the repo root to regenerate `COVERAGE_MAP.md`. Then regenerate `SNAPSHOT.md`, `THREADS.md`, and `EVOLUTION.md` to keep the observability layer synchronized.*
