"""Interactive CLI for Yuri Code AI."""
import os

from dotenv import load_dotenv

from agent.agent_runner import AgentConfigurationError, run_agent
from agent.database import (
    add_message,
    create_conversation,
    create_project,
    get_db,
    init_db,
    remember,
)

load_dotenv()
init_db()


def main() -> None:
    workspace = os.getenv("YURI_WORKSPACE", "./workspace")
    os.makedirs(workspace, exist_ok=True)
    conversation_id = os.getenv("YURI_CLI_CONVERSATION_ID", "cli-session")

    db = next(get_db())
    try:
        project = create_project(
            db, os.getenv("YURI_PROJECT_NAME", "Yuri-Code-AI"), workspace
        )
        conv = create_conversation(db, conversation_id, project_id=project.id)

        print("🤖 Yuri Code AI — CLI")
        print("Digite uma tarefa para o agente ou 'sair' para encerrar.\n")

        while True:
            try:
                user_input = input("Você > ").strip()
                if user_input.lower() in {"sair", "exit", "quit"}:
                    print("👋 Encerrando...")
                    break
                if not user_input:
                    continue

                add_message(db, conv.id, "user", user_input)
                try:
                    resposta = run_agent(
                        user_input,
                        workspace=workspace,
                        conversation_id=conversation_id,
                    )
                except AgentConfigurationError as exc:
                    resposta = f"Configuração do agente: {exc}"
                except Exception as exc:
                    resposta = f"Erro do agente: {exc}"
                add_message(db, conv.id, "assistant", resposta)
                print(f"\nIA > {resposta}\n")
            except KeyboardInterrupt:
                print("\n👋 Encerrando...")
                break
    finally:
        db.close()


if __name__ == "__main__":
    main()
