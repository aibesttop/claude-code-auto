# Repository Guidelines

## Project Structure & Module Organization
- `src/` houses the Python application code. Core orchestration lives in `src/core/` (agents, leader, team, tools), shared helpers in `src/utils/`, and web assets/templates in `src/web/`.
- `roles/`, `schemas/`, and `resources/` contain YAML definitions, schemas, and prompt resources used by the agent system.
- `docs/` stores design notes and change summaries; `scripts/` contains helper scripts.
- `config.yaml` defines runtime configuration; `demo_act/`, `logs/`, and `test_output/` are generated outputs.
- `tests/` is reserved for automated tests (currently minimal).

## Build, Test, and Development Commands
- Install dependencies: `python -m venv venv`, then `venv\Scripts\activate`, and `pip install -r requirements.txt`.
- Run locally with defaults: `python -m src.main`.
- Windows shortcut: `run_agent.bat` (also sets `TAVILY_API_KEY`).
- Diagnostics: `python diagnose_mission_decomposition.py` or `python diagnose_validation.py`.

## Coding Style & Naming Conventions
- Python 3.12+ with 4-space indentation; keep functions small and descriptive.
- Naming: `snake_case` for modules/functions, `CamelCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep new modules under the existing namespaces (`src/core/...`, `src/utils/...`) rather than creating top-level packages.
- No enforced formatter or linter; match the existing style in `src/`.

## Testing Guidelines
- Preferred framework is `pytest`; tests live in `tests/` and should be named `test_*.py`.
- Run the suite with `pytest tests/` when pytest is available.
- There is no current coverage gate; add focused tests for new features or bug fixes.

## Commit & Pull Request Guidelines
- Commit history favors short, descriptive summaries (English or Chinese). Follow that pattern and keep messages single-line.
- PRs should include: a concise summary, configuration or API changes, and any required run instructions. Link related issues if available.

## Configuration & Secrets
- Use `.env` or environment variables for `ANTHROPIC_API_KEY` and `TAVILY_API_KEY`.
- Do not commit real credentials; document required keys in PR descriptions when needed.
