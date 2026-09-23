import { NextResponse } from "next/server";

const agentUrl = process.env.YURI_AGENT_API_URL?.replace(/\/$/, "");

type AgentResponse = {
  session_id?: string;
  message?: string;
  workspace?: string;
};

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const message = typeof body.message === "string" ? body.message.trim() : "";
  const sessionId = typeof body.session_id === "string" ? body.session_id : undefined;

  if (!message) {
    return NextResponse.json({ message: "Envie uma tarefa para o agente." }, { status: 400 });
  }

  if (!agentUrl) {
    return NextResponse.json(
      { message: "O backend da Yuri Code AI ainda não está configurado. Defina YURI_AGENT_API_URL." },
      { status: 503 },
    );
  }

  try {
    const response = await fetch(`${agentUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
      cache: "no-store",
    });

    const data = (await response.json().catch(() => ({}))) as AgentResponse & { detail?: string };

    if (!response.ok) {
      return NextResponse.json(
        { message: data.detail ?? "O agente não conseguiu processar a tarefa." },
        { status: response.status >= 500 ? 502 : response.status },
      );
    }

    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { message: "Não foi possível conectar ao backend Python da Yuri Code AI." },
      { status: 502 },
    );
  }
}
