"""OpenHands execution bridge used by the FastAPI service."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class AgentConfigurationError(RuntimeError):
    pass


def _extract_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_extract_text(item) for item in value)
    text = getattr(value, "text", None)
    return text if isinstance(text, str) else ""


def _latest_agent_text(conversation: Any) -> str:
    for event in reversed(list(conversation.state.events)):
        message = getattr(event, "llm_message", None)
        if message is None or getattr(message, "role", None) != "assistant":
            continue
        content = _extract_text(getattr(message, "content", None))
        if content.strip():
            return content.strip()
    return ""


def run_agent(task: str, workspace: str | None = None) -> str:
    """Run one coding task in an OpenHands local workspace."""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise AgentConfigurationError("LLM_API_KEY não configurada.")

    try:
        from pydantic import SecretStr
        from openhands.sdk import Conversation, LLM
        from openhands.tools.preset.default import get_default_agent
    except ImportError as exc:
        raise AgentConfigurationError(
            "OpenHands SDK não está instalado corretamente."
        ) from exc

    root = Path(
        workspace or os.getenv("YURI_WORKSPACE", "./workspace")
    ).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    llm = LLM(
        usage_id="yuri-code-ai",
        model=os.getenv("LLM_MODEL", "gpt-5.5"),
        api_key=SecretStr(api_key),
        base_url=os.getenv("LLM_BASE_URL") or None,
    )
    agent = get_default_agent(llm=llm, cli_mode=True)
    conversation = Conversation(agent=agent, workspace=str(root))

    try:
        conversation.send_message(task)
        conversation.run()
        response = _latest_agent_text(conversation)
        status = getattr(getattr(conversation, "state", None), "execution_status", None)
        return response or f"Tarefa finalizada. Status do agente: {status or 'concluído'}."
    finally:
        close = getattr(conversation, "close", None)
        if callable(close):
            close()
