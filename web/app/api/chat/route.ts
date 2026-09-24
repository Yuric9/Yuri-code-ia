import { NextResponse } from "next/server";

const agentUrl = process.env.YURI_AGENT_API_URL?.replace(/\/$/, "");
const agentToken = process.env.YURI_API_TOKEN;

type AgentResponse = { session_id?: string; conversation_id?: string; message?: string; response?: string };

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const message = typeof body.message === "string" ? body.message.trim() : "";
  const sessionId = typeof body.session_id === "string" ? body.session_id : undefined;
  if (!message) return NextResponse.json({ message: "Envie uma tarefa para o agente." }, { status: 400 });
  if (!agentUrl) return NextResponse.json({ message: "Backend não configurado. Defina YURI_AGENT_API_URL." }, { status: 503 });
  if (!agentToken) return NextResponse.json({ message: "Token do backend não configurado no servidor." }, { status: 503 });
  try {
    const response = await fetch(agentUrl + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${agentToken}` },
      body: JSON.stringify({ message, session_id: sessionId }),
      cache: "no-store",
    });
    const data = (await response.json().catch(() => ({}))) as AgentResponse & { detail?: string };
    if (!response.ok) return NextResponse.json({ message: data.detail ?? "O agente não conseguiu processar a tarefa." }, { status: response.status >= 500 ? 502 : response.status });
    return NextResponse.json({ session_id: data.session_id ?? data.conversation_id, message: data.message ?? data.response });
  } catch {
    return NextResponse.json({ message: "Não foi possível conectar ao backend Python da Yuri Code AI." }, { status: 502 });
  }
}
