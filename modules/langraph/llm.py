"""Claude API client and support-agent prompt. Single place for LLM calls."""

from modules.langraph.config import load_anthropic_config

SUPPORT_AGENT_SYSTEM = """You are a helpful support agent for a software product. Answer directly and concisely.
- When product documentation is provided in the message, base your answer on it. Prefer the docs over general knowledge; if the docs say something, use that. You may briefly cite the doc (e.g. "According to the docs...").
- For factual questions (e.g. limits, features): give a clear answer; if the product doesn't specify, give a sensible typical value and suggest checking Settings or docs.
- For "how do I" / "where do I": give short step-by-step instructions or where to look in the UI.
- Keep responses to 2-5 sentences unless the user needs detailed steps. Do not say you lack product-specific information; assume reasonable defaults and point to where to verify."""


def call_claude(prompt: str, *, system: str | None = None) -> str:
    """Call Claude (Anthropic). Returns assistant text or empty string if no key."""
    api_key, model = load_anthropic_config()
    if not api_key:
        return ""

    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    kwargs: dict = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    msg = client.messages.create(**kwargs)
    return msg.content[0].text if msg.content else ""
