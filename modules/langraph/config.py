"""Environment and Anthropic configuration. Loads .env from project root."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root (parent of modules/langraph)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def load_anthropic_config() -> tuple[str | None, str]:
    """Return (api_key, model). Use for all LLM calls."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    return api_key, model


def has_anthropic_key() -> bool:
    """True if ANTHROPIC_API_KEY is set (for demo vs LLM mode)."""
    api_key, _ = load_anthropic_config()
    return bool(api_key)


def get_github_token() -> str | None:
    """Return GITHUB_TOKEN if set (for creating PRs)."""
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
