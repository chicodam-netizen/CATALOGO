---
epic_id: 3
title: Inventário & Tendência de Qualidade - Brownfield Enhancement
status: Draft
priority: P2
depends_on: [1]
recommends: [2.2]
blocks: []
owner: "@pm"
created: 2026-09-08
stories:
  - id: "3.1"
    title: Dashboard de inventário do catálogo
    executor: "@ux-design-expert"
    quality_gate: "@dev"
    quality_gate_tools: [ui_review, accessibility_check, performance_benchmark]
  - id: "3.2"
    title: Histórico de profiling persistido com método de amostragem rastreável
    executor: "@data-engineer"
    quality_gate: "@dev"
    quality_gate_tools: [schema_validation, migration_review, sampling_determinism_test]
  - id: "3.3"
    title: Audit trail de alterações no glossário
    executor: "@data-engineer"
    quality_gate: "@dev"
    quality_gate_tools: [schema_validation, migration_review, transaction_integrity_test]
---

# Epic 3: Inventário & Tendência de Qualidade

## Epic Goal

Dar ao consultor visão agregada do estado do catálogo (o que existe, o que está catalogado, o que está descoberto) e memória ao longo do tempo — tendência de qualidade dos dados e rastro de quem mudou o quê no glossário —, com honestidade estatística sobre o que é comparável e o que não é.

## Epic Description

### Existing System Context

- **Funcionalidade atual relevante:** o app é integralmente **stateless em relação ao tempo**. Cada execução de "Executar Data Discovery" (`src/app.py:64`) sobrescreve `st.session_state['profiling_results']` e nada é persistido. O glossário guarda apenas o estado atual (upsert em `glossary.py:26-50`), sem histórico. Não existe nenhuma visão agregada: a navegação é sempre schema → tabela → coluna.
- **Stack:** Python, Streamlit, pandas, SQLite, openpyxl.
- **Pontos de integração:** `DBManager.fetch_sample_data` (`db_manager.py:27-46`) é a fonte da amostra; `profile_column` produz as métricas; `save_metadata` é o ponto único de escrita no glossário.

### Enhancement Details

- **O que muda:** uma tela de inventário agregado; persistência de snapshots de profiling com o método de amostragem registrado; tabela de histórico de alterações do glossário.
- **Como integra:** todas as tabelas novas entram pela camada de migração (Story 1.2), no metadata store do workspace ativo (Story 1.1). O dashboard consulta o metadata store, não o banco do cliente.
- **Critério de sucesso:** o consultor abre um engajamento e vê, em uma tela, quanto do schema está catalogado; e consegue mostrar ao cliente a evolução de saúde de uma coluna entre duas datas — ou, honestamente, que os dois pontos não são comparáveis.

### Risco central deste epic (R3)

`fetch_sample_data` (`db_manager.py:27-46`) monta `SELECT TOP n` (SQL Server), `FETCH FIRST n ROWS ONLY` (Oracle) ou `LIMIT n` — **sem `ORDER BY` em nenhum dialeto**. Sem ordenação explícita, o SGBD não garante que duas execuções retornem o mesmo conjunto de linhas. Uma "tendência de qualidade" construída sobre amostras não determinísticas mede variação de amostragem, não variação de qualidade — e um gráfico assim entregue a um cliente é pior do que nenhum gráfico. Story 3.2 trata isso como AC bloqueante.

---

## Stories

### Story 3.1 — Dashboard de inventário do catálogo

`executor: @ux-design-expert` · `quality_gate: @dev` · `quality_gate_tools: [ui_review, accessibility_check, performance_benchmark]`

**Descrição:** Tela de visão agregada do workspace: o que existe no schema, quanto está catalogado, quanto está com responsável, quanto tem indício de PII.

**Acceptance Criteria:**

