import os

os.environ["DATABASE_URL"] = "sqlite:///./data/test_api.db"
os.environ["YURI_API_TOKEN"] = "test-token"

from fastapi.testclient import TestClient
import agent.api as api

client = TestClient(api.app)
AUTH = {"Authorization": "Bearer test-token"}


def test_health_is_public():
    response = client.get("/health")
    assert response.status_code == 200


def test_protected_route_requires_token():
    assert client.get("/projects").status_code == 401
    assert client.get("/projects", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_chat_rejects_empty_message():
    response = client.post("/chat", json={"message": "   "}, headers=AUTH)
    assert response.status_code == 400


def test_projects_use_json_body():
    response = client.post("/projects", json={"name": "teste"}, headers=AUTH)
    assert response.status_code == 200


def test_chat_runs_agent_and_persists_messages(monkeypatch):
    def fake_run_agent(task, workspace=None, conversation_id="default"):
        assert task == "crie um arquivo"
        assert conversation_id == "test-session"
        return "Tarefa concluída."

    monkeypatch.setattr(api, "run_agent", fake_run_agent)
    response = client.post(
        "/chat",
        json={"message": "crie um arquivo", "session_id": "test-session"},
        headers=AUTH,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "test-session"
    assert payload["response"] == "Tarefa concluída."
    messages = client.get("/conversations/test-session/messages", headers=AUTH)
    assert messages.status_code == 200
    assert messages.json()[-2:] == [
        {"role": "user", "content": "crie um arquivo"},
        {"role": "assistant", "content": "Tarefa concluída."},
    ]


def test_agent_requires_api_key(monkeypatch):
    from agent.agent_runner import AgentConfigurationError, run_agent

    monkeypatch.delenv("LLM_API_KEY", raising=False)
    try:
        run_agent("teste")
    except AgentConfigurationError as exc:
        assert "LLM_API_KEY" in str(exc)
    else:
        raise AssertionError("run_agent deveria exigir LLM_API_KEY")


def test_destructive_confirmation_guard(monkeypatch):
    from agent.agent_runner import AgentConfigurationError, run_agent

    monkeypatch.setenv("LLM_API_KEY", "test-only")
    monkeypatch.setenv("YURI_CONFIRMATION_MODE", "always")
    try:
        run_agent("git push --force origin main")
    except AgentConfigurationError as exc:
        assert "confirmação humana" in str(exc)
    else:
        raise AssertionError("ação destrutiva deveria exigir confirmação")


def test_research_without_provider_is_graceful(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    response = client.post(
        "/research",
        json={"query": "Next.js App Router", "max_results": 3},
        headers=AUTH,
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is False
