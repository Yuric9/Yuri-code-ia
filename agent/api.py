import asyncio
import os
import uvicorn
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent_runner import AgentConfigurationError, run_agent
from agent.database import (
    init_db, get_db, create_project, list_projects,
    create_conversation, get_conversation_by_external_id,
    list_conversations, add_message, get_messages,
    remember, recall, list_memories, forget
)

load_dotenv()
init_db()
app = FastAPI(title="Yuri Code AI API", version="0.12.0")

origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Yuri Code AI", "version": app.version}


@app.get("/projects")
def get_projects(db=Depends(get_db)):
    return [{"id": p.id, "name": p.name, "description": p.description} for p in list_projects(db)]


@app.post("/projects")
def post_project(name: str, description: Optional[str] = None, db=Depends(get_db)):
    p = create_project(db, name=name, description=description)
    return {"id": p.id, "name": p.name, "description": p.description}


@app.get("/conversations")
def get_conversations(db=Depends(get_db)):
    return [{"id": c.external_id, "title": c.title, "updated_at": c.updated_at.isoformat()} for c in list_conversations(db)]


@app.get("/conversations/{conv_id}/messages")
def get_conv_messages(conv_id: str, db=Depends(get_db)):
    conv = get_conversation_by_external_id(db, conv_id)
    if not conv:
        raise HTTPException(404, "Conversa não encontrada")
    return [{"role": m.role, "content": m.content} for m in get_messages(db, conv.id)]


@app.post("/chat")
async def chat(request: ChatRequest, db=Depends(get_db)):
    message = request.message.strip()
    if not message:
        raise HTTPException(400, "Mensagem vazia.")

    conv_id = request.conversation_id or request.session_id or f"conv_{os.urandom(8).hex()}"
    conv = get_conversation_by_external_id(db, conv_id)
    if not conv:
        conv = create_conversation(db, conv_id, title=message[:40])

    add_message(db, conv.id, "user", message)
    try:
        response = await asyncio.to_thread(
            run_agent,
            message,
            os.getenv("YURI_WORKSPACE", "./workspace"),
        )
    except AgentConfigurationError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        add_message(db, conv.id, "assistant", f"Erro do agente: {exc}")
        raise HTTPException(502, "O agente falhou ao processar a tarefa.") from exc

    add_message(db, conv.id, "assistant", response)
    return {
        "conversation_id": conv_id,
        "session_id": conv_id,
        "response": response,
        "message": response,
    }


@app.post("/memory/remember")
def memory_remember(scope: str, key: str, value: str, db=Depends(get_db)):
    remember(db, scope, key, value)
    return {"ok": True}


@app.get("/memory/recall")
def memory_recall(scope: str, key: str, db=Depends(get_db)):
    return {"value": recall(db, scope, key)}


@app.get("/memory")
def memory_list(scope: Optional[str] = None, db=Depends(get_db)):
    return [{"scope": m.scope, "key": m.key, "value": m.value} for m in list_memories(db, scope)]


@app.delete("/memory")
def memory_forget(scope: str, key: str, db=Depends(get_db)):
    return {"ok": forget(db, scope, key)}


def start_api():
    uvicorn.run(
        app,
        host=os.getenv("YURI_API_HOST", "0.0.0.0"),
        port=int(os.getenv("YURI_API_PORT", 8000)),
    )


if __name__ == "__main__":
    start_api()
