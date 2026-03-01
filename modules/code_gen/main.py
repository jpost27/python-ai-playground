"""
Code generation module — detect bug → generate fix (with validation pipeline).

Weeks 7–8: Code generation with Claude, AST/lint validation, fix-PR prototype.
Run: uv run python -m modules.code_gen.main
Install deps: uv sync --extra code-gen
"""


def main() -> None:
    print("Code gen module: detect bug → generate fix PR (placeholder).")
    # TODO: Generate patch → validate (AST, ruff) → optional PR flow


if __name__ == "__main__":
    main()
