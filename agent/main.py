import os
import asyncio
from dotenv import load_dotenv
from agent.database import init_db, create_project, create_conversation, add_message, get_db

load_dotenv()
init_db()

async def main():
    workspace = os.getenv("YURI_WORKSPACE", "./workspace")
    os.makedirs(workspace, exist_ok=True)
    
    db = next(get_db())
    project = create_project(db, os.getenv("YURI_PROJECT_NAME", "Yuri-Code-AI"), workspace)
    conv = create_conversation(db, "cli-session", project_id=project.id)
    
    print("🤖 Yuri Code AI v0.10.0 — Modo Interativo")
    print("Digite sua pergunta ou 'sair' para encerrar
")
    
    while True:
        try:
            user_input = input("Você > ")
            if user_input.lower() in ["sair", "exit", "quit"]:
                print("👋 Encerrando...")
                break
            
            add_message(db, conv.id, "user", user_input)
            resposta = f"Recebido: {user_input}"
            add_message(db, conv.id, "assistant", resposta)
            
            print(f"\nIA > {resposta}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Encerrando...")
            break
    
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
