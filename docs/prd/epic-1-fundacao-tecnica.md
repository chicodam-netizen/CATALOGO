---
epic_id: 1
title: Fundação Técnica (Workspace, Migração, Performance) - Brownfield Enhancement
status: Draft
priority: P0
blocking: true
depends_on: []
blocks: [2, 3, 4, 5]
owner: "@pm"
created: 2026-09-08
stories:
  - id: "1.1"
    title: Segregar o metadata store por workspace/cliente
    executor: "@dev"
    quality_gate: "@architect"
    quality_gate_tools: [code_review, pattern_validation, data_isolation_review]
  - id: "1.2"
    title: Migração idempotente de schema no metadata store
    executor: "@data-engineer"
    quality_gate: "@dev"
    quality_gate_tools: [schema_validation, migration_review, idempotency_test]
  - id: "1.3"
    title: Vetorizar o profiler para viabilizar varredura de schema
    executor: "@dev"
    quality_gate: "@architect"
    quality_gate_tools: [code_review, performance_benchmark, regression_test]
---

# Epic 1: Fundação Técnica (Workspace, Migração, Performance)

## Epic Goal

Tornar o metadata store seguro e evolutivo antes de empilhar qualquer funcionalidade de governança sobre ele: isolar metadados por cliente/engajamento, permitir evolução de schema sem quebrar bases existentes, e eliminar o gargalo de performance que inviabiliza varreduras de schema inteiro.

## Epic Description

### Existing System Context

- **Funcionalidade atual relevante:** o app persiste o glossário de negócios em SQLite local através de `src/models/glossary.py`, com tabela única `glossary` (PK composta schema/table/column). O profiling roda por tabela selecionada, coluna a coluna (`src/app.py:61-82`).
- **Stack:** Python, Streamlit (processo único), SQLAlchemy, pandas, SQLite, openpyxl.
- **Pontos de integração:** `app.py` importa `save_metadata`/`get_all_metadata` de `glossary.py`; `profile_column` é chamado em loop sobre `df.columns` em `app.py:72-76`; `DBManager` é instanciado a partir da connection string informada na sidebar (`app.py:22-34`).

### Problemas concretos que este epic resolve

1. **Ausência de fronteira por cliente.** `DB_FILE = 'metadata.db'` (`glossary.py:4`) é um caminho relativo fixo ao diretório de execução. Todo engajamento de consultoria escreve no mesmo arquivo: nomes de negócio, descrições, classificação LGPD e — depois do Epic 2 — o mapa de PII de qualquer cliente analisado ficam misturados. Pior, `sqlite:///metadata.db` também é a connection string default da **fonte analisada** (`app.py:24`), o que confunde repositório de metadados com objeto de análise.
2. **Schema imutável na prática.** `init_db()` (`glossary.py:6-24`) só executa `CREATE TABLE IF NOT EXISTS`. Em uma base já criada, adicionar coluna não tem efeito: a tabela existe, o CREATE é ignorado, e o código novo quebra em runtime ou grava errado, silenciosamente. Todos os epics seguintes adicionam colunas ou tabelas.
3. **Profiler não escala para descoberta.** `profile_column` itera valor a valor em Python puro (`profiler.py:59`) sobre até 50.000 linhas por coluna (`app.py:56`). Hoje isso já é lento em uma tabela; a partir do Epic 2 (descoberta de PII por conteúdo em todas as colunas de todas as tabelas) trava o app.

### Enhancement Details

- **O que muda:** resolução de caminho do metadata store por workspace; camada de migração versionada; validação vetorizada no profiler com sub-amostragem específica para modo discovery.
- **Como integra:** mantém a API pública de `glossary.py` (`save_metadata`, `get_metadata`, `get_all_metadata`) e a assinatura de `profile_column`, para não forçar reescrita de `app.py` além da seleção de workspace e do parâmetro de amostra.
- **Critério de sucesso:** dois engajamentos distintos coexistem sem contaminação; uma base `metadata.db` legada abre e migra sem perda; profiling de coluna de 50k linhas roda em < 2s.

---

## Stories

### Story 1.1 — Segregar o metadata store por workspace/cliente

`executor: @dev` · `quality_gate: @architect` · `quality_gate_tools: [code_review, pattern_validation, data_isolation_review]`

**Descrição:** Substituir o caminho fixo `metadata.db` por um metadata store resolvido a partir de um workspace (cliente/engajamento) ativo, selecionado explicitamente pelo consultor, com diretório-raiz configurável e higiene de repositório garantida.

**Acceptance Criteria:**

