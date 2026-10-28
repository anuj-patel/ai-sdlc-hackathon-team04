from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.request

MAX_CONTEXT_CHARS = 12_000
_REPO = re.compile(r"^[A-Za-z0-9_.-]+$")


def parse_repo(value: str) -> tuple[str, str]:
    raw = value.strip().rstrip("/")
    if raw.endswith(".git"):
        raw = raw[:-4]
    raw = re.sub(r"^https?://github\.com/", "", raw)
    raw = re.sub(r"^git@github\.com:", "", raw)
    parts = [part for part in raw.split("/") if part]
    if len(parts) < 2 or not _REPO.fullmatch(parts[0]) or not _REPO.fullmatch(parts[1]):
        raise ValueError("Use a GitHub URL like https://github.com/owner/repo or owner/repo")
    return parts[0], parts[1]


def _token() -> str:
    token = (os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or "").strip()
    if token:
        return token
    try:
        completed = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def fetch_readme(repo: str) -> str:
    """Read a repository README. Uses GITHUB_TOKEN, GH_TOKEN, or `gh auth` when set."""
    owner, name = parse_repo(repo)
    token = _token()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "vague-to-tickets",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{name}/readme",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:240]
        if error.code in {401, 403}:
            raise RuntimeError(
                "GitHub refused access. Set GITHUB_TOKEN in .env, or run `gh auth login`."
            ) from error
        if error.code == 404:
            raise RuntimeError(
                f"No README found for {owner}/{name}. Check the URL, or set GITHUB_TOKEN for a private repo."
            ) from error
        raise RuntimeError(f"GitHub returned {error.code} for {owner}/{name}. {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach GitHub: {error.reason}") from error

    encoded = payload.get("content") or ""
    text = base64.b64decode(encoded).decode("utf-8", errors="replace").strip()
    if not text:
        raise RuntimeError(f"{owner}/{name} has an empty README.")
    return text


def clip_context(text: str) -> str:
    cleaned = text.strip()
    if len(cleaned) <= MAX_CONTEXT_CHARS:
        return cleaned
    return cleaned[: MAX_CONTEXT_CHARS - 1] + "…"
