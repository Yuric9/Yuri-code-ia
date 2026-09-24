from pathlib import Path

from agent.quality_gate import run_quality_gate


def test_quality_gate_runs_pytest(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
    monkeypatch.setenv("YURI_QUALITY_GATE_TIMEOUT_SECONDS", "60")

    result = run_quality_gate(str(tmp_path))
    assert result["ok"] is True
    assert result["checks"][0]["name"] == "pytest"


def test_quality_gate_rejects_outside_workspace(tmp_path):
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    try:
        run_quality_gate(str(tmp_path), "../outside")
    except ValueError as exc:
        assert "fora do workspace" in str(exc)
    else:
        raise AssertionError("path traversal deveria ser rejeitado")
