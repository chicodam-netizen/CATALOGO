---
epic_id: 6
title: Débito Técnico de Plataforma (Escalabilidade, Dependências, Testes) - Brownfield Enhancement
status: Draft
priority: P2
depends_on: []
parallelizable: true
owner: "@pm"
created: 2026-09-08
note: >
  Epic paralelizável. Recomenda-se antecipar a Story 6.2 para junto do Epic 1
  e a Story 6.3 para antes da Story 1.3.
stories:
  - id: "6.1"
    title: Escalabilidade do deduplicator (matriz N×N e código morto)
    executor: "@dev"
    quality_gate: "@architect"
    quality_gate_tools: [code_review, memory_benchmark, regression_test]
  - id: "6.2"
    title: Declarar dependências e garantir instalação limpa reproduzível
    executor: "@devops"
    quality_gate: "@architect"
    quality_gate_tools: [dependency_audit, clean_install_test]
  - id: "6.3"
    title: Baseline de testes automatizados
    executor: "@dev"
    quality_gate: "@qa"
    quality_gate_tools: [test_coverage_review, test_quality_assessment]
---

# Epic 6: Débito Técnico de Plataforma

## Epic Goal

Eliminar três débitos que não pertencem a nenhuma das 12 funcionalidades de governança, mas que sabotam a execução de todas elas: um algoritmo que estoura memória no volume default, um ambiente que não instala do zero, e a ausência total de rede de segurança para refatorar.

## Epic Description

### Existing System Context

- **Funcionalidade atual relevante:** a tela "Análise de Duplicidades" (`src/app.py:144-204`) chama `find_duplicates` (`src/core/deduplicator.py:7`), que vetoriza as colunas selecionadas com TF-IDF e calcula similaridade de cosseno.
- **Stack:** Python, Streamlit, pandas, numpy, scikit-learn, rapidfuzz, SQLAlchemy.
- **Pontos de integração:** `deduplicator.py` é consumido apenas por `app.py`; `requirements_catalog.txt` é o manifesto de instalação; não existe diretório de testes.

### Débitos concretos, verificados no código

1. **Matriz de similaridade N×N completa.** `cosine_similarity(tfidf_matrix, tfidf_matrix)` (`deduplicator.py:35`) materializa uma matriz densa N×N. Com o `sample_size` default de 50.000 (`app.py:56`), isso são 2,5 bilhões de floats — na ordem de dezenas de GB. O resultado prático é `MemoryError`, e o usuário chega lá pelo caminho padrão da UI, sem nenhum aviso prévio.
2. **Código morto e custoso.** A linha 69 de `deduplicator.py` monta `duplicated_indices` com uma compreensão aninhada que recalcula `np.where` sobre todas as linhas — trabalho O(n²) cujo resultado é **imediatamente descartado**, já que as linhas 72-80 recomputam a mesma informação de forma utilizável. Além disso, `rapidfuzz` é importado (linha 5) e nunca utilizado.
3. **Dependências não declaradas.** `requirements_catalog.txt` declara apenas `streamlit`, `pandas`, `sqlalchemy`, `dnspython` e `openpyxl`. `deduplicator.py:1-5` importa `numpy`, `sklearn` e `rapidfuzz` — nenhum declarado. Uma instalação limpa quebra com `ImportError` na tela de duplicidades. Existem ainda **dois manifestos** no repositório (`requirements.txt` e `requirements_catalog.txt`) sem relação documentada entre eles.
4. **Zero testes automatizados.** Não há testes em `src/` nem diretório de testes no projeto. Os Epics 1 a 5 incluem refatorações de comportamento numérico (vetorização do profiler, migrações de schema, avaliação de regras) que, sem baseline de testes, são verificáveis apenas por inspeção manual.

---

## Stories

### Story 6.1 — Escalabilidade do deduplicator

`executor: @dev` · `quality_gate: @architect` · `quality_gate_tools: [code_review, memory_benchmark, regression_test]`

