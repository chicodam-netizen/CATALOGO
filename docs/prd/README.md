# Data Catalog & Profiler — PRD Brownfield (Índice / Roadmap)

**Projeto:** Data Catalog & Profiler (FD Consultoria)
**Tipo:** Brownfield enhancement — primeira entrada do projeto no fluxo AIOX
**Autor:** Morgan (@pm)
**Data:** 2026-09-08
**Status:** Draft — aguardando revisão do usuário antes do handoff para @sm

---

## 1. Modelo de Produto (decisão estratégica que governa todo o escopo)

> **O catálogo é uma FERRAMENTA DO CONSULTOR, não uma plataforma instalada no cliente.**

Consequências diretas no roadmap:

| Consequência | Impacto |
|---|---|
| Não há multiusuário concorrente no mesmo ambiente | RBAC e workflow de aprovação saem do roadmap (ver §5 — Parked) |
| Não há operação contínua no ambiente do cliente | Agendamento/alertas automáticos saem do roadmap (ver §5) |
| O mesmo binário/instalação atende **vários clientes** | **Segregação de dados por workspace/cliente vira requisito de fundação** (Epic 1) |
| O entregável é um artefato (dicionário, relatório), não um portal | Exportação consolidada é feature de topo de ROI (Epic 2, Story 2.3) |

---

## 2. Contexto do Sistema Existente (compartilhado por todos os epics)

**Stack:** Python + Streamlit (UI single-process), SQLAlchemy (conexão à fonte analisada), pandas, SQLite (metadata store local), openpyxl (export Excel).

**Estrutura real:**

| Arquivo | Responsabilidade | Observação relevante ao roadmap |
|---|---|---|
| `src/app.py` | UI Streamlit, 2 telas (Discovery/Profiling, Duplicidades) | `app.py:24` usa `sqlite:///metadata.db` como connection string default; `app.py:56` default de amostra = 50.000 linhas |
| `src/core/db_manager.py` | Conexão e introspecção via SQLAlchemy `inspect()` | `fetch_sample_data` (linhas 27-46) usa LIMIT/TOP **sem ORDER BY** |
| `src/core/profiler.py` | Profiling estatístico + validação por coluna | `profile_column` valida **valor a valor em loop Python** (linha 59) |
| `src/core/deduplicator.py` | Duplicidades exatas + fuzzy (TF-IDF) | matriz de similaridade **N×N completa** (linha 35); código morto na linha 69 |
| `src/models/glossary.py` | Metadata store SQLite (tabela `glossary`) | `DB_FILE = 'metadata.db'` fixo (linha 4); `init_db()` roda no import (linha 98); só `CREATE TABLE IF NOT EXISTS` (linhas 6-24) |
| `src/validators/*.py` | CPF, CNPJ, e-mail, telefone, texto livre | Ativos reutilizáveis — reuso antes de criar (IDS: REUSE > ADAPT > CREATE) |

**Estado de qualidade atual:** zero testes automatizados em `src/`; `requirements_catalog.txt` declara 5 pacotes e **não declara** `scikit-learn`, `numpy` e `rapidfuzz` — todos importados por `deduplicator.py:1-5`.

**Nota de precisão (verificado em 2026-09-08):** o arquivo `metadata.db` existe na raiz do projeto mas **não está rastreado pelo git** — `CATALOGO/.gitignore:10` já ignora o literal `metadata.db` e a linha anterior ignora `*.db`. O risco real, portanto, **não** é "arquivo versionado hoje", e sim: (a) um único arquivo compartilhado misturando metadados e mapa de PII de todos os clientes analisados, e (b) a regra de ignore está amarrada a um nome fixo na raiz — qualquer mudança de layout sem atualizar o `.gitignore` passa a versionar dados de cliente. Ambos são tratados na Story 1.1.

---

## 3. Ordem de Execução dos Epics

```
Epic 1 (FUNDAÇÃO — bloqueia todos os demais)
   ├─> Epic 2  Descoberta de Dados Sensíveis & Entregável
   ├─> Epic 3  Inventário & Tendência de Qualidade
   ├─> Epic 4  Relacionamentos & Governança de Processos
   └─> Epic 5  Qualidade Contínua

Epic 6 (Débito Técnico) — paralelizável; ver recomendação de antecipação abaixo
```

