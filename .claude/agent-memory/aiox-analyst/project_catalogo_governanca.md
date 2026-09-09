---
name: catalogo-governanca-produto
description: O app Streamlit em CATALOGO/src e ferramenta interna da FD Consultoria para diagnostico de governanca de dados/processos em clientes — nao e produto SaaS
metadata:
  type: project
---

O "Data Catalog & Profiler" (`src/app.py`) e usado pela FD Consultoria como **ferramenta de consultor** para acelerar diagnosticos e produzir entregaveis (dicionario de dados, inventario de PII, matriz dado-processo) em programas de governanca nos clientes.

**Why:** o ROI do produto vem de (1) acelerar as primeiras semanas do engajamento, (2) produzir artefatos que o cliente paga para receber, (3) reduzir horas manuais do consultor — nao de operar uma plataforma continua.

**How to apply:** ao priorizar funcionalidades, features que pressupoem o app rodando 24/7 dentro do cliente (agendamento/alertas, RBAC, workflow de aprovacao) valem menos do que features de diagnostico e de exportacao de entregavel, ate que exista decisao explicita sobre o fork de modelo: "ferramenta de consultor" vs "plataforma instalada no cliente". Essa decisao ainda estava em aberto em 2026-09-08 e deve ser resolvida antes de investir no Tema B (qualidade continua) e no C9 (RBAC).

Contexto tecnico relevante a decisoes de escopo: o store de metadados e um SQLite unico e hardcoded (`metadata.db`), sem separacao por cliente e sem migracoes — multi-cliente e pre-requisito nao resolvido.
