from agent.github_ops import GitHubOpsError, parse_repo


def test_parse_owner_repo():
    assert parse_repo("Yuric9/Yuri-Code-AI").owner == "Yuric9"
    assert parse_repo("https://github.com/Yuric9/Yuri-Code-AI.git").repo == "Yuri-Code-AI"


def test_parse_ssh_repo():
    target = parse_repo("git@github.com:Yuric9/Yuri-code-ia.git")
    assert target.owner == "Yuric9"
    assert target.repo == "Yuri-code-ia"


def test_reject_invalid_repo():
    import pytest

    with pytest.raises(GitHubOpsError):
        parse_repo("not-a-repository")
