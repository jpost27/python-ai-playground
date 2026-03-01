"""Graph node handlers: each takes TicketState, returns state update dict."""

import re
import subprocess
from pathlib import Path

from modules.langraph.classifier import classify
from modules.langraph.config import has_anthropic_key, get_github_token
from modules.langraph.llm import (
    RCA_SYSTEM,
    FIX_SYSTEM,
    SUPPORT_AGENT_SYSTEM,
    call_claude,
)
from modules.langraph.retrieval import (
    get_search_queries_for_bug,
    get_search_queries_from_ticket,
    retrieve_relevant_code,
    retrieve_relevant_docs,
)
from modules.langraph.state import TicketState

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def classify_ticket(state: TicketState) -> dict:
    """Set classification from ticket text."""
    return {"classification": classify(state["ticket"])}


def _prompt_with_docs(docs_context: str, ticket: str, instruction: str) -> str:
    """Build user prompt with optional product docs."""
    if docs_context and docs_context.strip():
        return (
            f"Use the following product documentation as context. {instruction}\n\n"
            "--- Documentation ---\n"
            f"{docs_context.strip()}\n"
            "--- End documentation ---\n\n"
            f"Support ticket: {ticket}"
        )
    return f"Support ticket (no documentation loaded): {ticket}"


def answer_question(state: TicketState) -> dict:
    """Answer a factual question using product docs when available."""
    if not has_anthropic_key():
        return {"response": "[Demo mode] Set ANTHROPIC_API_KEY to enable."}
    try:
        prompt = _prompt_with_docs(
            state.get("docs_context") or "",
            state["ticket"],
            "Answer this factual question based on the documentation when possible.",
        )
        text = call_claude(prompt, system=SUPPORT_AGENT_SYSTEM)
        return {"response": text or "I couldn't generate an answer."}
    except Exception:
        return {"response": "[Demo mode] LLM call failed. Check API key and model."}


def retrieve_docs(state: TicketState) -> dict:
    """Filter docs to only sections relevant to the ticket (question/confusion path)."""
    full_docs = (state.get("docs_context") or "").strip()
    if not full_docs:
        return {}
    ticket = state.get("ticket") or ""
    llm_cb = call_claude if has_anthropic_key() else None
    queries = get_search_queries_from_ticket(ticket, llm_callback=llm_cb)
    filtered = retrieve_relevant_docs(full_docs, ticket, search_queries=queries)
    return {"docs_context": filtered}


def suggest_help(state: TicketState) -> dict:
    """Suggest steps or resources for confused users using product docs when available."""
    if not has_anthropic_key():
        return {"response": "[Demo mode] Set ANTHROPIC_API_KEY to enable."}
    try:
        prompt = _prompt_with_docs(
            state.get("docs_context") or "",
            state["ticket"],
            "The user is confused — suggest steps or where to look, using the documentation to clear things up.",
        )
        text = call_claude(prompt, system=SUPPORT_AGENT_SYSTEM)
        return {"response": text or "I couldn't generate suggestions."}
    except Exception as e:
        return {"response": f"[LLM call failed] {type(e).__name__}: {e}"}


def retrieve_code(state: TicketState) -> dict:
    """Filter code to only chunks relevant to the bug (bug path)."""
    full_code = (state.get("code_context") or "").strip()
    if not full_code:
        return {}
    ticket = state.get("ticket") or ""
    llm_cb = call_claude if has_anthropic_key() else None
    queries = get_search_queries_for_bug(ticket, llm_callback=llm_cb)
    filtered = retrieve_relevant_code(full_code, ticket, search_queries=queries)
    return {"code_context": filtered}


