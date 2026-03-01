# Snippet Stash

A minimal CLI to save and recall text snippets. Data is stored in `.snippets.json` in the directory where you run the commands.

## Commands

- **add** — Add a new snippet with a title and body.
- **list** — List all snippets (newest first). Shows id, title, and a short preview.
- **get** — Show the full content of one snippet by id.
- **delete** — Remove a snippet by id.

## How to run

From the repo root:

```bash
uv run python -m example_project.main add "My note" "Some text to remember"
uv run python -m example_project.main list
uv run python -m example_project.main get 1
uv run python -m example_project.main delete 1
```

## Limits

- Snippets are stored in a single JSON file (`.snippets.json`) in the current working directory. There is no limit on how many snippets you can store; very large files may be slow.
- Title and body are plain text; no formatting or tags.

## Full documentation

For detailed user documentation (how to use each command, where data is stored, limitations, examples, and common questions), see **[docs/USER_DOCS.md](docs/USER_DOCS.md)**. That document is the reference for answering questions or clearing up confusion about Snippet Stash.

## Purpose

This app exists as a minimal example project for the LangGraph support-ticket demo. Tickets about Snippet Stash (bugs, questions, or confusion) can be classified and handled using the project as context.
