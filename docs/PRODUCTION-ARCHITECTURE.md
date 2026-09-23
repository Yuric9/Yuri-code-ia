# Yuri Code AI — Arquitetura de Produção

## Objetivo

Separar claramente a interface web, a API do agente e a persistência, evitando acoplamento entre o deploy Next.js e o processo Python de longa duração.

## Componentes

- **Web:** Next.js App Router em \`/web\`, hospedado na Vercel.
- **API do agente:** FastAPI/Python em \`/agent\`. Deve ser hospedada em um runtime Python persistente/compatível com o SDK do agente.
- **Banco:** PostgreSQL/Supabase em produção.
- **Pesquisa:** BrowserToolSet/OpenHands e Tavily opcional.
- **GitHub:** integração do agente para operações autorizadas no repositório.

## Fluxo

Browser -> Next.js -> \`/api/chat\` -> FastAPI -> OpenHands/LLM -> ferramentas -> PostgreSQL.

O navegador não deve acessar diretamente credenciais de LLM, GitHub ou banco.

## Variáveis essenciais

### Vercel

- \`YURI_AGENT_API_URL\`: URL pública da API Python.
- Variáveis públicas devem ser usadas somente quando realmente destinadas ao browser; a URL acima é consumida pelo Route Handler do Next.js.

### Backend

- \`LLM_API_KEY\`
- \`LLM_MODEL\`
- \`DATABASE_URL\`
- \`CORS_ORIGINS\`
- \`YURI_WORKSPACE\`
- \`TAVILY_API_KEY\` (opcional)

## Banco

SQLite é permitido somente para desenvolvimento local. Produção deve usar PostgreSQL/Supabase e \`DATABASE_URL\`.

## Deploy

1. Validar Python e TypeScript.
2. Executar testes.
3. Criar preview da Web.
4. Validar \`/api/chat\` contra a API Python.
5. Configurar PostgreSQL/Supabase.
6. Validar health check e persistência.
7. Somente depois promover para produção.

## Segurança

- Nunca commitar \`.env\`, tokens ou chaves.
- Nunca expor \`LLM_API_KEY\`, credenciais do GitHub ou \`DATABASE_URL\` no cliente.
- Restringir \`CORS_ORIGINS\` em produção.
- O workspace do agente deve ser explicitamente configurado e isolado.