def root_cause_analysis(state: TicketState) -> dict:
    """Run RCA using ticket, docs, and code context; set rca_result and response."""
    ticket = state["ticket"]
    if not has_anthropic_key():
        return {
            "rca_result": "",
            "response": "[Demo mode] Set ANTHROPIC_API_KEY to enable RCA.",
        }
    code = (state.get("code_context") or "").strip()
    docs = (state.get("docs_context") or "").strip()
    context_parts = []
    if code:
        context_parts.append("--- Source code ---\n" + code)
    if docs:
        context_parts.append("--- User docs ---\n" + docs[:8000])
    context = "\n\n".join(context_parts) if context_parts else "No code or docs provided."
    prompt = (
        "Bug report from user:\n\n"
        f"{ticket}\n\n"
        "Use the following project context to identify the root cause (file and what's wrong).\n\n"
        f"{context}"
    )
    try:
        rca = call_claude(prompt, system=RCA_SYSTEM)
        rca = (rca or "").strip()
        if not rca:
            rca = "Could not determine root cause."
        return {
            "rca_result": rca,
            "response": f"**Root cause analysis**\n{rca}",
        }
    except Exception as e:
        return {
            "rca_result": "",
            "response": f"[RCA failed] {type(e).__name__}: {e}",
        }


def _extract_diff_from_llm(text: str) -> str:
    """Extract unified diff from LLM output (e.g. inside ```diff ... ```)."""
    if not text or not text.strip():
        return ""
    # Prefer fenced block with diff
    m = re.search(r"```(?:diff)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # If the whole output looks like a diff (starts with --- or +++), use it
    if text.strip().startswith("---") or text.strip().startswith("+++"):
        return text.strip()
    return ""


def propose_fix(state: TicketState) -> dict:
    """Propose a code fix from RCA and code context; set suggested_fix and append to response."""
    rca = (state.get("rca_result") or "").strip()
    ticket = state.get("ticket") or ""
    code = (state.get("code_context") or "").strip()
    response_so_far = state.get("response") or ""
    if not has_anthropic_key():
        return {
            "suggested_fix": "",
            "response": response_so_far + "\n\n[Demo mode] Set ANTHROPIC_API_KEY to generate a fix.",
        }
    if not rca:
        return {
            "suggested_fix": "",
            "response": response_so_far + "\n\nNo fix proposed (no RCA).",
        }
    prompt = (
        "Root cause analysis:\n\n"
        f"{rca}\n\n"
        "Bug report:\n\n"
        f"{ticket}\n\n"
        "Source code:\n\n"
        f"{code}\n\n"
        "Produce a unified diff that fixes this bug. Paths relative to repo root (e.g. example_project/store.py)."
    )
    try:
        raw = call_claude(prompt, system=FIX_SYSTEM, max_tokens=2048)
        diff = _extract_diff_from_llm(raw or "")
        if not diff:
            return {
                "suggested_fix": "",
                "response": response_so_far + "\n\n**Suggested fix**\nCould not generate a valid diff.\n\n" + (raw or ""),
            }
        return {
            "suggested_fix": diff,
            "response": response_so_far + "\n\n**Suggested fix (unified diff)**\n```diff\n" + diff + "\n```",
        }
    except Exception as e:
        return {
            "suggested_fix": "",
            "response": response_so_far + f"\n\n[Fix generation failed] {type(e).__name__}: {e}",
        }


def create_pr(state: TicketState) -> dict:
    """If suggested_fix and GITHUB_TOKEN, create branch, apply diff, push, open PR; else append message."""
    response_so_far = state.get("response") or ""
    diff = (state.get("suggested_fix") or "").strip()
    token = get_github_token()
    if not diff:
        return {"response": response_so_far + "\n\nNo PR created (no suggested fix)."}
    if not token:
        return {
            "pr_url": "",
            "response": response_so_far + "\n\nSet GITHUB_TOKEN (or GH_TOKEN) to create a PR automatically.",
        }
    try:
        from github import Github
        repo = _get_repo_for_pr(token)
        if not repo:
            return {
                "pr_url": "",
                "response": response_so_far + "\n\nCould not resolve repo for PR (not a GitHub repo or no remote).",
            }
        branch_name = _create_branch_apply_and_push(repo, diff, token)
        if not branch_name:
            return {
                "pr_url": "",
                "response": response_so_far + "\n\nFailed to apply diff or push branch.",
            }
        pr = repo.create_pull(
            title="Hotfix from support ticket",
            body="Automated fix from support ticket RCA.\n\n" + (state.get("ticket") or "")[:500],
            head=branch_name,
            base=repo.default_branch,
        )
        pr_url = pr.html_url or ""
        return {
            "pr_url": pr_url,
            "response": response_so_far + f"\n\n**Pull request created:** {pr_url}",
        }
    except Exception as e:
        return {
            "pr_url": "",
            "response": response_so_far + f"\n\n[PR creation failed] {type(e).__name__}: {e}",
        }


def _get_repo_for_pr(token: str):
    """Resolve GitHub repo from current git remote; return PyGithub repo or None."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0:
            return None
        root = r.stdout.strip()
        r2 = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r2.returncode != 0 or not r2.stdout.strip():
            return None
        url = r2.stdout.strip()
        # ssh: git@github.com:owner/repo.git  or https: https://github.com/owner/repo.git
        if "github.com" not in url:
            return None
        from github import Github
        g = Github(token)
        if "github.com:" in url or "@github.com:" in url:
            # ssh
            m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
        else:
            m = re.search(r"github\.com[/]([^/]+)/([^/]+?)(?:\.git)?$", url)
        if not m:
            return None
        owner, repo_name = m.group(1), m.group(2)
        return g.get_repo(f"{owner}/{repo_name}")
    except Exception:
        return None


def _create_branch_apply_and_push(repo, diff: str, token: str) -> str | None:
    """Create hotfix branch, apply diff, commit, push. Returns branch name or None."""
    import os
    import tempfile
    from datetime import datetime, timezone

    branch_name = "hotfix/support-ticket-" + datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        default = repo.default_branch
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0:
            return None
        if r.stdout.strip():
            # Uncommitted changes - we need a clean tree to apply. Stash or abort.
            return None
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        current = (r.stdout or "").strip() or "main"
        r = subprocess.run(
            ["git", "fetch", "origin", default],
            cwd=_REPO_ROOT,
            capture_output=True,
            timeout=10,
        )
        if r.returncode != 0:
            return None
        r = subprocess.run(
            ["git", "checkout", "-b", branch_name, f"origin/{default}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            timeout=5,
        )
        if r.returncode != 0:
            return None
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False, encoding="utf-8") as f:
            f.write(diff)
            f.flush()
            path = f.name
        try:
            r = subprocess.run(
                ["git", "apply", "--ignore-whitespace", path],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode != 0:
                subprocess.run(["git", "checkout", current], cwd=_REPO_ROOT, capture_output=True, timeout=5)
                subprocess.run(["git", "branch", "-D", branch_name], cwd=_REPO_ROOT, capture_output=True)
                return None
            r = subprocess.run(
                ["git", "add", "-A"],
                cwd=_REPO_ROOT,
                capture_output=True,
                timeout=5,
            )
            r = subprocess.run(
                ["git", "commit", "-m", "Hotfix from support ticket (RCA)"],
                cwd=_REPO_ROOT,
                capture_output=True,
                timeout=5,
            )
            if r.returncode != 0:
                subprocess.run(["git", "checkout", current], cwd=_REPO_ROOT, capture_output=True, timeout=5)
                subprocess.run(["git", "branch", "-D", branch_name], cwd=_REPO_ROOT, capture_output=True)
                return None
            env = {**os.environ, "GITHUB_TOKEN": token, "GH_TOKEN": token}
            r = subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=_REPO_ROOT,
                capture_output=True,
                timeout=30,
                env=env,
            )
            if r.returncode != 0:
                push_url = repo.clone_url.replace("https://", f"https://x-access-token:{token}@")
                subprocess.run(
                    ["git", "remote", "add", "push-origin", push_url],
                    cwd=_REPO_ROOT,
                    capture_output=True,
                )
                r2 = subprocess.run(
                    ["git", "push", "-u", "push-origin", branch_name],
                    cwd=_REPO_ROOT,
                    capture_output=True,
                    timeout=30,
                )
                subprocess.run(["git", "remote", "remove", "push-origin"], cwd=_REPO_ROOT, capture_output=True)
                if r2.returncode != 0:
                    subprocess.run(["git", "checkout", current], cwd=_REPO_ROOT, capture_output=True, timeout=5)
                    return None
            subprocess.run(["git", "checkout", current], cwd=_REPO_ROOT, capture_output=True, timeout=5)
            return branch_name
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    except Exception:
        return None
