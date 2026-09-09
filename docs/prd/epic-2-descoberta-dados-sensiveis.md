---
epic_id: 2
title: Descoberta de Dados Sensíveis & Entregável - Brownfield Enhancement
status: Draft
priority: P1
depends_on: [1]
blocks: []
owner: "@pm"
created: 2026-09-08
stories:
  - id: "2.1"
    title: Descoberta de PII por conteúdo (não apenas por nome de coluna)
    executor: "@dev"
    quality_gate: "@architect"
    quality_gate_tools: [code_review, performance_benchmark, privacy_review]
  - id: "2.2"
    title: Ownership e stewardship no glossário
    executor: "@data-engineer"
    quality_gate: "@dev"
    quality_gate_tools: [schema_validation, migration_review, backward_compatibility_test]
  - id: "2.3"
    title: Exportação de dicionário de dados consolidado do schema
    executor: "@dev"
    quality_gate: "@architect"
    quality_gate_tools: [code_review, output_contract_validation, performance_benchmark]
---

# Epic 2: Descoberta de Dados Sensíveis & Entregável

## Epic Goal

Transformar o catálogo no principal ativo de um engajamento de governança: descobrir dados sensíveis pelo **conteúdo** real (não só pelo nome da coluna), atribuir responsáveis nomeados a cada dado, e produzir o dicionário consolidado que é o entregável final para o cliente.

## Epic Description

### Existing System Context

- **Funcionalidade atual relevante:** a inferência de tipo é feita exclusivamente por nome de coluna em `infer_validation_type` (`src/core/profiler.py:9-20` — procura `cpf`, `cnpj`, `email`, `telefone`/`celular`/`phone`). A classificação LGPD é um selectbox 100% manual (`src/app.py:111`). A exportação Excel é escopada **a uma única tabela** por vez (`app.py:125-139`).
- **Stack:** Python, Streamlit, pandas, SQLite, openpyxl.
- **Pontos de integração:** `profile_column` retorna `inferred_type`; `glossary.py` persiste `classification`; `app.py` monta o export mesclando `df_results` com `get_all_metadata`.

### Enhancement Details

- **O que muda:** detecção de PII baseada em amostragem de conteúdo com score de confiança; novos campos de responsabilidade no glossário; exportação schema-wide com medida de cobertura.
- **Como integra:** a detecção por conteúdo reaproveita a infraestrutura vetorizada entregue na Story 1.3 e os validadores de `src/validators/`. Os novos campos de ownership entram por migration (Story 1.2). O export consolidado generaliza o export existente em vez de criar um caminho paralelo.
- **Critério de sucesso:** o consultor consegue, em uma sessão, apontar quais colunas contêm PII com justificativa quantitativa, quem responde por cada dado, e entregar um dicionário do schema inteiro com percentual de cobertura declarado.

### Dependência bloqueante

Este epic **não** pode iniciar antes de Epic 1, Stories 1.1 (workspace), 1.2 (migração) e 1.3 (vetorização). Rodar descoberta de PII sobre todas as colunas de todas as tabelas com o profiler atual trava o app; adicionar colunas de ownership sem migração corrompe bases existentes; e gravar mapa de PII no `metadata.db` compartilhado é exatamente o vazamento que a Story 1.1 previne.

---

## Stories

### Story 2.1 — Descoberta de PII por conteúdo

`executor: @dev` · `quality_gate: @architect` · `quality_gate_tools: [code_review, performance_benchmark, privacy_review]`

**Descrição:** Detectar dados pessoais analisando o conteúdo amostrado de cada coluna, com score de confiança, sem depender de convenção de nomenclatura.

**Acceptance Criteria:**