1. Existe uma função única de resolução de caminho (ex.: `resolve_metadata_db_path(workspace)`); nenhum módulo referencia mais o literal `'metadata.db'` — `src/models/glossary.py:4` deixa de expor um caminho fixo relativo ao diretório de execução.
2. O app permite selecionar ou criar um workspace na sidebar **antes** de qualquer operação de glossário; o workspace ativo é mantido em `st.session_state` e exibido de forma persistente na interface.
3. Cada workspace grava em arquivo próprio sob um diretório de dados configurável (ex.: `data/workspaces/{workspace_slug}/metadata.db`), com o diretório-raiz sobrescrevível por variável de ambiente (ex.: `CATALOG_DATA_DIR`), sem hardcode de caminho absoluto.
4. Nenhuma escrita de glossário ocorre sem workspace ativo: a ausência de workspace bloqueia "Salvar Metadados" (`app.py:117-123`) com mensagem explícita, em vez de gravar em um arquivo default.
5. `init_db()` deixa de ser executado no import do módulo (`glossary.py:98`). A inicialização passa a ser explícita e vinculada ao workspace resolvido — importar o módulo não pode mais criar arquivo no diretório de execução.
6. A connection string default do app (`app.py:24`, hoje `sqlite:///metadata.db`) deixa de apontar para o mesmo arquivo do metadata store. O campo de conexão passa a representar exclusivamente a **fonte analisada**; o metadata store é independente dela.
7. Migração do `metadata.db` legado existente na raiz: procedimento documentado (importar para um workspace nomeado) e executado sem perda de nenhum registro da tabela `glossary`; contagem de linhas antes/depois conferida.
8. **Higiene de repositório:** o `.gitignore` cobre o novo diretório de workspaces. Hoje `CATALOGO/.gitignore:10` ignora apenas o literal `metadata.db` na raiz (o arquivo atual, verificado, **não** está rastreado); a regra precisa acompanhar o novo layout para que metadados e mapa de PII de cliente não passem a ser versionados. Validar com `git check-ignore -v` no novo caminho.
9. **Regressão:** o fluxo atual ponta a ponta (conectar → selecionar schema/tabela → Executar Data Discovery → salvar metadados → reabrir e ver metadados salvos → exportar Excel) continua funcional com um workspace selecionado.
10. Documentado o que é e o que não é workspace: é fronteira de dados por cliente/engajamento; **não** é conta de usuário, permissão ou tenant — RBAC segue fora de escopo (ver `backlog-parked.md`).

---

### Story 1.2 — Migração idempotente de schema no metadata store

`executor: @data-engineer` · `quality_gate: @dev` · `quality_gate_tools: [schema_validation, migration_review, idempotency_test]`

**Descrição:** Introduzir versionamento e migração idempotente do schema SQLite, de forma que qualquer story futura possa adicionar colunas/tabelas sem quebrar bases `metadata.db` já existentes. Endereça o risco R11.

**Acceptance Criteria:**

1. Existe uma função de migração (ex.: `migrate_db(conn)`) executada na abertura de todo workspace, com versão persistida via `PRAGMA user_version` ou tabela `schema_version` dedicada.
2. A migração é **idempotente**: executá-la N vezes consecutivas produz exatamente o mesmo schema, sem erro e sem efeito colateral.
3. A migração se aplica a bases legadas criadas pelo `init_db()` atual (`glossary.py:6-24`, schema sem versionamento) sem perda de dados — incluindo o `metadata.db` hoje presente na raiz do projeto.
4. Adição de coluna usa `ALTER TABLE ... ADD COLUMN` com verificação prévia via `PRAGMA table_info`. É **proibido** `DROP TABLE` ou recriação de `glossary` como estratégia de evolução.
5. Cada execução registra em log a versão de origem, a versão de destino e as migrations aplicadas.
6. Falha de migração aborta a abertura do workspace com mensagem acionável e **não deixa a base em estado parcialmente migrado** (migração dentro de transação, com rollback em erro).
7. Testes automatizados cobrem no mínimo: (a) base nova criada do zero, (b) base legada em schema v0 sem versionamento, (c) reexecução sobre base já migrada (idempotência), (d) falha simulada com verificação de rollback.
8. Existe documentação curta de "como adicionar uma nova migration", referenciada pelas stories dependentes (2.2, 3.2, 3.3, 4.2, 5.1).
9. **Regressão:** `save_metadata`, `get_metadata` e `get_all_metadata` continuam com o mesmo contrato e comportamento após a migração.

---

### Story 1.3 — Vetorizar o profiler para viabilizar varredura de schema

`executor: @dev` · `quality_gate: @architect` · `quality_gate_tools: [code_review, performance_benchmark, regression_test]`

**Descrição:** Substituir a validação valor a valor em Python puro por operações vetorizadas em pandas, e separar o tamanho de amostra de "análise" do tamanho de amostra de "descoberta". Endereça o risco R1 e é pré-requisito da Story 2.1.

**Acceptance Criteria:**

