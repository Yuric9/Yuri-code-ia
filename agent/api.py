import asyncio
import hmac
import os
import time
from collections import defaultdict, deque
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .agent_runner import AgentConfigurationError, run_agent
from .database import (
    add_message, create_conversation, create_project, forget,
    get_conversation_by_external_id, get_db, get_messages, init_db,
    list_conversations, list_memories, list_projects, recall, remember,
    engine,
)
from .quality_gate import run_quality_gate
from .web_research import search_web

load_dotenv()
if os.getenv("YURI_ENV", "development").strip().lower() != "production":
    init_db()
app = FastAPI(title="Yuri Code AI API", version="0.15.0")
cors_value = os.getenv("CORS_ORIGINS", "").strip()
origins = [item.strip() for item in cors_value.split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
_rate_events: dict[str, deque[float]] = defaultdict(deque)

def _rate_limit_per_minute() -> int:
    try:
        return max(0, int(os.getenv("YURI_RATE_LIMIT_PER_MINUTE", "0")))
    except ValueError:
        return 0

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.url.path == "/health" or request.method == "OPTIONS":
        return await call_next(request)
    configured = os.getenv("YURI_API_TOKEN", "").strip()
    if not configured:
        return JSONResponse({"detail": "YURI_API_TOKEN não configurado."}, status_code=503)
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token or not hmac.compare_digest(token, configured):
        return JSONResponse({"detail": "Token de autenticação inválido."}, status_code=401)
    limit = _rate_limit_per_minute()
    if limit:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{hash(token)}"
        now = time.monotonic()
        events = _rate_events[key]
        while events and now - events[0] >= 60:
            events.popleft()
        if len(events) >= limit:
            return JSONResponse({"detail": "Limite de requisições excedido."}, status_code=429)
        events.append(now)
    return await call_next(request)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    conversation_id: Optional[str] = Field(default=None, max_length=128)
    session_id: Optional[str] = Field(default=None, max_length=128)

class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10_000)

class MemoryRequest(BaseModel):
    scope: str = Field(min_length=1, max_length=100)
    key: str = Field(min_length=1, max_length=255)
    value: Optional[str] = Field(default=None, max_length=20_000)

class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    max_results: int = Field(default=10, ge=1, le=20)

class QualityGateRequest(BaseModel):
    repository: str = Field(default=".", min_length=1, max_length=255)

REQUIRED_TABLES = {"projects", "conversations", "messages", "memories", "research_records"}


def _database_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
            if connection.dialect.name == "sqlite":
                rows = connection.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                tables = {row[0] for row in rows}
            else:
                rows = connection.exec_driver_sql(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    """
                ).fetchall()
                tables = {row[0] for row in rows}
            return REQUIRED_TABLES.issubset(tables)
    except Exception:
        return False


@app.get("/health")
def health_check():
    database = "ok" if _database_ready() else "degraded"
    status = "ok" if database == "ok" else "degraded"
    return {"status": status, "service": "Yuri Code AI", "version": app.version, "database": database}


@app.get("/ready")
def readiness_check():
    """Protected readiness check; never exposes secret values."""
    environment = os.getenv("YURI_ENV", "development").strip().lower()
    database_ok = _database_ready()
    checks = {
        "database": database_ok,
        "api_token": bool(os.getenv("YURI_API_TOKEN", "").strip()),
        "llm": bool(os.getenv("LLM_API_KEY", "").strip()),
    }
    if environment == "production":
        sandbox = os.getenv("YURI_SANDBOX_MODE", "").strip().lower()
        checks["sandbox"] = sandbox in {"docker", "remote"}
        if sandbox == "remote":
            checks["openhands_server"] = bool(os.getenv("OPENHANDS_AGENT_SERVER_URL", "").strip())
    ready = all(checks.values())
    return JSONResponse(
        {"status": "ready" if ready else "not_ready", "environment": environment, "checks": checks},
        status_code=200 if ready else 503,
    )

@app.get("/projects")
def get_projects(db=Depends(get_db)):
    return [{"id": p.id, "name": p.name, "description": p.description} for p in list_projects(db)]

@app.post("/projects")
def post_project(request: ProjectRequest, db=Depends(get_db)):
    p = create_project(db, name=request.name, description=request.description)
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
        timeout = os.getenv("YURI_TASK_TIMEOUT_SECONDS", "").strip()
        work = asyncio.to_thread(run_agent, message, os.getenv("YURI_WORKSPACE", "./workspace"), conv_id)
        response = await asyncio.wait_for(work, timeout=float(timeout)) if timeout else await work
    except AgentConfigurationError as exc:
        raise HTTPException(503, str(exc)) from exc
    except asyncio.TimeoutError as exc:
        raise HTTPException(504, "Tempo limite configurável da tarefa atingido.") from exc
    except Exception as exc:
        add_message(db, conv.id, "assistant", "Erro interno do agente ao processar a tarefa.")
        raise HTTPException(502, "O agente falhou ao processar a tarefa.") from exc
    add_message(db, conv.id, "assistant", response)
    return {"conversation_id": conv_id, "session_id": conv_id, "response": response, "message": response}

@app.post("/memory/remember")
def memory_remember(request: MemoryRequest, db=Depends(get_db)):
    if request.value is None:
        raise HTTPException(422, "value é obrigatório.")
    remember(db, request.scope, request.key, request.value)
    return {"ok": True}

@app.post("/memory/recall")
def memory_recall(request: MemoryRequest, db=Depends(get_db)):
    return {"value": recall(db, request.scope, request.key)}

@app.post("/memory/list")
def memory_list(request: Optional[MemoryRequest] = None, db=Depends(get_db)):
    scope = request.scope if request else None
    return [{"scope": m.scope, "key": m.key, "value": m.value} for m in list_memories(db, scope)]

@app.delete("/memory")
def memory_forget(request: MemoryRequest, db=Depends(get_db)):
    return {"ok": forget(db, request.scope, request.key)}

@app.post("/research")
def research(request: ResearchRequest):
    try:
        return search_web(request.query, request.max_results)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@app.post("/quality-gate")
def quality_gate(request: QualityGateRequest):
    workspace = os.getenv("YURI_WORKSPACE", "./workspace")
    try:
        return run_quality_gate(workspace, request.repository)
    except (ValueError, OSError) as exc:
        raise HTTPException(400, str(exc)) from exc

def start_api():
    uvicorn.run(app, host=os.getenv("YURI_API_HOST", "0.0.0.0"), port=int(os.getenv("YURI_API_PORT", 8000)))

if __name__ == "__main__":
    start_api()
