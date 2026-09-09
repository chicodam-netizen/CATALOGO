---
epic_id: 4
title: Relacionamentos & Governança de Processos - Brownfield Enhancement
status: Draft
priority: P3
depends_on: [1]
blocks: []
owner: "@pm"
created: 2026-09-08
stories:
  - id: "4.1"
    title: Mapa de relacionamentos entre tabelas com fallback heurístico
    executor: "@dev"
    quality_gate: "@architect"
    quality_gate_tools: [code_review, pattern_validation, empty_state_review]
  - id: "4.2"
    title: Módulo de Governança de Processos com import de planilha
    executor: "@dev"
    quality_gate: "@architect"
    quality_gate_tools: [code_review, import_validation, schema_review]
---

# Epic 4: Relacionamentos & Governança de Processos

## Epic Goal

Ampliar o catálogo de "colunas isoladas" para "modelo de dados com relacionamentos", e estender a governança para além dos dados — processos e responsabilidades (RACI) — com um caminho de adoção realista: importar o que a FD já mantém em Excel, em vez de exigir digitação do zero.

## Epic Description

### Existing System Context

- **Funcionalidade atual relevante:** o `DBManager` já instancia o inspector do SQLAlchemy (`src/core/db_manager.py:8`) e expõe `get_schemas`, `get_tables` e `get_columns` — mas **não existe nenhum método de leitura de chaves estrangeiras** hoje, e nenhuma visão de relacionamento. Não há absolutamente nada de governança de processos no sistema.
- **Stack:** Python, Streamlit, SQLAlchemy (inspector), pandas, SQLite, openpyxl.
- **Pontos de integração:** `DBManager` (introspecção), metadata store do workspace (persistência), `app.py` (novas telas).

### Enhancement Details

- **O que muda:** leitura de FKs declaradas com fallback heurístico e visualização do modelo; novo módulo de processos alimentado por import de planilha, com vínculo opcional aos ativos de dados do catálogo.
- **Como integra:** o mapa de relacionamentos estende o `DBManager`; o módulo de processos usa tabelas novas via migration (Story 1.2) no workspace ativo, e `openpyxl` — já declarado — para o import.
- **Critério de sucesso:** o consultor consegue apresentar o modelo do cliente (mesmo sem FK física declarada, com a devida ressalva) e carregar uma matriz de processos/RACI existente em minutos, não em horas de digitação.

### Riscos centrais deste epic

**R7 — O mapa pode vir legitimamente vazio.** `inspector.get_foreign_keys` só retorna chaves estrangeiras **fisicamente declaradas** no banco. Os artefatos presentes no próprio repositório (`profiling_Dim_Cliente.xlsx`, `profiling_Dim_Produto.xlsx`, `profiling_Fato_Vendas.xlsx`) indicam modelagem dimensional — padrão em que FKs frequentemente não são declaradas fisicamente. Um mapa vazio sem explicação será lido como bug ou como "o cliente não tem relacionamentos", e ambas as leituras são falsas.

**R8 — Governança de processos não tem fonte de dados derivável.** Nenhuma informação de processo existe no banco analisado. Sem import, o módulo depende 100% de digitação manual, e a probabilidade de adoção real em um engajamento cai drasticamente.

---

## Stories

### Story 4.1 — Mapa de relacionamentos entre tabelas com fallback heurístico

`executor: @dev` · `quality_gate: @architect` · `quality_gate_tools: [code_review, pattern_validation, empty_state_review]`

**Descrição:** Descobrir e visualizar relacionamentos entre tabelas do schema, distinguindo com clareza o que é declarado no banco do que é inferido por heurística. Endereça o risco R7.

**Acceptance Criteria:**

1. `DBManager` ganha um método de leitura de chaves estrangeiras usando o inspector já instanciado (`db_manager.py:8`), com tratamento de exceção para dialetos ou permissões que não suportem a introspecção — falha de introspecção não pode derrubar a tela.
2. Relacionamentos **declarados** (FK física) são apresentados como fonte primária, com rótulo explícito de origem "declarado no banco".
3. **Fallback heurístico (R7):** quando nenhuma FK é encontrada, o sistema oferece — como ação opt-in do usuário, nunca automática e silenciosa — inferência por convenção de nomenclatura (ex.: coluna `cliente_id` em `Fato_Vendas` ↔ coluna homônima/PK em `Dim_Cliente`), com score de confiança por candidato.
4. Todo relacionamento inferido é visualmente **inequivocamente distinto** do declarado (rótulo "inferido", estilo de linha diferente, coluna de origem no export). Em nenhuma tela, export ou relatório um relacionamento inferido pode ser apresentado como FK real.
5. **Estado vazio honesto:** quando não há FK declarada e a heurística não é executada ou não encontra candidatos, a tela exibe a explicação — "nenhum relacionamento declarado fisicamente neste schema; isso é comum em modelos dimensionais e não significa ausência de relacionamento" — junto com a oferta de rodar a heurística. Tela vazia sem explicação é falha de AC.
6. Visualização do modelo (diagrama ou tabela de arestas) legível para schema com ao menos 30 tabelas; se um diagrama for usado, deve haver fallback tabular.
7. Nenhuma dependência pesada nova de renderização é introduzida sem declaração em `requirements_catalog.txt` e aprovação no quality gate; preferir recursos nativos do Streamlit ou saída Mermaid/DOT em texto.
8. O consultor pode **confirmar ou rejeitar** um relacionamento inferido, e a decisão é persistida no metadata store do workspace (via migration da Story 1.2), com autoria e data.
9. Exportação do mapa (arestas com origem declarado/inferido/confirmado) em Excel, reutilizando o padrão de export existente.
10. Introspecção de FKs de um schema com 100 tabelas conclui sem leitura de dados de negócio (apenas metadados).

