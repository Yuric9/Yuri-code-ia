import { NextResponse } from "next/server";

const agentUrl = (
  process.env.BACKEND_INTERNAL_URL ??
  process.env.YURI_AGENT_API_URL
)?.replace(/\/$/, "");

export async function GET() {
  if (!agentUrl) return NextResponse.json({ status: "unconfigured", message: "Backend não configurado." }, { status: 503 });
  try {
    const response = await fetch(agentUrl + "/health", {
      cache: "no-store",
      signal: AbortSignal.timeout(5_000),
    });
    const data = (await response.json().catch(() => ({}))) as { status?: string; service?: string; version?: string };
    if (!response.ok) return NextResponse.json({ status: "offline", message: "Backend indisponível." }, { status: 503 });
    return NextResponse.json({ status: data.status === "ok" ? "ok" : "degraded", service: data.service, version: data.version });
  } catch {
    return NextResponse.json({ status: "offline", message: "Não foi possível conectar ao backend." }, { status: 503 });
  }
}