1. Nova tela (novo item no `st.radio` de modo de análise, `app.py:17`) apresenta, por tabela do schema selecionado: número de colunas, % de colunas com nome de negócio, % com descrição, % com classificação LGPD, % com owner (se Story 2.2 concluída), nº de colunas com PII sugerida (se Story 2.1 concluída) e data do último profiling (se Story 3.2 concluída).
2. Métricas de catalogação são lidas do **metadata store do workspace ativo**; a estrutura do schema é lida via `DBManager`. Abrir o dashboard **não dispara profiling** nem leitura de dados do cliente além da introspecção de metadados.
3. Funcionalidades ainda não implementadas aparecem como coluna vazia rotulada ("não disponível"), nunca como zero — zero e "não medido" são coisas diferentes e a UI não pode confundi-los.
4. **Empty state honesto:** workspace novo sem nenhum metadado exibe mensagem explicativa e o próximo passo sugerido, não uma tabela vazia sem contexto.
5. Ordenação e filtro por qualquer coluna de métrica (ex.: "mostrar tabelas com menor cobertura primeiro"), para dirigir o trabalho do consultor.
6. Carregar o dashboard de um schema com 100 tabelas conclui em < 3s, sem varrer dados.
7. Segue o padrão visual Streamlit já estabelecido no app (sidebar para configuração, controles superiores para escopo).
8. Export do inventário em Excel reutiliza o padrão de export existente (`openpyxl`), sem dependência nova.
9. **Regressão:** as telas "Data Discovery & Profiling" e "Análise de Duplicidades" continuam acessíveis e inalteradas.

---

### Story 3.2 — Histórico de profiling persistido com método de amostragem rastreável

`executor: @data-engineer` · `quality_gate: @dev` · `quality_gate_tools: [schema_validation, migration_review, sampling_determinism_test]`

**Descrição:** Persistir cada execução de profiling como um snapshot datado, registrando o método de amostragem usado, para que tendência de qualidade seja estatisticamente defensável. Endereça o risco R3.

**Acceptance Criteria:**

1. Novas tabelas (ex.: `profiling_runs` e `profiling_metrics`) criadas **exclusivamente** pela camada de migração da Story 1.2, no metadata store do workspace ativo.
2. Cada execução de profiling grava um snapshot com: timestamp, workspace, connection identifier (sem credenciais), schema, tabela, coluna, e as métricas produzidas por `profile_column` (`null_pct`, `unique_pct`, `health_valid_pct`, `health_invalid_pct`, `inferred_type`, `total_rows`).
3. **Método de amostragem é registrado em cada snapshot:** `sample_size` solicitado, nº de linhas efetivamente retornadas, dialeto do SGBD, cláusula de limitação usada (TOP/FETCH FIRST/LIMIT), e um flag `sampling_deterministic` (true/false).
4. `fetch_sample_data` (`db_manager.py:27-46`) passa a aplicar **ordenação determinística** quando existe chave estável (PK ou coluna única identificada via `inspector`), definindo `sampling_deterministic = true`. Quando não existe chave estável, a query permanece como está e o snapshot é marcado `sampling_deterministic = false`.
5. A UI de tendência **só compara snapshots com método de amostragem compatível** (mesmo `sample_size`, mesmo dialeto, ambos determinísticos). Snapshots incompatíveis ou não determinísticos aparecem na série com marcação visual explícita e legenda: "amostra não determinística — variação pode refletir amostragem, não qualidade".
6. Gráfico de tendência por coluna (e agregado por tabela) mostrando evolução de `health_valid_pct` e `null_pct` ao longo dos snapshots.
7. Snapshots armazenam **apenas métricas** — nenhum valor de dado do cliente é persistido.
8. Política de retenção configurável (ex.: manter N snapshots por coluna ou snapshots dos últimos M meses), com limpeza executável, para que o metadata store não cresça indefinidamente.
9. Gravar snapshot não pode degradar perceptivelmente o tempo de profiling; escrita em lote, não uma transação por coluna.
10. **Regressão:** o profiling continua funcionando e exibindo resultados na sessão mesmo se a gravação do snapshot falhar (falha de persistência é avisada, não fatal).

---

### Story 3.3 — Audit trail de alterações no glossário

`executor: @data-engineer` · `quality_gate: @dev` · `quality_gate_tools: [schema_validation, migration_review, transaction_integrity_test]`

**Descrição:** Registrar o histórico de alterações do glossário — quem mudou, quando, de quê para quê — como evidência de governança.

**Acceptance Criteria:**

