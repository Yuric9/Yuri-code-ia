import os

from dotenv import load_dotenv

from agent.database import add_message, create_conversation, create_project, get_db, init_db

load_dotenv()
init_db()


def main() -> None:
    workspace = os.getenv("YURI_WORKSPACE", "./workspace")
    os.makedirs(workspace, exist_ok=True)

    db = next(get_db())
    try:
        project = create_project(db, os.getenv("YURI_PROJECT_NAME", "Yuri-Code-AI"), workspace)
        conv = create_conversation(db, "cli-session", project_id=project.id)

        print("🤖 Yuri Code AI v0.11.0 — Modo Interativo")
        print("Digite sua pergunta ou 'sair' para encerrar\n")

        while True:
            try:
                user_input = input("Você > ").strip()
                if user_input.lower() in {"sair", "exit", "quit"}:
                    print("👋 Encerrando...")
                    break
                if not user_input:
                    continue

                add_message(db, conv.id, "user", user_input)
                resposta = f"Recebido: {user_input}"
                add_message(db, conv.id, "assistant", resposta)
                print(f"\nIA > {resposta}\n")
            except KeyboardInterrupt:
                print("\n👋 Encerrando...")
                break
    finally:
        db.close()


if __name__ == "__main__":
    main()
