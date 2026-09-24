# Yuri Code AI — Arquitetura de Produção

## Objetivo

Executar o frontend Next.js e a API FastAPI no mesmo projeto Vercel, com o backend consumido internamente pelo frontend, e usar PostgreSQL/Supabase para persistência.

## Componentes

- **Web:** Next.js App Router em `/web`.
- **API do agente:** FastAPI/Python em `/agent`.
- **Banco:** PostgreSQL/Supabase em produção.
- **Pesquisa:** OpenHands/BrowserToolSet e Tavily opcional.
- **GitHub:** integração do agente para operações autorizadas.

## Fluxo

Browser -> Next.js -> `/api/chat` -> binding `BACKEND_INTERNAL_URL` -> FastAPI -> OpenHands/LLM -> PostgreSQL.

O navegador nunca recebe credenciais de LLM, GitHub ou banco.

## Variáveis de produção

### Vercel — frontend/backend

Configure como variáveis privadas do projeto, sem valores no Git:

- `YURI_API_TOKEN`
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_BASE_URL` (se necessário)
- `YURI_ENV=production`
- `YURI_SANDBOX_MODE=remote`
- `OPENHANDS_AGENT_SERVER_URL`
- `OPENHANDS_AGENT_SERVER_API_KEY`
- `DATABASE_URL`
- `CORS_ORIGINS` (domínio oficial, quando necessário)
- `YURI_WORKSPACE`
- `TAVILY_API_KEY` (opcional)
- `YURI_MAX_ITERATIONS`, `YURI_TASK_TIMEOUT_SECONDS`, `YURI_MAX_COST_USD` conforme os limites desejados.

`BACKEND_INTERNAL_URL` é criado pelo binding do Vercel Services e não deve ser digitado manualmente.

## Banco

SQLite é permitido somente para desenvolvimento local. Produção exige PostgreSQL/Supabase. O endpoint `/health` testa também a conectividade do banco e informa `database=ok` ou `database=degraded`.

## Sandbox do agente

`YURI_SANDBOX_MODE=local` não é aceito para produção. Para executar o OpenHands em produção, use um Agent Server remoto compatível e configure `OPENHANDS_AGENT_SERVER_URL` e `OPENHANDS_AGENT_SERVER_API_KEY`.

## Migração PostgreSQL\n\nO baseline SQL em `supabase/migrations/20260924000000_initial_schema.sql` reproduz o schema persistido pelo backend. Aplique-o uma vez no PostgreSQL/Supabase de produção antes do teste de persistência. Não coloque a `DATABASE_URL` no repositório.\n\n## Validação antes de produção

1. CI verde.
2. Deployment Vercel Ready.
3. Variáveis privadas configuradas.
4. PostgreSQL/Supabase acessível pelo backend.
5. `GET /health` retorna `status=ok` e `database=ok`.
6. Teste autenticado de `POST /chat`.
7. Teste de persistência: criar uma conversa e confirmar que mensagens permanecem após nova requisição.
8. Só então promover o deployment para produção.

## Readiness e observabilidade

- `GET /health` é o health check público de liveness e testa a conexão PostgreSQL.
- `GET /ready` exige Bearer token e verifica dependências necessárias para operar o agente.
- O readiness retorna somente indicadores booleanos (`true/false`), nunca valores de secrets.
- Em produção, o readiness também exige sandbox `docker` ou `remote`; no modo `remote`, exige `OPENHANDS_AGENT_SERVER_URL`.
- Um `503` em `ready` significa que o deployment está vivo, mas ainda não está apto a processar tarefas.

## Segurança

- Nunca commitar `.env`, tokens, chaves ou URLs com credenciais.
- Nunca expor `LLM_API_KEY`, credenciais do GitHub ou `DATABASE_URL` ao browser.
- Restringir CORS.
- Manter o workspace do agente isolado.
- Em produção, não usar SQLite nem sandbox local.