| # | Epic | Arquivo | Stories | Depende de | Prioridade |
|---|------|---------|---------|-----------|-----------|
| 1 | Fundação Técnica (Workspace, Migração, Performance) | [epic-1-fundacao-tecnica.md](epic-1-fundacao-tecnica.md) | 3 | — | **P0 — bloqueante** |
| 2 | Descoberta de Dados Sensíveis & Entregável | [epic-2-descoberta-dados-sensiveis.md](epic-2-descoberta-dados-sensiveis.md) | 3 | Epic 1 | P1 |
| 3 | Inventário & Tendência de Qualidade | [epic-3-inventario-tendencia-qualidade.md](epic-3-inventario-tendencia-qualidade.md) | 3 | Epic 1 (2.2 recomendado) | P2 |
| 4 | Relacionamentos & Governança de Processos | [epic-4-relacionamentos-governanca-processos.md](epic-4-relacionamentos-governanca-processos.md) | 2 | Epic 1 | P3 |
| 5 | Qualidade Contínua (leve) | [epic-5-qualidade-continua.md](epic-5-qualidade-continua.md) | 1 | Epic 1 (1.2 e 1.3) | P4 |
| 6 | Débito Técnico de Plataforma | [epic-6-debito-tecnico-plataforma.md](epic-6-debito-tecnico-plataforma.md) | 3 | — | P2 (parcial, ver nota) |
| — | Backlog Parado (Out of Scope) | [backlog-parked.md](backlog-parked.md) | 3 itens | Mudança de modelo de produto | Congelado |

**Recomendação estratégica sobre o Epic 6 (não é sequenciamento rígido, é gestão de risco):**

- **Story 6.2 (dependências não declaradas) deve ser antecipada para junto do Epic 1.** É a única story do backlog inteiro cujo custo é de minutos e cuja ausência quebra uma instalação limpa — inclusive a de um dev novo entrando no Epic 1.
- **Story 6.3 (baseline de testes) deve ser antecipada para antes da Story 1.3.** A vetorização do profiler é uma refatoração de comportamento numérico; sem rede de teste, a equivalência de resultados vira promessa em vez de verificação.
- **Story 6.1 (escalabilidade do deduplicator)** pode aguardar — é risco real (MemoryError), mas está em tela isolada e tem mitigação temporária trivial (limitar amostra).

---

## 4. Mapa Item Candidato → Epic/Story

| # Item original | Descrição | Destino |
|---|---|---|
| 12 | Dicionário de dados consolidado | Story 2.3 |
| 7 | Ownership / stewardship | Story 2.2 |
| 1 | PII por conteúdo | Story 2.1 |
| 4 | Histórico de profiling | Story 3.2 |
| 6 | Histórico de alterações no glossário | Story 3.3 |
| 2 | Dashboard de inventário | Story 3.1 |
| 10 | Mapa de relacionamentos / ER | Story 4.1 |
| 3 | Regras de qualidade customizáveis | Story 5.1 |
| 11 | Governança de processos | Story 4.2 |
| 8 | Workflow de aprovação | **Parked** |
| 9 | RBAC leve | **Parked** |
| 5 | Agendamento / alertas | **Parked** |

---

## 5. Out of Scope / Parked

Ver [backlog-parked.md](backlog-parked.md). Resumo: itens 5, 8 e 9 dependem da decisão de modelo de produto mudar de "ferramenta do consultor" para "plataforma instalada no cliente". Não devem virar epic, story ou AC até que essa decisão mude explicitamente.

---

## 6. Rastreabilidade de Riscos Técnicos → Acceptance Criteria

Nenhum risco identificado na revisão de código pode ficar sem endereço formal. Mapa:

| Risco | Origem no código | Endereçado em |
|---|---|---|
| R1 — Performance do profiler (loop Python) | `profiler.py:59` + `app.py:56` | Story 1.3 (AC1-AC6), pré-requisito da 2.1 |
| R11 — Sem migração de schema | `glossary.py:6-24` | Story 1.2 (todos os AC) |
| R3 — Amostragem sem ORDER BY | `db_manager.py:27-46` | Story 3.2 (AC3-AC5) |
| R7 — Mapa de relacionamentos vazio | Modelo dimensional sem FK física | Story 4.1 (AC3-AC5) |
| R8 — Governança de processos 100% manual | Nenhum dado derivável do banco | Story 4.2 (AC1-AC4) |
| R9 — Regras customizáveis = RCE/ReDoS | Superfície nova | Story 5.1 (AC2-AC6) |
| Débito — deduplicator N×N + código morto | `deduplicator.py:35,69` | Story 6.1 |
| Débito — dependências não declaradas | `requirements_catalog.txt` | Story 6.2 |
| Débito — zero testes | `src/` | Story 6.3 |
| Segregação/vazamento de metadados de cliente | `glossary.py:4`, `app.py:24`, `.gitignore:10` | Story 1.1 |

---

## 7. Próximo Passo

1. Usuário revisa e aprova os 6 epics + backlog parado.
2. `@po *validate` (opcional) para checagem de consistência de backlog.
3. `@sm *draft` para rascunhar as stories completas do **Epic 1** (mais 6.2 e 6.3 se a antecipação for aceita).
4. Stories vão para `docs/stories/` no padrão `{epicNum}.{storyNum}.story.md`.

— Morgan, planejando o futuro
