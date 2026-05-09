# pr-risk

`pr-risk` is a Python CLI tool for deterministic PR risk analysis in C++/CMake repositories.

It compares local changes against a base Git reference, collects changed file paths and diff statistics from Git, calculates a risk score with fixed rules, and prints a terminal report with the changed files, diff statistics, score, level, and reasons.

Current scope:

- Local command-line analysis only.
- Deterministic scoring based on changed file paths and diff churn.
- C++ source/header and CMake file awareness.
- Test-file detection for common test naming patterns.
- Text and JSON output.

## Current Risk Signals

Risk scoring is deterministic and based on changed file paths plus diff statistics:

- CMake/build files: `CMakeLists.txt` and `*.cmake` add build-system risk.
- C++ header/API files: `.h`, `.hh`, `.hpp`, and `.hxx` add API risk.
- C/C++ source files: `.c`, `.cc`, `.cpp`, and `.cxx` add implementation risk, capped across changed source files.
- Directory-aware signals: top-level `src/` and `lib/` indicate production code, `include/` indicates public API, `cmake/` indicates build configuration, and `third_party/` or `vendor/` indicate vendored dependencies.
- Test-file detection: paths under `tests/`, filenames starting with `test_`, and common `_test` suffixes count as test changes.
- Docs-only changes: files under `docs/`, README files, `.md`, and `.markdown` changes stay low risk and do not trigger the missing-tests signal.
- Churn-aware scoring: large total line churn increases risk at fixed thresholds.
- File-count scoring: broad changes across many files increase risk at fixed thresholds.

Diff statistics are parsed from Git numstat output and include:

- files changed
- lines added
- lines deleted
- total churn
- binary files changed

## Architecture

- `cli.py`: command-line argument parsing and command dispatch.
- `git_diff.py`: Git diff and changed-file detection.
- `risk.py`: deterministic risk scoring.
- `report.py`: terminal report output.

## Installation

```bash
pip install -e .
pip install pytest
```

## Running Tests

```bash
python -m pytest
```

## Running the CLI

```bash
pr-risk analyze --repo . --base main
pr-risk analyze --repo . --base main --format json
pr-risk --version
```

## Text Output

```text
PR Risk Report

Changed Files
+---+--------------------+
| # | File               |
+---+--------------------+
| 1 | CMakeLists.txt     |
| 2 | include/widget.hpp |
| 3 | src/widget.cpp     |
+---+--------------------+
  Diff Stats   
+----------------------+-------+
| Metric               | Value |
+----------------------+-------+
| Files changed        |     3 |
| Lines added          |   120 |
| Lines deleted        |    25 |
| Total churn          |   145 |
| Binary files changed |     0 |
+----------------------+-------+
Risk score: 100/100
Risk level: HIGH
Reasons:
- Build system files changed
- Header/API files changed
- Source implementation files changed
- Production code changed
- Public API directory changed
- Large diff: 145 changed lines
- No test files changed
```

## JSON Output

```bash
pr-risk analyze --repo . --base main --format json
```

The JSON output contains:

- `score`: integer risk score from `0` to `100`
- `level`: `LOW`, `MEDIUM`, or `HIGH`
- `changed_files`: changed file paths from Git
- `diff_stats`: diff statistics object
- `reasons`: deterministic reasons contributing to the score

Example:

```json
{
  "score": 100,
  "level": "HIGH",
  "changed_files": ["CMakeLists.txt", "include/widget.hpp", "src/widget.cpp"],
  "diff_stats": {
    "files_changed": 3,
    "lines_added": 120,
    "lines_deleted": 25,
    "total_churn": 145,
    "binary_files_changed": 0
  },
  "reasons": [
    "Build system files changed",
    "Header/API files changed",
    "Source implementation files changed",
    "Production code changed",
    "Public API directory changed",
    "Large diff: 145 changed lines",
    "No test files changed"
  ]
}
```

## Current Limitations

- Deterministic heuristic analysis only.
- Local CLI only.
- No AI/LLM analysis yet.
- No GitHub integration yet.
- No build/test execution yet.
- No semantic C++/CMake patch analysis yet.

## Roadmap

- v0.3.0: semantic C++/CMake diff signals.
