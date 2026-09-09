---
name: project-roadmap-prd-catalogo
description: Roadmap do Data Catalog em 6 epics sharded em docs/prd/, com Epic 1 bloqueante e riscos técnicos convertidos em AC explícitos
metadata:
  type: project
---

O PRD brownfield do Data Catalog & Profiler está sharded em `docs/prd/` (padrão `epic-{n}*.md` do `.aiox-core/core-config.yaml`), criado em 2026-09-08 pelo @pm. Índice: `docs/prd/README.md`. Status: Draft, aguardando revisão do usuário antes de `@sm *draft`.

Ordem: Epic 1 (Fundação: workspace, migração, performance) → 2 (PII + ownership + dicionário) → 3 (inventário + histórico) → 4 (relacionamentos + processos) → 5 (regras de qualidade). Epic 6 (débito técnico) é paralelizável.

**Why:** Epic 1 é bloqueante por dois motivos duros verificados no código — `glossary.py` só faz `CREATE TABLE IF NOT EXISTS` (qualquer coluna nova em base existente é ignorada silenciosamente) e o profiler valida valor a valor em Python puro sobre 50k linhas (varredura de schema trava o app). Nenhuma story de feature que toque glossário ou profiling pode preceder isso.

**How to apply:**
- Ao propor qualquer story nova, verificar se ela adiciona coluna/tabela: se sim, ela depende da Story 1.2 (migração idempotente) e o AC de migração é obrigatório.
- Riscos de código viram **AC explícito**, nunca nota de rodapé. Tabela de rastreabilidade risco→AC está na §6 do `docs/prd/README.md`.
- Recomendação já registrada ao usuário: antecipar Story 6.2 (dependências não declaradas) para junto do Epic 1, e Story 6.3 (baseline de testes) para antes da Story 1.3.
- Correção factual importante: `metadata.db` **não** está rastreado pelo git (já coberto por `.gitignore`). O risco real é arquivo único compartilhado entre clientes, não versionamento. Não repetir a premissa errada.

Relacionado: [[project-modelo-produto-catalogo]]