**Descrição:** Tornar a detecção de duplicidades viável no volume que a própria UI oferece por padrão, e limpar o código morto.

**Acceptance Criteria:**

1. `find_duplicates` deixa de materializar a matriz densa N×N (`deduplicator.py:35`). A estratégia adotada usa candidatos esparsos (ex.: top-k vizinhos via `NearestNeighbors`/`sparse_dot_topn`, ou blocking por chave) e é documentada com sua complexidade de memória.
2. Existe **guarda explícita de volume**: acima de um limite configurável de linhas, o sistema avisa antes de executar, com estimativa, e oferece reduzir a amostra — em vez de tentar, consumir toda a memória e falhar.
3. O código morto da linha 69 (`duplicated_indices` recomputado em O(n²) e descartado) é removido. Nota para o implementador: essa expressão também depende de `similar_indices` vazando do escopo do loop anterior — comportamento acidental, não intencional.
4. `rapidfuzz` (importado em `deduplicator.py:5` e não usado) é **utilizado de fato** no refinamento de score dos pares candidatos **ou** removido do código. Import não utilizado não permanece.
5. **Equivalência de resultado:** para um dataset de referência de tamanho moderado, o conjunto de grupos de duplicados encontrado é equivalente ao da implementação atual; divergências são documentadas e justificadas.
6. Benchmark de memória e tempo registrado (antes/depois) para 10k, 50k e 100k linhas. Meta: 50k linhas concluem sem `MemoryError`.
7. **Regressão:** a tela de duplicidades mantém o mesmo comportamento visível — métricas de contagem (`app.py:183-184`), tabela de duplicados agrupados e export Excel com as abas "Duplicados" e "Registros Unicos".
8. Toda dependência utilizada na nova estratégia está declarada (Story 6.2).

---

### Story 6.2 — Declarar dependências e garantir instalação limpa reproduzível

`executor: @devops` · `quality_gate: @architect` · `quality_gate_tools: [dependency_audit, clean_install_test]`

**Descrição:** Fazer com que o projeto instale e execute a partir de um clone limpo. É a story de menor esforço e maior efeito de desbloqueio de todo o roadmap.

**Acceptance Criteria:**

1. `requirements_catalog.txt` passa a declarar **todas** as dependências efetivamente importadas pelo código, incluindo `numpy`, `scikit-learn` e `rapidfuzz` (`deduplicator.py:1-5`), com versões mínimas.
2. Auditoria completa: todo import de terceiros em `src/` é cruzado com o manifesto; a lista de discrepâncias é reportada e zerada.
3. A relação entre `requirements.txt` e `requirements_catalog.txt` é resolvida — consolidação em um único manifesto ou documentação explícita de qual serve a quê. Ambiguidade de manifesto não permanece.
4. **Teste de instalação limpa:** em virtualenv novo, `pip install -r <manifesto>` seguido de `streamlit run` permite navegar nas duas telas (Profiling e Duplicidades) sem nenhum `ImportError`. O procedimento é documentado e reproduzido por outra pessoa que não a autora.
5. Instruções de setup do ambiente documentadas (versão de Python suportada, criação de venv, execução).
6. Nenhuma dependência é adicionada sem uso real no código (o inverso do débito atual).

---

### Story 6.3 — Baseline de testes automatizados

`executor: @dev` · `quality_gate: @qa` · `quality_gate_tools: [test_coverage_review, test_quality_assessment]`

**Descrição:** Estabelecer a rede de segurança mínima que as refatorações dos Epics 1 a 5 pressupõem.

**Acceptance Criteria:**

