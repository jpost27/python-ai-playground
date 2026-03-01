# Python AI Playground

Learning project for **agentic AI** with Python: LangGraph, prompt engineering, vector databases, RAG, tool calling, code search, and code generation.

## Environment (uv + Python 3.12)

This project uses [uv](https://docs.astral.sh/uv/) for fast virtualenv creation and dependency management (similar in spirit to having a single `pom.xml` and running from one repo).

1. **Install uv** (one-time):

   - **macOS / Linux:**  
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```  
     Or on macOS with Homebrew: `brew install uv`

   - **Windows (PowerShell):**  
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```  
     Or with WinGet: `winget install --id=astral-sh.uv -e`  
     Or with [Scoop](https://scoop.sh): `scoop install main/uv`

2. **Create venv and install base deps** (from repo root).  
   Use **PowerShell** or **Terminal** (macOS/Linux); the same commands work on both:

   ```bash
   cd python-ai-playground
   uv sync
   ```

   This reads `.python-version` (3.12), creates `.venv`, and installs base dependencies (anthropic, langchain-core, langgraph, python-dotenv).

3. **Install extras only when you need them** (so you can prototype one module at a time):

   ```bash
   uv sync --extra rag          # Weeks 1–2: RAG + Chroma
   uv sync --extra agent        # Weeks 3–4: multi-agent / tool calling
   uv sync --extra code-search  # Weeks 5–6: GitHub API, code embeddings
   uv sync --extra code-gen     # Weeks 7–8: code gen, ruff, validation
   uv sync --extra all          # everything
   ```

   The **langraph** module uses only base dependencies — no extra needed; `uv sync` is enough.

## Running a module

Each module can be run on its own (use the module name, not the file path — no `.py`):

```bash
uv run python -m modules.rag.main
uv run python -m modules.langraph.main
uv run python -m modules.agent.main
uv run python -m modules.code_search.main
uv run python -m modules.code_gen.main
```

`uv run` uses the project’s virtualenv and dependencies automatically.

## Example project (Snippet Stash)

A minimal CLI app lives in `example_project/` for use with the LangGraph ticket demo. It has no extra dependencies.

```bash
uv run python -m example_project.main add "My note" "Some text"
uv run python -m example_project.main list
uv run python -m example_project.main get 1
uv run python -m example_project.main delete 1
```

See `example_project/README.md` for a quick reference and **`example_project/docs/USER_DOCS.md`** for full user documentation (what it is, how to use it, limitations, examples, and common questions).

## API keys

Create a `.env` in the project root (do not commit it). For example:

```env
ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-sonnet-4-6   # optional, override if you get model errors
# GITHUB_TOKEN=...   # when you add code_search / code_gen
```

**Format:** `ANTHROPIC_API_KEY=sk-ant-...` — no spaces around `=`, no quotes. The `.env` file must be in the project root (same folder as `pyproject.toml`).

If you see "LLM call failed" but "ANTHROPIC_API_KEY loaded", the key is set correctly; the failure is usually model access. Try adding `ANTHROPIC_MODEL=claude-3-haiku-20240307` to `.env` (or another model from your [Anthropic console](https://console.anthropic.com/)).

Load in code with `python-dotenv` (already a base dependency):

```python
from dotenv import load_dotenv
load_dotenv()
import os
api_key = os.environ["ANTHROPIC_API_KEY"]
```

## Project layout

```
python-ai-playground/
├── .python-version          # 3.12
├── pyproject.toml           # deps + optional groups (rag, agent, code-search, code-gen)
├── README.md
├── .env                     # your keys (gitignored)
├── .env.example             # template
├── example_project/        # minimal CLI (Snippet Stash) for LangGraph demos
│   ├── main.py
│   ├── store.py
│   └── README.md
└── modules/
    ├── rag/                 # Weeks 1–2: RAG, vector DB, “answer from docs”
    │   └── main.py
    ├── langraph/            # LangGraph playground (graphs, nodes, state, cycles)
    │   └── main.py
    ├── agent/               # Weeks 3–4: multi-agent, tool calling, “classify → search → respond”
    │   └── main.py
    ├── code_search/         # Weeks 5–6: code embeddings, GitHub API, search repos
    │   └── main.py
    └── code_gen/            # Weeks 7–8: code gen, validation, “detect bug → fix PR”
        └── main.py
```

## Learning plan (reference)

| Weeks   | Focus | Extras / modules |
|--------|--------|-------------------|
| **1–2**  | LangGraph course, Prompt Engineering, Vector DBs; build “answer from docs” RAG | `rag` |
| **3–4**  | LangGraph multi-agent, tool calling with Claude; “classify ticket → search docs → respond” | `agent` |
| **5–6**  | Code embeddings, GitHub API, extend agent to search code repos | `code-search` |
| **7–8**  | Code generation with Claude, validation (AST, lint), “detect bug → generate fix PR” | `code-gen` |

Start with `uv sync` and `uv run python -m modules.rag.main` when you begin the RAG module; add `--extra rag` when you’re ready to use Chroma and LangChain for that module.
