import os

os.environ["DATABASE_URL"] = "sqlite:///./data/test_api.db"

from fastapi.testclient import TestClient

import agent.api as api


client = TestClient(api.app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_rejects_empty_message():
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 400


def test_chat_runs_agent_and_persists_messages(monkeypatch):
    def fake_run_agent(task, workspace=None):
        assert task == "crie um arquivo"
        return "Tarefa concluída."

    monkeypatch.setattr(api, "run_agent", fake_run_agent)

    response = client.post(
        "/chat",
        json={"message": "crie um arquivo", "session_id": "test-session"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "test-session"
    assert payload["response"] == "Tarefa concluída."

    messages = client.get("/conversations/test-session/messages")
    assert messages.status_code == 200
    assert messages.json() == [
        {"role": "user", "content": "crie um arquivo"},
        {"role": "assistant", "content": "Tarefa concluída."},
    ]