1. A descoberta por conteúdo executa sobre a **sub-amostra do modo discovery** definida na Story 1.3 (AC4), nunca sobre 50.000 valores por coluna.
2. Existem detectores por conteúdo para, no mínimo: CPF, CNPJ, e-mail, telefone, CEP, cartão de crédito e data de nascimento — implementados de forma vetorizada (regex pré-compilada) com validação de dígito aplicada apenas ao subconjunto que passou no pré-filtro de formato.
3. Cada coluna recebe um **score de confiança** por detector: percentual de valores da amostra que casam com o padrão. A classificação só é **sugerida** acima de um limiar configurável (default 60%); abaixo disso o sinal é registrado mas não sugerido.
4. A sugestão automática **nunca sobrescreve** a classificação LGPD salva manualmente (`app.py:111`). O consultor aceita ou rejeita a sugestão, e a origem do valor (`inferido` vs `manual`) é persistida no glossário.
5. O nome da coluna continua sendo sinal complementar (`infer_validation_type`, `profiler.py:9-20`), mas o conteúdo prevalece quando divergem; a divergência é exibida explicitamente ao consultor (ex.: coluna `observacao` contendo 78% de e-mails).
6. **Privacidade:** nenhum valor bruto de PII é persistido no metadata store, gravado em log ou incluído em export. Apenas contagens, percentuais, flags e nomes de coluna. AC verificável por inspeção do conteúdo do banco após uma execução.
7. A varredura de schema inteiro é **opt-in**, cancelável, e apresenta estimativa de tempo antes de iniciar; a varredura da tabela selecionada continua sendo o caminho padrão.
8. Toda escrita ocorre no metadata store do workspace ativo (Story 1.1); sem workspace ativo, a descoberta pode rodar mas não pode persistir.
9. Benchmark registrado: varredura de descoberta em schema com 20 tabelas × 30 colunas conclui em tempo documentado e sem congelar a UI.

---

### Story 2.2 — Ownership e stewardship no glossário

`executor: @data-engineer` · `quality_gate: @dev` · `quality_gate_tools: [schema_validation, migration_review, backward_compatibility_test]`

**Descrição:** Adicionar responsáveis nomeados (data owner e data steward) ao glossário, com cobertura mensurável, sem quebrar bases existentes.

**Acceptance Criteria:**

1. Novas colunas em `glossary` (ex.: `data_owner`, `data_owner_contact`, `data_steward`, `updated_at`, `updated_by`) são adicionadas **exclusivamente** via a camada de migração da Story 1.2 — nunca por alteração do `CREATE TABLE` em `init_db()`.
2. A migração é idempotente e aplicável a bases legadas: registros existentes ganham os campos vazios, sem erro e sem perda.
3. Registros legados sem owner **não quebram** `get_metadata` / `get_all_metadata` nem a renderização em `app.py:91,127`; campos ausentes se comportam como string vazia.
4. `save_metadata` (`glossary.py:26-50`) é estendido de forma que o upsert **preserve campos não enviados** — salvar pelo formulário de glossário não pode zerar `data_owner` gravado em outro fluxo. AC verificável por teste: gravar owner, depois salvar apenas descrição, e conferir que owner permanece.
5. Owner e steward são editáveis na UI junto aos demais campos do glossário, seguindo o padrão de expander por coluna já existente.
6. Validação leve de contato: se o contato do owner for e-mail, ele é validado **reutilizando** `src/validators/email_val.py` (IDS: REUSE); e-mail inválido gera aviso, não bloqueio.
7. Existe um indicador de **cobertura de ownership**: percentual de colunas catalogadas com owner definido, por tabela e por schema.
8. Ownership entra no export do dicionário (Story 2.3) como coluna de primeira classe.
9. Fica explicitamente documentado que owner/steward são campos **declarativos de governança**, sem qualquer efeito de permissão ou controle de acesso — RBAC segue parado (ver `backlog-parked.md`).

---

### Story 2.3 — Exportação de dicionário de dados consolidado do schema

`executor: @dev` · `quality_gate: @architect` · `quality_gate_tools: [code_review, output_contract_validation, performance_benchmark]`

**Descrição:** Gerar o entregável central do engajamento: um dicionário de dados do schema inteiro, mesclando metadados de negócio, perfil técnico, sensibilidade e responsabilidade, com cobertura declarada honestamente.

**Acceptance Criteria:**

