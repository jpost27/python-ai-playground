# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Python AI Playground — a modular learning project for agentic AI. Each module under `modules/` is a standalone CLI script run via `uv run python -m modules.<name>.main`. See `README.md` for the full list and extras.

### Running modules

- **Lint:** `uv run ruff check .`
- **Tests:** `uv run pytest` (no test files exist yet; pytest is a dev dependency)
- **Run a module:** `uv run python -m modules.<name>.main` (e.g. `modules.langraph.main`)

### Non-obvious caveats

- The `langraph` module is the only one with real implementation; the others (`rag`, `agent`, `code_search`, `code_gen`) are placeholders that print a message and exit.
- Without `ANTHROPIC_API_KEY`, the langraph module runs in **demo mode** using a heuristic classifier. To force demo mode even when the env var exists, unset it: `ANTHROPIC_API_KEY= uv run python -m modules.langraph.main`.
- There is a pre-existing bug in `modules/langraph/main.py`: the `answer_question` function references `_get_llm()` which is undefined. This only triggers when `ANTHROPIC_API_KEY` is set and the classify step routes to "question". Demo mode (no API key) works fine.
- Ruff reports 11 pre-existing lint issues (10× E501 line-too-long, 1× F821 undefined name). These are in the existing code — do not treat them as regressions.
- `uv` must be on `PATH`. It installs to `~/.local/bin` — the update script ensures this.
