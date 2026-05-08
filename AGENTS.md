# AGENTS.md

## Project
pr-risk is a Python CLI tool for evidence-backed PR risk analysis in C++/CMake repositories.

## Architecture
Keep code simple and modular:
- cli.py: command-line interface only
- git_diff.py: Git diff/file change detection only
- risk.py: deterministic risk scoring only
- report.py: terminal report output only
- tests/: pytest tests

## Rules
- Do not add AI/LLM code yet.
- Do not add a web app.
- Do not add Docker yet.
- Do not change project structure unless explicitly asked.
- Keep functions small and testable.
- Prefer deterministic logic.
- Add or update tests for every behavior change.

## Commands
Install:
pip install -e .
pip install pytest

Run tests:
pytest

Run CLI:
pr-risk analyze --repo . --base main