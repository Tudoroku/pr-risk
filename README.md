# pr-risk

`pr-risk` is a Python CLI tool for deterministic PR risk analysis in C++/CMake repositories.

It compares local changes against a base Git reference, collects changed file paths from Git, calculates a risk score with fixed rules, and prints a terminal report with the changed files, score, level, and reasons.

Current scope:

- Local command-line analysis only.
- Deterministic scoring based on changed file paths.
- C++ source/header and CMake file awareness.
- Test-file detection for common test naming patterns.

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
```

## Example Output

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
Risk score: 80/100
Risk level: HIGH
Reasons:
- Build system files changed
- Header/API files changed
- Source implementation files changed
- No test files changed
```

## Current Limitations

- Deterministic analysis only.
- Local CLI only.
- No AI/LLM analysis yet.
- No GitHub integration yet.
