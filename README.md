# pr-risk

`pr-risk` is a Python CLI tool for deterministic PR risk analysis in C++/CMake repositories.

It compares local changes against a base Git reference, collects changed file paths, diff statistics, and selected patch signals from Git, calculates a risk score with fixed rules, and prints a terminal report with the changed files, diff statistics, patch signals, score, level, and reasons.

Current scope:

- Local command-line analysis only.
- Deterministic scoring based on changed file paths and diff churn.
- C++ source/header and CMake file awareness.
- Heuristic C++/CMake patch signal detection.
- Execution-aware risk scoring from configured build/test commands.
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
- v0.5.0 execution-aware scoring: configured build/test results can add risk when `--run-checks` is used.

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

Patch signals affect risk scoring conservatively at the category level. They are heuristics only: `pr-risk` is not a compiler, does not perform full C++ parsing, does not perform ABI analysis, and does not prove breaking changes.

## Execution-Aware Scoring

v0.5.0 adds execution-aware risk scoring for configured local build/test commands.

Execution penalties:

- Build failed: `+30`
- Tests failed: `+25`
- Build timed out: `+20`
- Tests timed out: `+20`
- Timeouts are not double-counted as failures.
- Tests skipped because the build failed or timed out do not receive a test penalty.
- Execution not run, or no commands configured, means no execution penalty.
- The final score remains capped at `100`.

A failing configured command is evidence, not proof that the PR itself is wrong.

Recommendations:

- `do_not_merge_until_build_passes`: build command failed.
- `do_not_merge_until_tests_pass`: test command failed.
- `investigate_execution_timeout`: build or test command timed out.
- `require_senior_review`: risk level is `HIGH`.
- `careful_review`: risk level is `MEDIUM`.
- `normal_review`: risk level is `LOW`.

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
pr-risk analyze --repo . --base main --run-checks
pr-risk --version
```

By default, analysis does not run local commands. Use `--run-checks` to add configured build/test execution evidence.

## Configuration

v0.4.0 introduced configured build/test execution evidence through `.pr-risk.toml`. v0.5.0 uses that execution evidence in risk scoring when `--run-checks` is provided:

```toml
[commands]
build = "cmake --build build"
test = "ctest --test-dir build --output-on-failure"

[execution]
timeout_seconds = 300
```

- `[commands].build` is optional.
- `[commands].test` is optional.
- `[execution].timeout_seconds` is optional and defaults to `300`.
- Commands run only when `--run-checks` is provided.
- Failed or timed-out build/test execution can increase the risk score in v0.5.0.
- stdout/stderr are captured internally but are not printed in text or JSON output.

Security warning: commands are executed locally through the system shell. Only run trusted repository configs.

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
Recommendation:
- Require senior review.
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

With `--run-checks`, text output includes execution evidence:

```text
Recommendation:
- Do not merge until tests pass.
Execution Checks:
- Build: passed (exit code 0, 12.4s)
- Test: failed (exit code 8, 5.1s)
```

If the build fails or times out, the configured test command is skipped and does not add a test penalty.

## JSON Output

```bash
pr-risk analyze --repo . --base main --format json
pr-risk analyze --repo . --base main --format json --run-checks
```

The JSON output contains:

- `score`: integer risk score from `0` to `100`
- `level`: `LOW`, `MEDIUM`, or `HIGH`
- `recommendation`: merge/review recommendation string
- `changed_files`: changed file paths from Git
- `diff_stats`: diff statistics object
- `patch_signals`: heuristic CMake and API-like patch signals
- `reasons`: deterministic reasons contributing to the score
- `execution`: configured build/test execution evidence

Patch signals use this shape:

```json
{
  "patch_signals": {
    "cmake": ["Link dependencies changed"],
    "api": ["API-like header change detected in include/widget.hpp"]
  }
}
```

Without `--run-checks`, commands are not run and JSON includes:

```json
{
  "execution": {
    "run": false
  }
}
```

With `--run-checks`, JSON execution evidence uses this shape:

```json
{
  "execution": {
    "run": true,
    "build": {
      "configured": true,
      "command": "cmake --build build",
      "exit_code": 0,
      "timed_out": false,
      "duration_seconds": 12.4
    },
    "test": {
      "configured": true,
      "command": "ctest --test-dir build --output-on-failure",
      "exit_code": 8,
      "timed_out": false,
      "duration_seconds": 5.1,
      "skipped": false,
      "skip_reason": null
    }
  }
}
```

Example:

```json
{
  "score": 100,
  "level": "HIGH",
  "recommendation": "require_senior_review",
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
  ],
  "execution": {
    "run": false
  }
}
```

## Current Limitations

- Deterministic heuristic analysis only.
- Local CLI only.
- No GitHub integration yet.
- Commands run locally through the system shell.
- Only trusted repository configs should be run.
- No Docker isolation yet.
- No automatic build discovery yet.
- No stdout/stderr artifact storage yet.
- No coverage parsing yet.
- Not a compiler.
- Not full C++ parsing.
- Not ABI analysis.
- Does not prove breaking changes.

## Roadmap

- v0.6.0: Docker sandbox execution.
- v0.7.0: GitHub/GitLab PR integration.
