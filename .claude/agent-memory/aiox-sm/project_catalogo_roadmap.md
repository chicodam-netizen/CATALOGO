---
name: project-catalogo-roadmap
description: Sequência de execução e dependências entre stories do Epic 1 e Epic 6 do Data Catalog & Profiler, definida pelo @pm e formalizada nas stories
metadata:
  type: project
---

O projeto CATALOGO (Data Catalog & Profiler, FD Consultoria) tem PRD brownfield sharded em `docs/prd/`, sem `docs/architecture/` ainda — a única fonte de arquitetura para draftar stories é o próprio epic + leitura direta do código-fonte em `src/`.

Ordem de execução recomendada pelo @pm (Morgan) para desbloquear o roadmap com menor risco, registrada em `docs/prd/README.md` §3: **6.2 → 6.3 → 1.1 → 1.2 → 1.3**.

- **Story 6.2** (dependências não declaradas em `requirements_catalog.txt`) antecipada por ser a mais barata e desbloquear instalação limpa.
- **Story 6.3** (baseline de testes pytest) antecipada para antes da 1.3, pois a vetorização do profiler precisa de rede de segurança para provar equivalência numérica.
- **1.1 → 1.2** têm dependência técnica real: a migração de schema (1.2) é executada "na abertura de todo workspace" (conceito introduzido pela 1.1).
- **1.3** depende tecnicamente de 6.3 (equivalência numérica), mas não tem dependência técnica direta com 1.1/1.2 — a ordem entre elas é gestão de risco, não acoplamento de código.
- **1.3 bloqueia Story 2.1** (Epic 2) explicitamente, conforme o epic.

Todas as 5 stories já foram criadas em `docs/stories/{epic}.{story}.story.md` com este sequenciamento documentado em frontmatter (`sequence`, `dependencies`) e em uma seção `## Dependencies` no corpo de cada story.

**Why:** sem essa ordem registrada, um dev poderia pegar 1.1 antes de 6.2/6.3 e reintroduzir os mesmos riscos que o @pm identificou (ambiente quebrado, refatoração sem rede de teste).

**How to apply:** ao draftar Epics 2-5 (que dependem de Epic 1), verificar se a Story 1.2's "como adicionar migration" (AC8) já está documentada antes de escrever ACs que assumem migração de schema disponível (Stories 2.2, 3.2, 3.3, 4.2, 5.1 dependem disso).
