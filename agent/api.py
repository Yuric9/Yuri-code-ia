import os
import uvicorn
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent.database import (
    init_db, get_db, create_project, list_projects,
    create_conversation, get_conversation_by_external_id,
    list_conversations, add_message, get_messages,
    remember, recall, list_memories, forget
)

load_dotenv()
init_db()

app = FastAPI(title="Yuri Code AI API", version="0.10.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Yuri Code AI", "version": "0.10.0"}

@app.get("/projects")
def get_projects(db=Depends(get_db)):
    return [{"id": p.id, "name": p.name, "description": p.description} for p in list_projects(db)]

@app.post("/projects")
def post_project(name: str, description: str = None, db=Depends(get_db)):
    p = create_project(db, name=name, description=description)
    return {"id": p.id, "name": p.name}

@app.get("/conversations")
def get_conversations(db=Depends(get_db)):
    return [
        {"id": c.external_id, "title": c.title, "updated_at": c.updated_at.isoformat()}
        for c in list_conversations(db)
    ]

@app.get("/conversations/{conv_id}/messages")
def get_conv_messages(conv_id: str, db=Depends(get_db)):
    conv = get_conversation_by_external_id(db, conv_id)
    if not conv:
        raise HTTPException(404, "Conversa não encontrada")
    msgs = get_messages(db, conv.id)
    return [{"role": m.role, "content": m.content} for m in msgs]

@app.post("/chat")
async def chat(request: ChatRequest, db=Depends(get_db)):
    conv_id = request.conversation_id or f"conv_{os.urandom(8).hex()}"
    conv = get_conversation_by_external_id(db, conv_id)
    if not conv:
        conv = create_conversation(db, conv_id, title=request.message[:40])
    
    add_message(db, conv.id, "user", request.message)
    resposta = f"Recebido: {request.message}"
    add_message(db, conv.id, "assistant", resposta)
    
    return {
        "conversation_id": conv_id,
        "response": resposta
    }

@app.post("/memory/remember")
def memory_remember(scope: str, key: str, value: str, db=Depends(get_db)):
    remember(db, scope, key, value)
    return {"ok": True}

@app.get("/memory/recall")
def memory_recall(scope: str, key: str, db=Depends(get_db)):
    val = recall(db, scope, key)
    return {"value": val}

def start_api():
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("API_PORT", 8000)))

if __name__ == "__main__":
    start_api()
