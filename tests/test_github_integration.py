import pytest

from agent.github_integration import (
    GitHubOpsError,
    open_pull_request,
    repository_policy,
    require_github_token,
    validate_working_branch,
)


def test_repository_policy_normalizes_repo():
    policy = repository_policy("https://github.com/Yuric9/Yuri-code-ia.git")
    assert policy.full_name == "Yuric9/Yuri-code-ia"
    assert policy.base_branch == "main"


def test_working_branch_blocks_base_branches():
    with pytest.raises(GitHubOpsError):
        validate_working_branch("main")
    with pytest.raises(GitHubOpsError):
        validate_working_branch("master")
    with pytest.raises(GitHubOpsError):
        validate_working_branch("feature/../main")


def test_token_is_required(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(GitHubOpsError):
        require_github_token()


def test_open_pull_request_requires_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(GitHubOpsError):
        open_pull_request("Yuric9/Yuri-code-ia", "feat/example")
