"""High-level GitHub workflow helpers used by the autonomous agent."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen
import json

from .github_ops import GitHubOpsError, GitHubTarget, commit, parse_repo, push


@dataclass(frozen=True, slots=True)
class PullRequest:
    number: int
    url: str
    title: str


def _api_request(method: str, url: str, payload: dict | None = None) -> dict:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubOpsError("GITHUB_TOKEN não configurado para operações da API GitHub.")
    body = None if payload is None else json.dumps(payload).encode()
    request = Request(url, data=body, method=method, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    })
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def create_pull_request(repo: str, branch: str, base: str = "main", title: str = "Yuri Code AI changes", body: str = "") -> PullRequest:
    target: GitHubTarget = parse_repo(repo)
    data = _api_request(
        "POST",
        f"https://api.github.com/repos/{target.owner}/{target.repo}/pulls",
        {"title": title, "head": branch, "base": base, "body": body},
    )
    return PullRequest(number=int(data["number"]), url=data["html_url"], title=data["title"])


def finish_branch(root: str, repo: str, message: str, branch: str | None = None, base: str = "main", create_pr: bool = False, title: str = "Yuri Code AI changes", body: str = "") -> PullRequest | None:
    path = Path(root).expanduser().resolve()
    current = branch or __import__("subprocess").run(["git", "branch", "--show-current"], cwd=path, text=True, capture_output=True, check=True).stdout.strip()
    commit(str(path), message)
    push(str(path), current)
    if not create_pr:
        return None
    return create_pull_request(repo, current, base, title, body)
