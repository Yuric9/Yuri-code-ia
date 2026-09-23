# Yuri Code AI

Agente de IA para programação, desenvolvido por Yuri.

## Objetivo

A Yuri Code AI é um agente de programação com autonomia para pesquisar na internet, entender projetos, criar e editar código, executar comandos, testar, corrigir erros e continuar iterando até concluir uma tarefa.

## Capacidades atuais

- **Programação:** leitura, criação, edição e organização de arquivos.
- **Execução:** terminal, instalação de dependências, testes e comandos de desenvolvimento.
- **Pesquisa web:** navegador integrado para pesquisar sites, documentação, GitHub e outras fontes públicas.
- **Pesquisa adicional:** integração opcional com Tavily para buscas estruturadas e conteúdo extraído.
- **Memória persistente:** SQLite por padrão ou PostgreSQL configurável.
- **Banco de dados:** projetos, conversas, mensagens, memórias e histórico de pesquisas.
- **Iteração:** pode pesquisar, implementar, testar, analisar falhas e corrigir novamente.

## Política de capacidade

Não existe quota diária, mensal ou por conversa implementada pela Yuri Code AI. Também não existe um limite artificial de arquivos, pesquisas ou número de iterações por tarefa.

Isso **não** significa burlar limites externos. Modelo de IA, APIs, navegador, hospedagem, sistema operacional, serviços de terceiros e contas utilizadas podem possuir limites técnicos, de segurança ou de cobrança. A aplicação não adiciona uma quota própria por cima desses limites.

## Base tecnológica

O motor usa o **OpenHands Software Agent SDK**, que permite agentes de programação com ferramentas, workspaces e ferramentas personalizadas. O SDK também possui integração de navegador para navegar, interagir com páginas e extrair conteúdo. citeturn1search1turn3view0

## Banco e memória

O banco é inicializado automaticamente quando o agente inicia.

Por padrão:

`./data/yuri_ai.db` (desenvolvimento local; produção deve usar PostgreSQL/Supabase via `DATABASE_URL`).

Para produção, configure `DATABASE_URL` com PostgreSQL. A camada de persistência já separa:

- projetos;
- conversas;
- mensagens;
- memórias por escopo/chave;
- histórico de pesquisas e fontes.

## Pesquisa na internet

A Yuri Code AI pode usar o `BrowserToolSet` do OpenHands para navegar diretamente na web. Isso permite que o próprio agente decida quando pesquisar, visite várias páginas e extraia informações. citeturn3view0

Também existe uma camada opcional com Tavily. Ela não impõe limite dentro da aplicação e registra os resultados no banco. O provedor externo, naturalmente, aplica seus próprios créditos e limites de conta. A API do Tavily oferece busca, extração e pesquisa aprofundada. citeturn0search0turn0search2

## Configuração rápida

1. Copie `config/.env.example` para `.env`.
2. Configure `LLM_API_KEY` e `LLM_MODEL`.
3. Instale as dependências base com `pip install .` e, para executar o agente OpenHands, use `pip install ".[agent]"`. Para desenvolvimento/testes, use `pip install ".[test]"`.
4. Defina `YURI_WORKSPACE` para o projeto que a IA poderá trabalhar.
5. Opcionalmente configure `TAVILY_API_KEY`.
6. Execute `yuri-code-ai`.

## Princípio

A Yuri Code AI deve entender antes de alterar, pesquisar quando necessário, implementar de forma completa, testar o resultado e continuar corrigindo quando encontrar problemas.
