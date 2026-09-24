# Fase 1 — Hardening e segurança

## Autenticação
Todas as rotas, exceto `/health`, exigem `Authorization: Bearer <YURI_API_TOKEN>`. O token fica somente no backend.

## CORS
Sem `CORS_ORIGINS`, nenhuma origem é autorizada.

## Sandbox
Produção exige `YURI_SANDBOX_MODE=docker` ou `remote`. O modo Docker usa o `DockerWorkspace` do OpenHands; o modo remote conecta a um Agent Server isolado. O modo local é somente para desenvolvimento/testes.

## Segredos
A API não injeta `LLM_API_KEY`, `DATABASE_URL` ou `GITHUB_TOKEN` no ambiente do workspace local. Em produção, segredos do sandbox devem ser administrados pelo Agent Server, não pelo processo da API.

## Guardrails
`YURI_MAX_ITERATIONS`, `YURI_TASK_TIMEOUT_SECONDS` e `YURI_MAX_COST_USD` são opcionais. Vazios significam sem cota artificial da aplicação. Iterações e custo são encaminhados ao OpenHands; o timeout também é aplicado no endpoint.

## Confirmação
`YURI_CONFIRMATION_MODE=always` bloqueia tarefas que já declaram ações destrutivas conhecidas. A UX completa de aprovação de ações emitidas durante a execução ficará para a Fase 3, quando eventos/streaming forem expostos.

## Prompt injection
Páginas web, arquivos, repositórios e saídas de comandos são dados não confiáveis. O prompt de execução instrui o agente a não seguir instruções externas que tentem substituir a tarefa ou exfiltrar segredos.

## Rate limit
`YURI_RATE_LIMIT_PER_MINUTE=0` desliga o limitador. Valor positivo aplica proteção contra abuso por IP/token.
