---
epic_id: 5
title: Qualidade Contínua (leve) - Brownfield Enhancement
status: Draft
priority: P4
depends_on: [1]
hard_prereq_stories: ["1.2", "1.3"]
blocks: []
owner: "@pm"
created: 2026-09-08
stories:
  - id: "5.1"
    title: Regras de qualidade customizáveis por coluna (conjunto fechado e seguro)
    executor: "@dev"
    quality_gate: "@architect"
    quality_gate_tools: [code_review, security_scan, redos_test, performance_benchmark]
---

# Epic 5: Qualidade Contínua (leve)

## Epic Goal

Permitir que o consultor expresse regras de qualidade específicas do cliente ("este campo só aceita este domínio", "este valor precisa estar entre X e Y") sem transformar o app em uma superfície de execução de código arbitrário nem em um alvo trivial de negação de serviço.

## Epic Description

### Existing System Context

- **Funcionalidade atual relevante:** a validação hoje é **fixa e fechada em código**. `infer_validation_type` (`src/core/profiler.py:9-20`) escolhe entre `cpf`, `cnpj`, `email`, `phone` e `text` por nome de coluna, e `profile_column` despacha para os validadores de `src/validators/`. Não existe nenhuma forma de o usuário definir uma regra própria. O único parâmetro configurável no app é o tamanho da amostra (`app.py:56`) e o threshold de similaridade na tela de duplicidades (`app.py:156`).
- **Stack:** Python, Streamlit, pandas, SQLite.
- **Arquitetura relevante ao risco:** Streamlit executa em **processo único**. Qualquer computação que trave o processo — regex catastrófica, loop longo, código do usuário — congela a aplicação inteira para a sessão, no meio de uma apresentação ao cliente.

### Enhancement Details

- **O que muda:** um construtor de regras baseado em um **conjunto fechado de operadores**, persistido por workspace e por coluna, cujo resultado alimenta as métricas de saúde e o dicionário consolidado.
- **Como integra:** regras persistidas via migration (Story 1.2); avaliação vetorizada reutilizando a infraestrutura da Story 1.3; resultado somado ao `stats` retornado pelo profiling.
- **Critério de sucesso:** o consultor define uma regra de domínio específica do cliente pela UI, ela é avaliada junto ao profiling, e nenhuma entrada possível nessa UI consegue executar código ou travar o app.

### Risco central deste epic (R9)

Regras customizáveis são, por definição, entrada do usuário que vira execução. Dois modos de falha, ambos graves:

1. **RCE.** Permitir expressão Python livre (`eval`, `exec`, `DataFrame.query` com string do usuário, `pandas.eval`) entrega execução de código arbitrário ao app — que roda na máquina do consultor, com acesso à connection string do cliente.
2. **ReDoS.** Permitir regex livre sem limite de tempo permite que um padrão catastrófico (ex.: `(a+)+$`) sobre uma coluna de 50k valores trave o processo único do Streamlit indefinidamente. Não é preciso má-fé — um consultor colando um regex de internet basta.

Ambos são tratados como AC bloqueantes na Story 5.1.

---

## Stories

### Story 5.1 — Regras de qualidade customizáveis por coluna (conjunto fechado e seguro)

`executor: @dev` · `quality_gate: @architect` · `quality_gate_tools: [code_review, security_scan, redos_test, performance_benchmark]`

**Descrição:** Construtor de regras de qualidade por coluna com operadores pré-definidos, avaliação vetorizada e contenção rígida da superfície de execução.

**Acceptance Criteria:**

1. As regras são construídas a partir de um **conjunto fechado e enumerado de operadores**, definido em código, com parâmetros tipados. Conjunto mínimo: `not_null`, `unique`, `in_domain` (lista de valores), `not_in_domain`, `between` (numérico), `length_between`, `date_between`, `matches_pattern` (ver AC4 e AC5). Qualquer operador novo exige alteração de código e passagem por quality gate — não é extensível em runtime pelo usuário.
2. **Proibição de execução arbitrária (bloqueante):** é vedado o uso de `eval`, `exec`, `compile`, `pandas.eval`, `DataFrame.query` ou qualquer avaliador de expressão sobre string fornecida pelo usuário, em qualquer ponto do caminho de avaliação de regras. Verificação: revisão de código no quality gate + teste automatizado que tenta submeter uma expressão Python como parâmetro de regra e verifica que ela é **rejeitada na validação da regra**, não avaliada.
3. Os parâmetros de cada regra são validados por tipo e por faixa antes da persistência; parâmetro inválido é rejeitado na criação da regra, com mensagem clara, e nunca chega à etapa de avaliação.
4. **Regex (bloqueante):** o operador `matches_pattern` opera preferencialmente sobre um **catálogo de padrões pré-aprovados** (ex.: CEP, placa, código interno), selecionável em lista. O catálogo é a experiência padrão da UI.
5. Se regex livre for habilitada, ela é tratada como recurso de risco explícito e exige **todas** as contenções a seguir: (a) limite máximo de tamanho do padrão; (b) rejeição de construções reconhecidamente catastróficas (quantificador aninhado, backtracking exponencial) na validação; (c) execução com **deadline obrigatório** — via engine com timeout nativo (ex.: módulo `regex`) ou execução isolada em processo/thread com cancelamento; (d) ao estourar o deadline, a regra é automaticamente **desabilitada e sinalizada na UI**, e a aplicação continua responsiva. Teste automatizado com padrão catastrófico conhecido comprova que o app não congela.
6. Nenhuma avaliação de regra roda de forma bloqueante e ilimitada no thread da UI: existe limite de tempo por regra e por execução, com feedback de progresso e possibilidade de cancelamento.
7. Regras são persistidas por workspace, schema, tabela e coluna, via migration da Story 1.2. Regras de um workspace não vazam para outro.
8. A avaliação é **vetorizada**, reutilizando a infraestrutura da Story 1.3; não é aceitável iterar valor a valor em Python.
9. O resultado das regras compõe as métricas de saúde da coluna e aparece no dicionário consolidado (Story 2.3), distinguindo "regra padrão do sistema" de "regra customizada do cliente".
10. Regras podem ser desabilitadas sem serem excluídas, e o histórico de criação/alteração de regra registra autor e data (coerente com a Story 3.3).
11. **Regressão:** colunas sem regra customizada continuam com o comportamento de profiling atual, inalterado.

