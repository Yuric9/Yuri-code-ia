"""Safe GitHub repository operations for autonomous engineering tasks."""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class GitHubTarget:
    owner: str
    repo: str


class GitHubOpsError(RuntimeError):
    pass


def parse_repo(value: str) -> GitHubTarget:
    value = value.strip()
    if value.startswith("git@github.com:"):
        value = value.split(":", 1)[1]
    elif value.startswith("https://github.com/") or value.startswith("http://github.com/"):
        value = urlparse(value).path.strip("/")
    value = value.removesuffix(".git").strip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise GitHubOpsError("Repositório GitHub inválido; use owner/repo ou uma URL GitHub.")
    owner, repo = value.split("/", 1)
    return GitHubTarget(owner, repo)


def _run(root: Path, *args: str) -> str:
    env = os.environ.copy()
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, env=env)
    output = (result.stdout + "
" + result.stderr).strip()
    if result.returncode:
        raise GitHubOpsError(output or f"git {' '.join(args)} falhou")
    return result.stdout.strip()


def clone(repo: str, destination: str, ref: str | None = None) -> str:
    """Clone a public or credentialed GitHub repository using the local Git credential setup."""
    parse_repo(repo)
    target = Path(destination).expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        raise GitHubOpsError(f"Destino já existe e não está vazio: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    command = ["clone"]
    if ref:
        command += ["--branch", ref]
    command += [repo, str(target)]
    subprocess.run(["git", *command], text=True, check=True)
    return str(target)


def status(root: str) -> str:
    return _run(Path(root).expanduser().resolve(), "status", "--short", "--branch")


def create_branch(root: str, branch: str, base: str | None = None) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or branch.startswith("/") or branch.endswith("/"):
        raise GitHubOpsError("Nome de branch inválido.")
    path = Path(root).expanduser().resolve()
    if base:
        _run(path, "fetch", "origin", base)
        _run(path, "switch", "-c", branch, f"origin/{base}")
    else:
        _run(path, "switch", "-c", branch)
    return _run(path, "branch", "--show-current")


def commit(root: str, message: str) -> str:
    path = Path(root).expanduser().resolve()
    if not message.strip():
        raise GitHubOpsError("Mensagem de commit vazia.")
    _run(path, "add", "--all")
    if not _run(path, "status", "--porcelain"):
        return _run(path, "rev-parse", "HEAD")
    _run(path, "commit", "-m", message.strip())
    return _run(path, "rev-parse", "HEAD")


def push(root: str, branch: str | None = None, *, set_upstream: bool = True) -> str:
    path = Path(root).expanduser().resolve()
    current = branch or _run(path, "branch", "--show-current")
    if not current:
        raise GitHubOpsError("Não foi possível determinar a branch atual.")
    args = ["push"]
    if set_upstream:
        args += ["-u", "origin", current]
    else:
        args += ["origin", current]
    return _run(path, *args)
