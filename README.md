# pr-risk

`pr-risk` is a Python CLI tool for deterministic PR risk analysis in C++/CMake repositories.

It compares local changes against a base Git reference, collects changed file paths, diff statistics, and selected patch signals from Git, calculates a risk score with fixed rules, and prints a terminal report with the changed files, diff statistics, patch signals, score, level, and reasons.

Current scope:

- Local command-line analysis only.
- Deterministic scoring based on changed file paths and diff churn.
- C++ source/header and CMake file awareness.
- Heuristic C++/CMake patch signal detection.
- Test-file detection for common test naming patterns.
- Text and JSON output.

## Current Risk Signals

Risk scoring is deterministic and based on changed file paths, diff statistics, and heuristic patch signals:

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

## Patch Signals

v0.3.0 adds heuristic C++/CMake patch signals. Patch extraction uses Git unified diff.

CMake patch signal detection covers added or removed patch lines containing:

- `add_library`
- `add_executable`
- `target_link_libraries`
- `target_include_directories`
- `target_compile_options`
- `target_compile_definitions`
- `find_package`

Header/API-like patch detection covers:

- class declarations
- struct declarations
- enum declarations
- simple function declarations
- trailing return type declarations

Patch signals affect risk scoring conservatively at the category level. They are heuristics only: `pr-risk` is not a compiler, does not perform full C++ parsing, does not perform ABI analysis, does not build or run tests yet, and does not prove breaking changes.

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
Patch Signals:
CMake:
- Link dependencies changed
Header/API:
- API-like header change detected in include/widget.hpp
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
- `patch_signals`: heuristic CMake and API-like patch signals
- `reasons`: deterministic reasons contributing to the score

Patch signals use this shape:

```json
{
  "patch_signals": {
    "cmake": ["Link dependencies changed"],
    "api": ["API-like header change detected in include/widget.hpp"]
  }
}
```

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
  "patch_signals": {
    "cmake": ["Link dependencies changed"],
    "api": ["API-like header change detected in include/widget.hpp"]
  },
  "reasons": [
    "Build system files changed",
    "Header/API files changed",
    "Source implementation files changed",
    "Production code changed",
    "Public API directory changed",
    "Large diff: 145 changed lines",
    "CMake patch signals detected",
    "Build/link/package configuration changed",
    "API-like header changes detected",
    "No test files changed"
  ]
}
```

## Current Limitations

- Deterministic heuristic analysis only.
- Local CLI only.
- No GitHub integration yet.
- No build/test execution yet.
- Not a compiler.
- Not full C++ parsing.
- Not ABI analysis.
- Does not prove breaking changes.

## Roadmap

- v0.4.0: sandboxed build/test execution.
