# Yuri Code AI — Runbook de Produção

## Objetivo

Este runbook fecha a preparação operacional do Yuri Code AI sem armazenar credenciais no GitHub.

## Antes de ativar produção

1. Confirmar que o deployment Vercel está **Ready**.
2. Configurar manualmente no Vercel:
   - `YURI_ENV=production`
   - `YURI_API_TOKEN`
   - `LLM_API_KEY`
   - `LLM_MODEL`
   - `DATABASE_URL`
   - `YURI_SANDBOX_MODE=remote`
   - `OPENHANDS_AGENT_SERVER_URL`
   - `OPENHANDS_AGENT_SERVER_API_KEY`
   - `CORS_ORIGINS`, quando necessário.
3. Confirmar que o PostgreSQL/Supabase já recebeu as migrations do diretório `supabase/migrations`.
4. Não configurar `DATABASE_URL`, tokens ou chaves no GitHub.
5. Não usar SQLite nem sandbox local em produção.

## Smoke test

Após configurar as variáveis:

### 1. Liveness

`GET /health`

Esperado:

```json
{"status":"ok","database":"ok"}
```

O endpoint também verifica a existência das tabelas essenciais do schema.

### 2. Readiness

`GET /ready` com Bearer token.

Esperado:

```json
{
  "status": "ready",
  "environment": "production",
  "checks": {
    "database": true,
    "api_token": true,
    "llm": true,
    "sandbox": true,
    "openhands_server": true
  }
}
```

Os valores reais de secrets nunca são retornados.

### 3. Chat autenticado

Enviar uma tarefa simples por `POST /chat` usando Bearer token.

Confirmar:

- resposta HTTP bem-sucedida;
- `conversation_id`/ `session_id` retornado;
- resposta do agente;
- registro da mensagem no PostgreSQL.

### 4. Persistência

Consultar:

`GET /conversations/{conversation_id}/messages`

Confirmar que as mensagens continuam disponíveis em uma nova requisição.

## Falhas esperadas

- `503` em `/health`: banco indisponível ou schema incompleto.
- `503` em `/ready`: deployment vivo, mas alguma dependência obrigatória não está configurada.
- `401`: Bearer token ausente ou inválido.
- `502`: falha do agente durante o processamento.
- `504`: timeout configurado da tarefa foi atingido.

## Segurança

- Nunca colocar secrets em commits, logs ou respostas da API.
- O frontend não recebe `LLM_API_KEY`, `DATABASE_URL` ou credenciais do Agent Server.
- O backend usa token Bearer para as rotas protegidas.
- Em produção, o OpenHands deve executar em sandbox remoto compatível.
- A confirmação humana continua obrigatória quando `YURI_CONFIRMATION_MODE=always` estiver configurado.

## Rollback

Se o smoke test falhar após uma alteração:

1. Não alterar o schema de produção para contornar erro de aplicação.
2. Identificar o deployment Vercel que introduziu a regressão.
3. Fazer rollback pelo histórico de deployments da Vercel.
4. Corrigir em branch separada.
5. Reexecutar CI e smoke test antes de promover novamente.

## Critério de conclusão

A aplicação só deve ser considerada operacionalmente pronta quando:

- CI estiver verde;
- deployment Vercel estiver Ready;
- `/health` retornar banco OK;
- `/ready` retornar ready;
- `POST /chat` autenticado executar uma tarefa;
- a conversa e as mensagens forem persistidas no PostgreSQL;
- nenhuma credencial estiver presente no repositório.