1. Framework de testes configurado (`pytest`), com diretório `tests/` espelhando a estrutura de `src/` e comando de execução documentado.
2. Cobertura de testes para os validadores de `src/validators/` (`docs_br.py`, `email_val.py`, `phone.py`, `text_clean.py`), incluindo casos válidos, inválidos, borda e entrada nula/vazia.
3. Testes para `profile_column` (`src/core/profiler.py`) que fixam o comportamento **atual** como baseline: percentuais de nulos, únicos e saúde para um DataFrame de referência congelado. Esses testes são o critério de equivalência da Story 1.3.
4. Teste de smoke que importa todos os módulos de `src/` e falha em caso de import quebrado (detecta o débito da Story 6.2 automaticamente).
5. Testes rodam sem depender de banco externo, de rede ou de credenciais.
6. O dataset de referência usado nos testes é sintético, versionado, e **não contém dados de cliente**.
7. Meta de cobertura acordada e registrada para o escopo coberto (validadores + profiler); não é exigida cobertura do `app.py` (UI Streamlit) nesta story.
8. Execução dos testes documentada de forma que o quality gate de qualquer story futura possa invocá-la.

---

## Compatibility Requirements

- [ ] Nenhuma mudança de comportamento visível na tela de Duplicidades além do ganho de escala e dos avisos de volume.
- [ ] Nenhuma alteração de schema ou de dados.
- [ ] Manifesto de dependências permanece instalável em Windows (ambiente atual do usuário) — atenção a rodas binárias de `scikit-learn`/`numpy`.
- [ ] Testes não introduzem dependência de runtime na aplicação (dependências de teste separadas ou marcadas como tal).

## Risk Mitigation

- **Primary Risk:** a substituição do algoritmo de similaridade (6.1) altera silenciosamente os grupos de duplicados encontrados, e um relatório de deduplicação entregue a um cliente passa a divergir do anterior sem explicação.
- **Mitigation:** dataset de referência e AC de equivalência (6.1 AC5); benchmark documentado (6.1 AC6); a Story 6.3 fornece o instrumento de verificação.
- **Risco secundário:** instalar `scikit-learn` em ambiente Windows sem toolchain de compilação.
- **Mitigation:** teste de instalação limpa como AC (6.2 AC4), executado no ambiente-alvo real.
- **Rollback Plan:** 6.2 e 6.3 são puramente aditivas (manifesto e testes) e não têm risco de rollback. 6.1 é confinada a `deduplicator.py`, consumido por um único ponto (`app.py:169`), e reverte por commit isolado.

## Quality Gates

| Story | Pre-Commit | Pre-PR | Risco |
|---|---|---|---|
| 6.1 | Benchmark de memória, teste de equivalência | Revisão de estratégia algorítmica (@architect) | MEDIUM |
| 6.2 | Auditoria de dependências | Teste de instalação limpa validado (@architect) | LOW |
| 6.3 | Revisão de qualidade dos testes | Avaliação de cobertura e utilidade (@qa) | LOW |

## Definition of Done

- [ ] As 3 stories concluídas com todos os AC atendidos.
- [ ] Deduplicação de 50.000 linhas concluída sem `MemoryError`, com benchmark registrado.
- [ ] Instalação limpa em venv novo validada por uma segunda pessoa.
- [ ] Suíte de testes verde, executável por um comando documentado.
- [ ] Nenhum import não declarado e nenhum import não utilizado remanescente em `src/`.
- [ ] Nenhuma regressão na tela de Duplicidades.

## Story Manager Handoff

"Desenvolver as stories detalhadas deste epic brownfield. Considerações:

- Sistema existente: Python + Streamlit + pandas + numpy + scikit-learn + rapidfuzz.
- Pontos de integração: `src/core/deduplicator.py` (consumido apenas por `src/app.py:169`), `requirements_catalog.txt`, novo diretório `tests/`.
- Compatibilidade crítica: comportamento visível da tela de duplicidades preservado; instalação limpa deve funcionar no ambiente Windows do usuário.
- **Sequenciamento recomendado:** 6.2 junto com o Epic 1 (desbloqueio imediato de ambiente); 6.3 antes da Story 1.3 (a vetorização do profiler precisa da baseline de testes para provar equivalência); 6.1 pode aguardar."
