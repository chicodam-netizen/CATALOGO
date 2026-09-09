---
name: feedback-ac-fidelity
description: Preservar literalmente a redação dos Acceptance Criteria do epic ao draftar stories neste projeto; detalhamento vai em Tasks/Dev Notes, não reescrevendo o AC
metadata:
  type: feedback
---

Ao draftar as stories 1.1, 1.2, 1.3, 6.2 e 6.3, o usuário foi explícito: "Cada story deve conter os Acceptance Criteria já definidos no epic correspondente (não invente novos ACs — extraia e detalhe os que já estão no epic)".

Abordagem aplicada: copiar o texto do AC verbatim do epic (incluindo referências arquivo:linha já levantadas pelo @pm) na seção "Acceptance Criteria" da story, e colocar todo detalhamento adicional (passos técnicos, achados de código verificados, decisões de design) nas seções `Tasks / Subtasks` e `Dev Notes` — nunca reescrevendo ou expandindo o texto do próprio AC.

**Why:** o epic já passou por validação do usuário; reescrever ACs no nível da story criaria divergência de fonte de verdade entre epic e story, e violaria Article IV (No Invention) da Constitution AIOX.

**How to apply:** em qualquer story futura deste projeto (Epics 2-5), sempre copiar os ACs literalmente do arquivo de epic correspondente antes de adicionar qualquer task ou nota técnica. Se um AC parecer incompleto durante o draft, resolver via Dev Notes (achados de código, decisões de implementação) ou sinalizar para o @po/@pm — não editar o AC diretamente na story.
