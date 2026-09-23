# Automação GitHub

A Yuri Code AI pode operar um repositório GitHub por meio do Git local e, quando configurado, da API do GitHub.

## Variáveis

- `GITHUB_TOKEN`: token fornecido pelo ambiente de execução; nunca grave o token no repositório.

## Fluxo recomendado

1. Clonar o repositório em um workspace dedicado.
2. Criar uma branch de trabalho.
3. Indexar e analisar o projeto.
4. Implementar as mudanças.
5. Executar quality gate.
6. Criar commit.
7. Fazer push da branch.
8. Criar Pull Request somente quando solicitado/configurado.

As operações locais são feitas por `agent.github_ops`. A criação de Pull Request usa a API oficial do GitHub por `agent.github_workflow`.

A automação não deve sobrescrever trabalho não relacionado sem antes inspecionar o estado do workspace. Tokens e outros segredos devem permanecer nas variáveis de ambiente ou no mecanismo de secrets do ambiente de execução.
