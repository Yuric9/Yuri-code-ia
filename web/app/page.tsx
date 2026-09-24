"use client";

import { FormEvent, KeyboardEvent, useEffect, useState } from "react";

type Message = { role: "user" | "ai"; text: string };
type ConnectionStatus = "checking" | "online" | "offline";
type ChatResponse = { session_id?: string; message?: string };

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [connection, setConnection] = useState<ConnectionStatus>("checking");

  useEffect(() => {
    let active = true;
    async function checkBackend() {
      try {
        const response = await fetch("/api/health", { cache: "no-store" });
        if (active) setConnection(response.ok ? "online" : "offline");
      } catch {
        if (active) setConnection("offline");
      }
    }
    checkBackend();
    const timer = window.setInterval(checkBackend, 30_000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setMessages((current) => [...current, { role: "user", text }]);
    setInput("");
    setBusy(true);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      const data = (await response.json().catch(() => ({}))) as ChatResponse;
      if (data.session_id) setSessionId(data.session_id);
      setMessages((current) => [...current, { role: "ai", text: data.message ?? (response.ok ? "Tarefa processada." : "Não foi possível processar a tarefa.") }]);
      if (response.ok) setConnection("online");
    } catch {
      setConnection("offline");
      setMessages((current) => [...current, { role: "ai", text: "Não foi possível conectar ao backend da Yuri Code AI." }]);
    } finally {
      setBusy(false);
    }
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  const statusLabel = connection === "online" ? "● Agente conectado" : connection === "offline" ? "● Backend indisponível" : "● Verificando agente…";

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand"><div className="logo">Y</div><div><strong>Yuri Code AI</strong><span>AI Coding Agent</span></div></div>
        <nav className="nav">
          <button className="active">⌘ Chat</button><button>▣ Projetos</button><button>◫ Arquivos</button><button>⑂ Git</button><button>⚙ Configurações</button>
        </nav>
        <div className="project"><small>PROJETO ATUAL</small><strong>Workspace do agente</strong></div>
      </aside>
      <main className="main">
        <header className="header"><h1>Assistente de programação</h1><span className={`status ${connection}`}>{statusLabel}</span></header>
        <section className="content">
          {messages.length === 0 ? <div className="hero"><h2>O que vamos programar?</h2><p>Descreva uma tarefa. A Yuri Code AI pode pesquisar, criar, editar, executar testes e iterar no projeto conectado.</p></div> : <div className="messages">
            {messages.map((message, index) => <div key={`${message.role}-${index}`} className={`message ${message.role}`}>{message.text}</div>)}
            {busy && <div className="message ai">Agente trabalhando…</div>}
          </div>}
          <form className="composer" onSubmit={sendMessage}>
            <textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleComposerKeyDown} placeholder="Ex.: analise meu projeto, encontre os erros e corrija tudo..." disabled={busy} aria-label="Tarefa para a Yuri Code AI" />
            <div className="composer-footer"><span className="hint">Enter envia • Shift + Enter quebra linha</span><button className="send" type="submit" disabled={busy || !input.trim()}>{busy ? "Executando..." : "Enviar ↑"}</button></div>
          </form>
        </section>
      </main>
    </div>
  );
}