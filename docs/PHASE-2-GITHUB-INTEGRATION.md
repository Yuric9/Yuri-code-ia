# Fase 2 — Integração GitHub

A Fase 2 adiciona uma camada explícita para operações autorizadas no GitHub sem expor credenciais ao navegador.

## Regras

- GITHUB_TOKEN permanece somente no ambiente do backend/agente.
- O token nunca deve ser colocado em código, URLs, logs ou respostas do agente.
- O trabalho deve ocorrer em branch própria; main/master são bloqueadas pela camada de integração.
- Pull Requests são criados pela API oficial do GitHub e sempre apontam para uma branch de trabalho.
- O repositório é validado como owner/repo antes de qualquer operação.
- A criação de PR exige GITHUB_TOKEN.
- O workspace continua separado por conversa e sujeito às proteções da Fase 1.

## Fluxo

1. Receber owner/repo ou URL GitHub.
2. Validar repositório e branch base.
3. Preparar/usar workspace isolado.
4. Trabalhar em branch própria.
5. Executar testes e quality gate.
6. Criar commit.
7. Fazer push da branch.
8. Criar PR somente quando solicitado/configurado.

A integração não faz push direto para main/master.
