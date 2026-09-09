---
name: project-modelo-produto-catalogo
description: Data Catalog & Profiler é ferramenta do consultor FD, não plataforma instalada no cliente — decisão que congela RBAC, aprovação e agendamento
metadata:
  type: project
---

O **Data Catalog & Profiler** (`D:\FD_CONSULTORIA\DESENVOLVIMENTO\CATALOGO`) é uma **ferramenta do consultor da FD Consultoria**, executada localmente durante engajamentos de governança de dados/processos — **não** é uma plataforma instalada no ambiente do cliente. Decisão confirmada pelo usuário em 2026-09-08.

**Why:** o app é Streamlit em processo único, operado por uma pessoa por vez, sobre uma base de cliente por vez. Não há multiusuário nem operação contínua no cliente. Construir identidade/permissão/agendamento agora seria pagar complexidade por capacidades sem usuário real, que precisariam ser reprojetadas se o modelo mudasse.

**How to apply:**
- Itens **parados** (não virar epic, story ou AC): RBAC leve, workflow de aprovação, agendamento/alertas automáticos. Detalhes e gatilho de reativação em `docs/prd/backlog-parked.md`.
- Substitutos aceitos no escopo atual: owner/steward e RACI como **campos declarativos sem efeito de permissão**; audit trail no lugar de workflow de aprovação; histórico de profiling no lugar de alertas automáticos.
- Consequência positiva do modelo: como a mesma instalação atende **vários clientes**, a segregação de metadados por workspace/cliente é requisito de fundação (Epic 1, Story 1.1), não feature.
- Se o usuário sinalizar mudança para "plataforma instalada no cliente", a reativação começa obrigatoriamente por RBAC e exige revisão do Epic 1 por @architect (workspace foi projetado como fronteira de dados, não de tenant).

Relacionado: [[project-roadmap-prd-catalogo]]