1. A exportação passa a ser **schema-wide** (hoje é escopada a uma única tabela em `app.py:125-139`), preservando o export por tabela como opção.
2. O documento consolidado inclui, por linha: schema, tabela, coluna, tipo nativo, nome de negócio, descrição, domínio de valores, classificação LGPD, origem da classificação (inferida/manual), PII sugerida e confiança (Story 2.1), owner e steward (Story 2.2), e métricas de perfil (`null_pct`, `unique_pct`, `health_valid_pct`).
3. Tabelas e colunas **sem** metadados preenchidos aparecem no documento com as lacunas visíveis — nunca omitidas. O dicionário reporta a realidade do catálogo, não uma versão filtrada dela.
4. O cabeçalho do documento apresenta **métricas de cobertura**: % de colunas com nome de negócio, % com descrição, % com classificação, % com owner, e data do último profiling considerado.
5. Formato primário `.xlsx` via `openpyxl` (já declarado em `requirements_catalog.txt`); formato secundário em Markdown ou CSV é opcional e não pode introduzir dependência nova.
6. O nome do arquivo gerado identifica workspace/cliente e data (ex.: `dicionario_{workspace}_{YYYY-MM-DD}.xlsx`), evitando entregar ao cliente A um arquivo com nome genérico gerado sobre dados do cliente B.
7. Gerar o dicionário de um schema com 50 tabelas não estoura memória: a montagem é incremental (por tabela), não um único DataFrame gigante em memória.
8. A exportação **não exige** reprofiling completo: usa os metadados persistidos e, quando disponível, o último snapshot de profiling (Story 3.2). Sem snapshot, o documento indica "perfil não disponível" na coluna correspondente em vez de falhar.
9. **Regressão:** o botão de export atual da tela de Profiling continua funcionando com o mesmo comportamento.

---

## Compatibility Requirements

- [ ] Toda alteração de schema passa pela camada de migração da Story 1.2 (nenhum `CREATE TABLE` novo em `init_db()`).
- [ ] `profile_column` mantém os campos existentes; campos de PII são **aditivos**.
- [ ] Classificação LGPD manual existente prevalece sobre qualquer inferência.
- [ ] Export por tabela continua disponível e inalterado no comportamento.
- [ ] Nenhuma dependência nova sem declaração em `requirements_catalog.txt`.

## Risk Mitigation

- **Primary Risk:** vazamento de dados do cliente — gravar amostras de PII no metadata store ou entregar um dicionário com nome de arquivo/conteúdo cruzado entre clientes.
- **Mitigation:** 2.1 AC6 proíbe persistência de valor bruto e é verificável por inspeção do banco; 2.3 AC6 força identificação de workspace no artefato; Epic 1 Story 1.1 garante o isolamento físico.
- **Risco secundário:** falso positivo de PII levando o cliente a classificar erroneamente um dado (risco reputacional do entregável).
- **Mitigation:** score de confiança sempre exposto (2.1 AC3), sugestão nunca auto-aplicada (2.1 AC4), divergência nome × conteúdo exibida (2.1 AC5).
- **Risco terciário:** degradação de performance ao varrer schema inteiro.
- **Mitigation:** dependência dura da Story 1.3; sub-amostra de discovery; varredura opt-in e cancelável (2.1 AC7).
- **Rollback Plan:** as três stories são aditivas. Reverter 2.1 e 2.3 é remoção de código sem efeito sobre dados. Reverter 2.2 exige apenas ignorar as colunas adicionadas — a migração nunca remove nem reescreve dados existentes.

## Quality Gates

| Story | Pre-Commit | Pre-PR | Risco |
|---|---|---|---|
| 2.1 | Revisão de privacidade (nenhum valor bruto persistido), benchmark | Revisão de arquitetura de detecção (@architect) | HIGH |
| 2.2 | Validação de schema, teste de compatibilidade retroativa | Revisão de migration e upsert (@dev) | MEDIUM |
| 2.3 | Validação do contrato de saída, benchmark de memória | Revisão de escalabilidade do export (@architect) | MEDIUM |

## Definition of Done

- [ ] As 3 stories concluídas com todos os AC atendidos.
- [ ] Descoberta de PII por conteúdo demonstrada em coluna cujo nome não denuncia o conteúdo.
- [ ] Inspeção do metadata store confirma ausência de qualquer valor de PII persistido.
- [ ] Cobertura de ownership visível e correta em um workspace de teste.
- [ ] Dicionário consolidado gerado para um schema completo, com métricas de cobertura no cabeçalho.
- [ ] Nenhuma regressão nos fluxos de Profiling, glossário e export por tabela.

## Story Manager Handoff

"Desenvolver as stories detalhadas deste epic brownfield. Considerações:

- Sistema existente: Python + Streamlit + pandas + SQLite; Epic 1 já concluído (workspace, migração, profiler vetorizado).
- Pontos de integração: `src/core/profiler.py` (detecção), `src/models/glossary.py` (persistência), `src/app.py` (UI e export).
- Padrões existentes a seguir: validadores de `src/validators/` são reutilizados, não reimplementados; toda mudança de schema passa pela migração da Story 1.2.
- Compatibilidade crítica: classificação manual prevalece sobre inferida; nenhum valor de PII persistido; export por tabela preservado.
- Cada story deve incluir verificação de que o fluxo existente permanece intacto."
