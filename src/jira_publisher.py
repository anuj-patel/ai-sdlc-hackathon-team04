from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request

from src.schema import Ticket
from src.tracker import ticket_document


class JiraNotConfigured(RuntimeError):
    pass


def jira_settings() -> dict[str, str] | None:
    base = os.getenv("JIRA_BASE_URL", "").strip().rstrip("/")
    email = os.getenv("JIRA_EMAIL", "").strip()
    token = os.getenv("JIRA_API_TOKEN", "").strip()
    project = os.getenv("JIRA_PROJECT_KEY", "").strip()
    issue_type = os.getenv("JIRA_ISSUE_TYPE", "Task").strip() or "Task"
    if not (base and email and token and project):
        return None
    return {
        "base": base,
        "email": email,
        "token": token,
        "project": project,
        "issue_type": issue_type,
    }


def issue_text(ticket: Ticket) -> str:
    return ticket_document(ticket)


def issue_body(ticket: Ticket, project: str, issue_type: str) -> dict:
    if ticket.status != "ready":
        raise ValueError(f"{ticket.id} is {ticket.status}. Only ready tickets can be pushed.")
    if not ticket.developer_check.passed:
        raise ValueError(f"{ticket.id} did not pass the developer-agent check.")
    paragraphs = []
    for line in issue_text(ticket).split("\n"):
        paragraphs.append(
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": line or " "}],
            }
        )
    return {
        "fields": {
            "project": {"key": project},
            "summary": ticket.title[:250],
            "issuetype": {"name": issue_type},
            "description": {"type": "doc", "version": 1, "content": paragraphs},
        }
    }


def create_issues(tickets: list[Ticket]) -> list[dict[str, str]]:
    """Create one Jira issue per ready ticket. The caller must confirm first."""
    if not tickets:
        raise ValueError("Choose at least one ready ticket.")
    settings = jira_settings()
    if settings is None:
        raise JiraNotConfigured(
            "Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT_KEY in .env."
        )
    created: list[dict[str, str]] = []
    for ticket in tickets:
        payload = issue_body(ticket, settings["project"], settings["issue_type"])
        created.append(_post_issue(settings, payload))
    return created


def _post_issue(settings: dict[str, str], payload: dict) -> dict[str, str]:
    raw = f"{settings['email']}:{settings['token']}".encode()
    request = urllib.request.Request(
        f"{settings['base']}/rest/api/3/issue",
        data=json.dumps(payload).encode(),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {base64.b64encode(raw).decode()}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Jira returned {error.code}. {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach Jira: {error.reason}") from error
    key = body.get("key") or ""
    return {"key": key, "url": f"{settings['base']}/browse/{key}"}
