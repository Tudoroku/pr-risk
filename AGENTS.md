# AGENTS.md

## Project

`pr-risk` is a Python CLI tool for evidence-backed PR risk analysis in C++/CMake repositories.

The product is intentionally deterministic first:

- no AI/LLM analysis yet
- no web app yet
- no GitHub integration yet
- no database
- no Docker sandboxing yet

Current release line:

- `v0.1.0` = file-path risk classification
- `v0.2.0` = diff-size/churn-aware analysis + JSON output
- `v0.3.0` = heuristic C++/CMake patch signals
- `v0.4.0` = configured build/test execution evidence

## Architecture

Keep code simple and modular:

- `cli.py`: CLI entrypoint, orchestration, and output format selection
- `git_diff.py`: Git diff/file change extraction only
- `diff_stats.py`: Git numstat parsing and diff statistics only
- `patch.py`: file-aware patch-line extraction only
- `cmake_analysis.py`: heuristic CMake patch signal detection only
- `api_change.py`: heuristic API-like header patch signal detection only
- `risk.py`: deterministic risk scoring only
- `runner.py`: local command execution and execution-check orchestration only
- `config.py`: `.pr-risk.toml` config loading only
- `report.py`: terminal/text report output only
- `tests/`: pytest tests

Important boundary:

- Do not move JSON rendering into `report.py`.
- `report.py` must stay text-only.
- Do not make `runner.py` responsible for CLI, JSON formatting, text formatting, config parsing, or risk scoring.

## Rules

- Do not add AI/LLM code yet.
- Do not add a web app.
- Do not add Docker yet.
- Do not add GitHub integration yet.
- Do not add a database.
- Do not add full C++ parsing, tree-sitter, or clang tooling yet.
- Do not add coverage parsing yet.
- Do not change project structure unless explicitly asked.
- Keep functions small and testable.
- Prefer deterministic logic.
- Add or update tests for every behavior change.
- Do not rewrite unrelated files.
- Do not change risk scoring unless explicitly asked.

## Execution Safety

`pr-risk` can run configured local commands through `.pr-risk.toml`.

Important:

- Commands are executed locally through the system shell.
- Only run trusted repository configs.
- Execution is not sandboxed.
- Docker/isolation is future work.
- Do not call current execution support “sandboxed execution.”

In `v0.4.0`, execution results are evidence only. Build/test failures are reported but do not affect risk score yet.

## Commands

Install:

```bash
pip install -e .
pip install pytest
```

Run tests:

```bash
python -m pytest
```

Run CLI text output:

```bash
pr-risk analyze --repo . --base main
```

Run CLI JSON output:

```bash
pr-risk analyze --repo . --base main --format json
```

Run configured execution checks:

```bash
pr-risk analyze --repo . --base main --run-checks
```

Run configured execution checks with JSON:

```bash
pr-risk analyze --repo . --base main --run-checks --format json
```

## Development Workflow

Before starting a milestone:

```bash
git status --short
python -m pytest
pr-risk analyze --repo . --base main
pr-risk analyze --repo . --base main --format json
```

After changes:

```bash
git --no-pager diff --stat
git --no-pager diff
python -m pytest
```

Use small focused commits. Do not commit unrelated changes.