---

## Compatibility Requirements

- [ ] Tabelas de regras entram por migration idempotente (Story 1.2).
- [ ] `profile_column` mantém os campos existentes; métricas de regra são aditivas.
- [ ] Colunas sem regras customizadas produzem exatamente o mesmo resultado de antes.
- [ ] Nenhuma dependência nova sem declaração em `requirements_catalog.txt` (inclui eventual engine de regex com timeout).
- [ ] Streamlit permanece responsivo em todos os cenários de regra, inclusive nos patológicos.

## Risk Mitigation

- **Primary Risk (R9-a):** execução de código arbitrário via regra do usuário, em uma máquina que detém credenciais de banco de cliente.
- **Mitigation:** conjunto fechado de operadores (AC1); proibição explícita e testada de avaliadores de expressão (AC2); validação tipada de parâmetros (AC3).
- **Primary Risk (R9-b):** ReDoS congelando o processo único do Streamlit durante uso com o cliente.
- **Mitigation:** catálogo de padrões como caminho padrão (AC4); deadline obrigatório, rejeição de construções catastróficas e auto-desabilitação da regra (AC5); limites de tempo por execução (AC6).
- **Risco secundário:** proliferação de regras mal definidas poluindo as métricas de saúde e minando a confiança no relatório.
- **Mitigation:** distinção entre regra do sistema e regra customizada no dicionário (AC9); regras desabilitáveis com histórico e autoria (AC10).
- **Rollback Plan:** story aditiva. Desabilitar o módulo de regras (feature flag) restaura o comportamento de profiling anterior imediatamente; as tabelas de regras permanecem inertes. Recomendado entregar atrás de flag dado o perfil de risco.

## Quality Gates

| Story | Pre-Commit | Pre-PR | Pre-Deployment | Risco |
|---|---|---|---|---|
| 5.1 | Security scan (ausência de `eval`/`exec`/`query` com string do usuário), teste de ReDoS, benchmark | Revisão de arquitetura de segurança da avaliação de regras (@architect) | Verificação de feature flag e plano de desativação | **HIGH** |

## Definition of Done

- [ ] Story concluída com todos os AC atendidos.
- [ ] Teste automatizado comprovando rejeição de expressão Python submetida como regra.
- [ ] Teste automatizado com padrão regex catastrófico comprovando que a aplicação permanece responsiva e a regra é auto-desabilitada.
- [ ] Security scan sem ocorrência de avaliador de expressão sobre entrada do usuário.
- [ ] Métricas de regra visíveis no profiling e no dicionário consolidado, com distinção de origem.
- [ ] Feature flag de desativação documentada e testada.
- [ ] Nenhuma regressão para colunas sem regra customizada.

## Story Manager Handoff

"Desenvolver a story detalhada deste epic brownfield. Considerações:

- Sistema existente: Python + Streamlit (**processo único** — isto é central ao risco) + pandas + SQLite; Epic 1 concluído (migração e vetorização são pré-requisitos duros).
- Pontos de integração: `src/core/profiler.py` (avaliação), `src/validators/` (padrões reutilizáveis), metadata store do workspace (persistência), `src/app.py` (construtor de regras na UI).
- Padrões existentes a seguir: validadores existentes são reutilizados como operadores do catálogo; toda mudança de schema via migration da Story 1.2.
- Compatibilidade crítica: nenhuma coluna sem regra customizada pode mudar de resultado.
- **Atenção especial:** este é o item de maior risco de segurança de todo o roadmap. Os AC2 e AC5 são bloqueantes e não podem ser flexibilizados por conveniência de UX. Se a regex livre não puder ser contida com deadline confiável, entregue apenas o catálogo de padrões pré-aprovados (AC4) e registre a regex livre como escopo futuro."
