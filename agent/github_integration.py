"""Phase 2 GitHub integration with explicit safety boundaries."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

from .github_ops import GitHubOpsError, GitHubTarget, parse_repo
from .github_workflow import PullRequest, create_pull_request


@dataclass(frozen=True, slots=True)
class RepositoryPolicy:
    owner: str
    repo: str
    base_branch: str = "main"

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


def repository_policy(repo: str, base_branch: str = "main") -> RepositoryPolicy:
    target: GitHubTarget = parse_repo(repo)
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", base_branch) or base_branch in {".", ".."}:
        raise GitHubOpsError("Branch base inválida.")
    return RepositoryPolicy(target.owner, target.repo, base_branch)


def require_github_token() -> str:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise GitHubOpsError("GITHUB_TOKEN não configurado para a integração GitHub.")
    return token


def validate_working_branch(branch: str, base_branch: str = "main") -> str:
    branch = branch.strip()
    if not branch or branch in {"main", "master", base_branch}:
        raise GitHubOpsError("A automação não pode trabalhar diretamente na branch protegida/base.")
    if branch.startswith("-") or ".." in branch or not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
        raise GitHubOpsError("Nome de branch inválido.")
    return branch


def open_pull_request(
    repo: str,
    branch: str,
    *,
    base: str = "main",
    title: str = "Yuri Code AI changes",
    body: str = "",
) -> PullRequest:
    require_github_token()
    policy = repository_policy(repo, base)
    safe_branch = validate_working_branch(branch, policy.base_branch)
    return create_pull_request(policy.full_name, safe_branch, policy.base_branch, title, body)