1. `profile_column` (`src/core/profiler.py:59`) não itera mais valor a valor em Python puro para os tipos `cpf`, `cnpj`, `email`, `phone` e `text`: a validação passa a operar de forma vetorizada (`pandas .str` + regex pré-compilada) sobre a Series.
2. As contagens (`Válido` / `Inválido` / `Outros`) e os campos `health_valid_pct` / `health_invalid_pct` permanecem numericamente equivalentes à implementação atual sobre um dataset de referência congelado; qualquer divergência exige justificativa registrada e aceite explícito no quality gate.
3. Regras que não são expressáveis em regex — notadamente o dígito verificador de CPF/CNPJ em `src/validators/docs_br.py` — executam **apenas sobre o subconjunto que passou no pré-filtro de formato**, nunca sobre a coluna inteira.
4. Existe um parâmetro explícito de sub-amostra para o **modo discovery** (default entre 1.000 e 5.000 valores por coluna), separado e independente do `sample_size` de análise (`app.py:56`, default 50.000).
5. Benchmark registrado (antes/depois) para cada tipo inferido sobre coluna de 50.000 linhas. Meta: profiling de uma coluna de 50k em **< 2s**.
6. Perfilar todas as colunas de uma tabela larga (>= 30 colunas × 50k linhas) conclui sem congelar a UI, com indicador de progresso visível ao usuário.
7. **Regressão:** o gráfico de saúde (`app.py:88`) e a exportação Excel (`app.py:125-139`) continuam funcionando com o mesmo conjunto e nomes de colunas retornados por `profile_column`.
8. Nenhuma dependência nova é introduzida sem ser declarada em `requirements_catalog.txt` (ver Story 6.2).
9. Os validadores em `src/validators/` são **reutilizados ou adaptados**, não substituídos por implementação paralela (IDS: REUSE > ADAPT > CREATE). Se uma reimplementação vetorizada for necessária, ela e o validador escalar devem compartilhar a mesma fonte de verdade (mesmo padrão/regra), com teste que prova a equivalência.

---

## Compatibility Requirements

- [ ] A API pública de `src/models/glossary.py` (`save_metadata`, `get_metadata`, `get_all_metadata`) mantém assinaturas compatíveis; mudanças são aditivas (parâmetros opcionais).
- [ ] Bases `metadata.db` existentes são migradas, nunca descartadas nem recriadas.
- [ ] `profile_column` mantém a chave e o tipo de todos os campos hoje retornados em `stats`.
- [ ] A UI mantém o padrão Streamlit existente (sidebar para configuração, controles superiores para escopo, expanders por coluna).
- [ ] Nenhuma mudança de comportamento na tela de Duplicidades.

## Risk Mitigation

- **Primary Risk:** a refatoração do profiler (1.3) altera silenciosamente os percentuais de saúde já usados em entregáveis de cliente, corroendo a confiança no relatório.
- **Mitigation:** dataset de referência congelado + teste de equivalência numérica como AC bloqueante (1.3 AC2); Story 6.3 (baseline de testes) antecipada para antes da 1.3.
- **Risco secundário:** a introdução de workspace quebra o caminho do `metadata.db` legado e o consultor perde o glossário já preenchido.
- **Mitigation:** 1.1 AC7 exige migração verificada por contagem de linhas antes/depois; backup manual do arquivo antes da execução.
- **Rollback Plan:** as três stories são commits independentes e revertíveis. O metadata store legado é um arquivo único — basta preservar cópia de `metadata.db` antes da 1.1 para voltar ao estado anterior. A 1.3 é isolada em `profiler.py` e reverte sem tocar em dados.

## Quality Gates

| Story | Pre-Commit | Pre-PR | Risco |
|---|---|---|---|
| 1.1 | Revisão de isolamento de dados, verificação de `.gitignore` | Revisão de arquitetura de storage (@architect) | MEDIUM |
| 1.2 | Validação de schema, teste de idempotência | Revisão de migration + rollback (@dev) | HIGH |
| 1.3 | Benchmark + teste de equivalência numérica | Revisão de performance e regressão (@architect) | HIGH |

## Definition of Done

- [ ] As 3 stories concluídas com todos os AC atendidos.
- [ ] Dois workspaces distintos coexistem, com metadados comprovadamente isolados.
- [ ] Base `metadata.db` legada migrada sem perda, com evidência de contagem.
- [ ] Benchmark de profiling documentado (antes/depois), meta < 2s por coluna de 50k atingida.
- [ ] Nenhuma regressão nos fluxos existentes de Profiling e Duplicidades.
- [ ] `.gitignore` verificado contra o novo layout de dados.
- [ ] Documentação de "como adicionar migration" publicada e referenciada pelos epics dependentes.

## Story Manager Handoff

"Desenvolver as stories detalhadas deste epic brownfield. Considerações:

- Sistema existente: Python + Streamlit (single-process) + SQLAlchemy + pandas + SQLite.
- Pontos de integração: `src/models/glossary.py` (metadata store), `src/core/profiler.py` (profiling), `src/app.py` (UI e orquestração).
- Padrões existentes a seguir: validadores em `src/validators/` devem ser reutilizados; UI segue o padrão sidebar + controles superiores + expanders.
- Compatibilidade crítica: API de `glossary.py` estável, bases legadas migradas e não recriadas, campos de `profile_column` preservados.
- Cada story deve incluir verificação explícita de que o fluxo existente permanece intacto.

Este epic é **bloqueante**: os Epics 2 a 5 não devem entrar em desenvolvimento antes da conclusão das Stories 1.1 e 1.2."
