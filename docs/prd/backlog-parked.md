# Backlog Parado — Out of Scope

**Status:** Congelado (não virar epic, story ou AC)
**Autor:** Morgan (@pm)
**Data:** 2026-09-08
**Revisão obrigatória se:** a decisão de modelo de produto mudar

---

## Por que estes itens estão parados

O modelo de produto confirmado é **ferramenta do consultor** — o catálogo roda na máquina do consultor da FD, durante um engajamento, operado por uma pessoa por vez, sobre uma base de cliente por vez.

Os três itens abaixo só fazem sentido no modelo oposto: **plataforma instalada no cliente**, com múltiplos usuários do cliente operando continuamente, sem o consultor presente. Construí-los agora significaria pagar custo de complexidade (identidade, permissão, estado de aprovação, execução agendada, infraestrutura de notificação) por capacidades que ninguém usaria no modelo atual — e que precisariam ser reprojetadas quando o modelo mudasse, porque hoje não há como validar os requisitos reais.

**Decisão:** ficam registrados aqui, com o gatilho de reativação explícito. Não são backlog "para depois" no sentido de prioridade baixa — são itens **fora do modelo de produto vigente**.

---

## Item 5 — Agendamento e alertas automáticos

**O que seria:** executar profiling periodicamente sem intervenção e notificar responsáveis quando a qualidade degradar.

**Por que está parado:** pressupõe um processo de longa duração rodando no ambiente do cliente, com acesso persistente ao banco e canal de notificação configurado. O app é Streamlit em processo único, iniciado manualmente pelo consultor e encerrado ao fim da sessão. Não existe nada para agendar em cima.

**O que precisaria existir antes:** modelo de produto = plataforma instalada; runtime persistente (serviço/worker) separado da UI; credenciais de banco armazenadas com segurança no ambiente do cliente; canal de notificação definido (e-mail/Teams/Slack); definição de quem responde por cada alerta — o que depende do Item 9.

**Substituto no escopo atual:** o histórico de profiling (Story 3.2) já entrega a capacidade de **comparar** execuções ao longo do tempo. O que fica de fora é apenas o disparo automático.

---

## Item 8 — Workflow de aprovação

**O que seria:** alterações no glossário passariam por um fluxo de submissão → revisão → aprovação antes de virarem oficiais.

**Por que está parado:** um workflow de aprovação exige, no mínimo, dois papéis distintos e autenticados — quem submete e quem aprova. Sem identidade nem permissão (Item 9), o "fluxo" seria a mesma pessoa clicando em aprovar o que ela mesma escreveu: cerimônia sem controle.

**O que precisaria existir antes:** Item 9 (RBAC) concluído; múltiplos usuários reais operando a mesma instância; definição de política de aprovação com o cliente.

**Substituto no escopo atual:** o audit trail (Story 3.3) registra quem mudou o quê e quando, com autoria declarativa. Para um engajamento conduzido pela FD, rastreabilidade posterior cobre a necessidade de evidência de governança sem o custo do workflow.

---

## Item 9 — RBAC leve

**O que seria:** papéis e permissões controlando quem pode ler, editar e aprovar cada parte do catálogo.

**Por que está parado:** não há multiusuário. A ferramenta roda localmente, operada pelo consultor. Introduzir autenticação e autorização adicionaria gestão de identidade, sessão e credenciais a uma aplicação Streamlit local — superfície de segurança nova para proteger contra um adversário que, no modelo atual, não existe.

**O que precisaria existir antes:** modelo de produto = plataforma instalada no cliente; hospedagem com sessão real; decisão sobre provedor de identidade (local vs SSO do cliente); definição de papéis com o cliente.

**Substituto no escopo atual:** os campos de **owner e steward** (Story 2.2) e os papéis **RACI** (Story 4.2) capturam responsabilidade como **informação de governança declarativa**. Está explicitamente documentado nessas stories que tais campos não conferem nenhuma permissão no sistema — a distinção entre "responsável documentado" e "permissão técnica" precisa permanecer nítida para não criar falsa sensação de controle.

---

## Gatilho de reativação

Estes itens voltam à mesa **somente** quando a decisão de modelo de produto mudar de "ferramenta do consultor" para "plataforma instalada no cliente". Se isso ocorrer:

1. A reativação começa obrigatoriamente pelo **Item 9 (RBAC)** — os Itens 5 e 8 dependem dele.
2. A mudança de modelo exige revisão do Epic 1: workspace por cliente foi projetado como fronteira **de dados**, não como fronteira **de tenant**. Em modelo de plataforma, isso precisa ser reavaliado por @architect antes de qualquer story.
3. As decisões de "campo declarativo, sem efeito de permissão" (Stories 2.2, 3.3, 4.2) passam a ser pontos de integração com o modelo de permissão real, não mais notas de escopo.

**Ação até lá:** nenhuma. Não estimar, não rascunhar story, não criar AC parcial "preparando terreno". Escopo parado é escopo parado.