1. Nova tabela `glossary_history` criada pela camada de migração da Story 1.2, no metadata store do workspace ativo.
2. Toda alteração via `save_metadata` (`glossary.py:26-50`) registra: timestamp, workspace, schema, tabela, coluna, campo alterado, valor anterior, valor novo e autor.
3. O autor é a identidade **declarativa** do consultor, informada no workspace (campo simples). Fica explícito na documentação que isso **não é autenticação nem controle de acesso** — RBAC permanece parado (`backlog-parked.md`).
4. Só são registrados campos que efetivamente mudaram; salvar sem alterar nada não gera linha de histórico.
5. A escrita do histórico ocorre na **mesma transação** do upsert: ou grava metadado e histórico, ou não grava nenhum dos dois. AC verificável por teste com falha injetada.
6. Histórico consultável por coluna na UI (ex.: expander "Histórico de alterações" dentro do expander da coluna), em ordem cronológica decrescente.
7. Criação inicial de um registro é distinguível de uma edição posterior (ex.: valor anterior nulo com evento `CREATE`).
8. O comportamento atual do upsert (`ON CONFLICT ... DO UPDATE`) permanece funcionalmente idêntico do ponto de vista do chamador.
9. Política de retenção/limite de crescimento definida, coerente com a da Story 3.2.
10. O dicionário consolidado (Story 2.3) pode incluir opcionalmente a coluna "última alteração" derivada do histórico.

---

## Compatibility Requirements

- [ ] Todas as tabelas novas entram por migration idempotente (Story 1.2); nenhum `CREATE TABLE` novo em `init_db()`.
- [ ] `profile_column` mantém contrato de retorno inalterado; a persistência é responsabilidade da camada chamadora.
- [ ] Alteração em `fetch_sample_data` preserva o comportamento atual para bancos sem chave estável identificável.
- [ ] As duas telas existentes permanecem inalteradas em comportamento.
- [ ] Nenhuma dependência nova sem declaração em `requirements_catalog.txt`.

## Risk Mitigation

- **Primary Risk (R3):** apresentar ao cliente uma "tendência de qualidade" que na verdade mede ruído de amostragem — dano direto de credibilidade do entregável.
- **Mitigation:** ordenação determinística quando possível (3.2 AC4); registro obrigatório do método (3.2 AC3); bloqueio de comparação entre métodos incompatíveis e marcação visual explícita (3.2 AC5).
- **Risco secundário:** crescimento descontrolado do metadata store com snapshots e histórico, degradando a abertura do workspace.
- **Mitigation:** política de retenção em ambas as stories (3.2 AC8, 3.3 AC9); escrita em lote (3.2 AC9).
- **Risco terciário:** falha na gravação de snapshot interromper um profiling em andamento durante uma sessão com o cliente.
- **Mitigation:** 3.2 AC10 — falha de persistência é degradação graciosa, não erro fatal.
- **Rollback Plan:** todas as stories são aditivas (novas tabelas, nova tela). Reverter o código deixa as tabelas órfãs e inertes — nenhum dado existente é alterado ou removido. A única mudança em código existente é o `ORDER BY` em `fetch_sample_data`, revertível isoladamente.

## Quality Gates

| Story | Pre-Commit | Pre-PR | Risco |
|---|---|---|---|
| 3.1 | Revisão de UI e empty states, benchmark de carga | Revisão de integração com metadata store (@dev) | LOW |
| 3.2 | Validação de schema, teste de determinismo de amostragem | Revisão de migration e integridade estatística (@dev) | HIGH |
| 3.3 | Validação de schema, teste de integridade transacional | Revisão de migration e transação (@dev) | MEDIUM |

## Definition of Done

- [ ] As 3 stories concluídas com todos os AC atendidos.
- [ ] Dashboard de inventário funcional com dados reais de um workspace.
- [ ] Dois snapshots de profiling da mesma coluna gerando gráfico de tendência, com o método de amostragem visível.
- [ ] Cenário de amostra não determinística demonstrado com a marcação de aviso correta na UI.
- [ ] Histórico de glossário registrando corretamente CREATE e UPDATE, com teste de rollback transacional passando.
- [ ] Política de retenção documentada e executável.
- [ ] Nenhuma regressão nos fluxos existentes.

## Story Manager Handoff

"Desenvolver as stories detalhadas deste epic brownfield. Considerações:

- Sistema existente: Python + Streamlit + pandas + SQLite; Epic 1 concluído.
- Pontos de integração: `src/core/db_manager.py` (amostragem), `src/core/profiler.py` (métricas), `src/models/glossary.py` (persistência e histórico), `src/app.py` (nova tela e gráficos).
- Padrões existentes a seguir: toda mudança de schema via migration da Story 1.2; UI segue o padrão Streamlit vigente.
- Compatibilidade crítica: `fetch_sample_data` não pode quebrar em bancos sem PK; falha de persistência de snapshot não pode abortar o profiling.
- **Atenção especial:** a Story 3.2 tem um AC de honestidade estatística (determinismo de amostragem). Ele não é opcional nem negociável por conveniência de implementação — é a diferença entre um gráfico defensável e um gráfico enganoso."
