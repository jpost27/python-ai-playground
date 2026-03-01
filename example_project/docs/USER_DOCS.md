# Snippet Stash — User documentation

This document describes Snippet Stash: what it is, how to use it, and what to expect. Use it as the source of truth when answering user questions or clearing up confusion.

---

## What is Snippet Stash?

**Snippet Stash** is a small command-line tool for saving and recalling short pieces of text (“snippets”). Each snippet has:

- **Id** — A number assigned automatically when you add the snippet (1, 2, 3, …). You use this id with `get` and `delete`.
- **Title** — A short label you give when adding (e.g. “Shopping list”, “API key”).
- **Body** — The main text content.
- **Created** — The time the snippet was added (stored automatically in UTC).

There is no account, no server, and no cloud. Everything is stored in a single file on your machine.

---

## How to run it

You must run Snippet Stash from the **python-ai-playground** project root, using the project’s environment:

```bash
uv run python -m example_project.main <command> [arguments]
```

If you don’t have `uv` installed, see the main project README for setup. You can also run it with the project’s Python directly, for example:

```bash
.venv\Scripts\python -m example_project.main list
```

Replace `list` with any command described below.

---

## Commands

### `add` — Add a new snippet

**Usage:** `add <title> <body>`

Creates a new snippet with the title and body you provide. The tool prints the new snippet’s id.

**Examples:**

```bash
uv run python -m example_project.main add "Todo" "Buy milk, call dentist"
uv run python -m example_project.main add "API key" "sk-abc123..."
uv run python -m example_project.main add "Note" "Meeting at 3pm on Tuesday"
```

**Tips:**

- Title and body are separate arguments. If your title or body contains spaces, wrap the whole argument in quotes (as in the examples).
- There is no character limit enforced by the app, but very long snippets make the list preview less readable.

---

### `list` — List all snippets

**Usage:** `list`

Shows every snippet in one list. For each snippet you see:

- Its **id** (e.g. `#1`, `#2`)
- Its **title**
- A **preview** of the body (first 50 characters, then `...` if longer)

Snippets are ordered **newest first** (most recently added at the top).

**Example output:**

```
  #3  Note  — Meeting at 3pm on Tuesday
  #2  API key  — sk-abc123...
  #1  Todo  — Buy milk, call dentist
```

If you have no snippets yet, you’ll see:  
`No snippets yet. Use 'add <title> <body>' to create one.`

---

### `get` — Show one snippet in full

**Usage:** `get <id>`

Prints the full snippet for the given id: title, creation time, and full body. Use the id from `list`.

**Examples:**

```bash
uv run python -m example_project.main get 1
uv run python -m example_project.main get 3
```

If the id doesn’t exist, the tool prints `Snippet #<id> not found.` and exits with an error.

---

### `delete` — Remove a snippet

**Usage:** `delete <id>`

Permanently removes the snippet with that id. The change is saved immediately.

**Examples:**

```bash
uv run python -m example_project.main delete 2
```

If the id doesn’t exist, you’ll see `Snippet #<id> not found.` and the command exits with an error.

---

## Where is my data stored?

All snippets are stored in a single file:

- **File name:** `.snippets.json`
- **Location:** The **current working directory** when you run the command (usually the folder you’re in when you open the terminal, or the project root if you `cd` there first).

So:

- If you run the tool from `C:\Projects\python-ai-playground`, the file is `C:\Projects\python-ai-playground\.snippets.json`.
- If you run it from `C:\Projects\python-ai-playground\docs`, the file is `C:\Projects\python-ai-playground\docs\.snippets.json`.

There is no sync between folders: each folder has its own `.snippets.json` and thus its own set of snippets. There is no export to PDF, no cloud backup, and no built-in way to merge or move data—only this local JSON file.

---

## Limitations

1. **Plain text only** — Title and body are stored as plain text. There is no Markdown, no rich text, and no tags or categories.

2. **One file per directory** — Data lives in `.snippets.json` in the current working directory. Different directories mean different snippet sets.

3. **No search** — There is no search command. To find something, use `list` and then `get <id>` for the snippet you want.

4. **No edit** — You cannot change a snippet after adding it. To “edit,” delete the old snippet and add a new one.

5. **Ids are not reused** — When you delete a snippet, its id is not reassigned. New snippets always get the next available id (e.g. after deleting #2, the next add might be #4).

6. **No size limit** — The app does not enforce a maximum number of snippets or length of text. Very large `.snippets.json` files may become slow to read or write.

7. **Encoding** — The file is saved as UTF-8. Non-ASCII characters (e.g. emoji, accented letters) are supported.

---

## Examples in one place

```bash
# Add a few snippets
uv run python -m example_project.main add "First" "Hello world"
uv run python -m example_project.main add "Second" "Another snippet here"

# See them (newest first)
uv run python -m example_project.main list

# Read the first one in full
uv run python -m example_project.main get 1

# Remove the second one
uv run python -m example_project.main delete 2

# List again to confirm
uv run python -m example_project.main list
```

---

## Common questions and confusion

**Why are snippets in reverse order in `list`?**  
They are shown newest first so you can quickly see what you added last. There is no option to sort oldest-first in the current version.

**I ran `list` and see nothing. Did I lose my data?**  
Check which folder you’re in. Snippet Stash uses `.snippets.json` in the **current directory**. If you ran the tool from a different folder than before, you’re looking at a different (possibly empty) file.

**Can I export my snippets?**  
Your data is already in a single file: `.snippets.json`. You can copy or back up that file. The format is standard JSON (id, title, body, created per snippet). There is no built-in “export to PDF” or similar.

**What if I get “Snippet #X not found”?**  
That id doesn’t exist in the current `.snippets.json`. Run `list` to see the ids that exist in the folder you’re in.

**Can I use Snippet Stash from another project?**  
You run it as part of the python-ai-playground repo (`uv run python -m example_project.main ...`). You can run that from any directory—the **snippet file** will be created in whatever directory is current when you run the command.

---

*This documentation is the authoritative reference for Snippet Stash behavior and is intended for use when answering user questions or resolving confusion about the tool.*
