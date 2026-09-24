"""Deterministic quality-gate runner for repository workspaces.

Only predefined commands are executed; user-supplied shell is never evaluated.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class GateCheck:
    name: str
    command: list[str]
    ok: bool
    exit_code: int
    output: str


def _run(root: Path, name: str, command: list[str]) -> GateCheck:
    result = subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        timeout=int(os.getenv("YURI_QUALITY_GATE_TIMEOUT_SECONDS", "300")),
        env={**os.environ, "CI": "1"},
    )
    output = (result.stdout + "\n" + result.stderr).strip()[-12000:]
    return GateCheck(name, command, result.returncode == 0, result.returncode, output)


def _checks(root: Path) -> list[tuple[str, list[str]]]:
    checks: list[tuple[str, list[str]]] = []
    if (root / "pyproject.toml").exists() or (root / "pytest.ini").exists():
        checks.append(("pytest", ["python", "-m", "pytest", "-q"]))
    package = root / "package.json"
    if package.exists():
        try:
            scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
        except (OSError, json.JSONDecodeError):
            scripts = {}
        if "build" in scripts:
            checks.append(("npm-build", ["npm", "run", "build"]))
    return checks


def run_quality_gate(workspace: str, relative_repo: str = ".") -> dict:
    base = Path(workspace).expanduser().resolve()
    root = (base / relative_repo).resolve()
    if root != base and base not in root.parents:
        raise ValueError("Repositório fora do workspace permitido.")
    if not root.is_dir():
        raise ValueError("Diretório do repositório não encontrado.")
    checks = [_run(root, name, command) for name, command in _checks(root)]
    if not checks:
        return {"ok": False, "checks": [], "message": "Nenhum projeto Python/Node reconhecido."}
    return {
        "ok": all(item.ok for item in checks),
        "checks": [asdict(item) for item in checks],
        "message": "Quality gate aprovado." if all(item.ok for item in checks) else "Quality gate reprovado.",
    }