---

### Story 4.2 — Módulo de Governança de Processos com import de planilha

`executor: @dev` · `quality_gate: @architect` · `quality_gate_tools: [code_review, import_validation, schema_review]`

**Descrição:** Criar o módulo de governança de processos tendo o import de planilha como caminho principal de entrada de dados, e a digitação manual como complemento. Endereça o risco R8.

**Acceptance Criteria:**

1. **Import de planilha é entregue nesta primeira story do tema**, não postergado: o módulo aceita `.xlsx` (via `openpyxl`, já declarado) contendo matriz de processos e/ou RACI, que é o formato que a FD já utiliza.
2. Existe um **template de planilha versionado no repositório** (colunas esperadas documentadas), baixável pela UI, para reduzir atrito de preparação.
3. O import apresenta **mapeamento de colunas guiado**: o usuário associa colunas da planilha aos campos do modelo, com sugestão automática por similaridade de nome; o import não assume cegamente a ordem das colunas.
4. **Validação antes da gravação:** o import gera relatório prévio com linhas aceitas e linhas rejeitadas (com o motivo de cada rejeição). A gravação é tudo-ou-nada por lote — **nunca importação parcial silenciosa**.
5. Tabelas de processo (ex.: `processes`, `process_raci`, `process_data_assets`) criadas exclusivamente via migration da Story 1.2, no metadata store do workspace ativo.
6. **Re-import é idempotente por chave de processo:** reimportar uma planilha corrigida atualiza os registros existentes (upsert) em vez de duplicar. A chave de identificação do processo é explícita e documentada.
7. Vínculo **opcional** entre processo e ativo de dados do catálogo (schema/tabela/coluna) — a ponte entre governança de processos e governança de dados. O vínculo é opcional para não bloquear a carga inicial.
8. Edição e criação manual de processos continuam possíveis na UI, seguindo o padrão de formulário já usado no glossário.
9. Export dos processos (incluindo RACI e vínculos com dados) em Excel, reutilizando o padrão existente.
10. Papéis RACI são campos **declarativos**; não conferem nenhuma permissão no sistema — workflow de aprovação e RBAC seguem parados (`backlog-parked.md`).
11. Planilha malformada, vazia ou com aba inexistente produz mensagem acionável, nunca stack trace na tela.

---

## Compatibility Requirements

- [ ] Todas as tabelas novas entram por migration idempotente (Story 1.2).
- [ ] Nenhuma alteração de comportamento nas telas de Profiling e Duplicidades.
- [ ] Métodos existentes de `DBManager` permanecem com assinatura e comportamento inalterados; a leitura de FKs é aditiva.
- [ ] Falha de introspecção de FK degrada graciosamente (mensagem), sem derrubar a aplicação.
- [ ] Nenhuma dependência nova sem declaração em `requirements_catalog.txt`.

## Risk Mitigation

- **Primary Risk (R7):** relacionamento inferido por heurística ser confundido com FK real e ser levado para dentro de um documento de arquitetura entregue ao cliente.
- **Mitigation:** distinção visual e de dados obrigatória (4.1 AC4); heurística sempre opt-in (4.1 AC3); confirmação humana persistida com autoria (4.1 AC8).
- **Risco secundário (R8):** módulo de processos entregue e nunca usado, por exigir digitação manual completa.
- **Mitigation:** import de planilha como AC1 da própria story, não como incremento futuro; template versionado (4.2 AC2); mapeamento guiado (4.2 AC3).
- **Risco terciário:** import parcial corromper a base de processos no meio de um engajamento.
- **Mitigation:** validação prévia com relatório e gravação tudo-ou-nada (4.2 AC4); idempotência no re-import (4.2 AC6).
- **Rollback Plan:** ambas as stories são aditivas (novo método, novas telas, novas tabelas). Reverter o código deixa as tabelas inertes. Nenhum dado pré-existente é alterado.

## Quality Gates

| Story | Pre-Commit | Pre-PR | Risco |
|---|---|---|---|
| 4.1 | Revisão de estados vazios e distinção declarado/inferido | Revisão de arquitetura de introspecção (@architect) | MEDIUM |
| 4.2 | Validação de import (rejeição, idempotência, atomicidade) | Revisão de schema e contrato do template (@architect) | MEDIUM |

## Definition of Done

- [ ] As 2 stories concluídas com todos os AC atendidos.
- [ ] Mapa demonstrado nos três cenários: FK declarada presente; nenhuma FK com estado vazio explicado; heurística executada com relacionamentos rotulados como inferidos.
- [ ] Import de planilha demonstrado com uma matriz de processo real da FD (ou anonimizada), incluindo caso de linha rejeitada e caso de re-import idempotente.
- [ ] Template de planilha versionado no repositório e acessível pela UI.
- [ ] Nenhuma regressão nos fluxos existentes.

## Story Manager Handoff

"Desenvolver as stories detalhadas deste epic brownfield. Considerações:

- Sistema existente: Python + Streamlit + SQLAlchemy + pandas + SQLite; Epic 1 concluído.
- Pontos de integração: `src/core/db_manager.py` (inspector já instanciado na linha 8, leitura de FK a ser adicionada), metadata store do workspace, `src/app.py` (novas telas).
- Padrões existentes a seguir: import/export via `openpyxl`; formulários seguindo o padrão do glossário; toda mudança de schema via migration da Story 1.2.
- Compatibilidade crítica: heurística de relacionamento nunca pode ser apresentada como FK declarada; import nunca pode gravar parcialmente.
- **Atenção especial:** a Story 4.1 tem alta probabilidade de encontrar zero FKs declaradas (modelo dimensional). O estado vazio explicado e o fallback heurístico são o núcleo da story, não um caso de borda."
