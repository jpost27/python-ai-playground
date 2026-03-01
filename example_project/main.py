"""
Snippet Stash — minimal CLI to save and recall text snippets.

Run from repo root:
  uv run python -m example_project.main add "My title" "Snippet body here"
  uv run python -m example_project.main list
  uv run python -m example_project.main get 1
  uv run python -m example_project.main delete 1
"""

import argparse
import sys

from example_project.store import (
    add_snippet,
    list_snippets,
    get_snippet,
    delete_snippet,
)


def cmd_add(args: argparse.Namespace) -> int:
    snippet = add_snippet(args.title, args.body)
    print(f"Added snippet #{snippet['id']}: {snippet['title']}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    snippets = list_snippets()
    if not snippets:
        print("No snippets yet. Use 'add <title> <body>' to create one.")
        return 0
    for s in snippets:
        preview = (s.get("body") or "")[:50]
        if len(s.get("body") or "") > 50:
            preview += "..."
        print(f"  #{s['id']}  {s.get('title', '(no title)')}  — {preview}")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    s = get_snippet(args.id)
    if not s:
        print(f"Snippet #{args.id} not found.", file=sys.stderr)
        return 1
    print(f"#{s['id']}  {s.get('title', '')}")
    print(s.get("created", ""))
    print()
    print(s.get("body", ""))
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    if delete_snippet(args.id):
        print(f"Deleted snippet #{args.id}.")
        return 0
    print(f"Snippet #{args.id} not found.", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="snippet-stash",
        description="Save and recall text snippets. Data is stored in .snippets.json in the current directory.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Add a new snippet")
    add_p.add_argument("title", help="Short title for the snippet")
    add_p.add_argument("body", help="Snippet body text")
    add_p.set_defaults(func=cmd_add)

    sub.add_parser("list", help="List all snippets (newest first)").set_defaults(func=cmd_list)

    get_p = sub.add_parser("get", help="Show one snippet by id")
    get_p.add_argument("id", type=int, help="Snippet id (from list)")
    get_p.set_defaults(func=cmd_get)

    del_p = sub.add_parser("delete", help="Delete a snippet by id")
    del_p.add_argument("id", type=int, help="Snippet id (from list)")
    del_p.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
