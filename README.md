# Data Catalog & Profiler

Aplicação Streamlit para catálogo de metadados, profiling de qualidade de dados e
análise de duplicidades sobre bancos acessíveis via SQLAlchemy.

Duas telas:

- **Data Discovery & Profiling** — estatísticas por coluna, inferência de tipo, validadores
  (CPF/CNPJ, e-mail, telefone, texto livre) e glossário de negócios persistido em SQLite.
- **Análise de Duplicidades** — duplicidades exatas e aproximadas (TF-IDF + similaridade de cosseno).

---

## 1. Requisitos

| Item | Valor |
|------|-------|
| Python | **3.11 a 3.14** (piso imposto por `numpy>=2.3.2`) |
| Sistema testado | Windows 11 Pro + Python 3.14.3 (venv limpo) |
| CI | Ubuntu + Python 3.11 (`.github/workflows/ci.yml`) |
| Banco padrão | SQLite (`sqlite:///metadata.db`) — nenhum driver extra necessário |

Drivers de outros bancos **não** estão no manifesto porque não são importados pelo código.
Para SQL Server (`mssql+pyodbc://...`), instale à parte: `pip install pyodbc` + ODBC Driver 17/18 no SO.

---

## 2. Manifestos de dependência

O repositório tem **dois** arquivos de requirements com propósitos distintos. Só um deles é do app:

| Arquivo | Serve a quê | Instalar para rodar o app? |
|---------|-------------|----------------------------|
| **`requirements_catalog.txt`** | **Manifesto oficial da aplicação.** Todos os pacotes importados por `src/` (+ `openpyxl`, engine exigida em runtime pelo `pd.ExcelWriter`). É o arquivo usado pelo CI. | **SIM** |
| `requirements-aiox-tooling.txt` | Tooling de IA/MCP do repositório (`anthropic`, `mcp`). Nenhum desses pacotes é importado por `src/`. Era o antigo `requirements.txt`, renomeado na Story 6.2 para eliminar a ambiguidade — o nome padrão fazia quem clonava o repo instalar o ambiente errado e o app quebrava com `ImportError`. | Não |

Regra do manifesto do app: **nenhum pacote é declarado sem uso real no código** (import direto em `src/`
ou engine exigida em runtime). Os pisos de versão são a primeira release com wheel binária
`cp314-win_amd64` publicada, porque `numpy`, `scikit-learn` e `pandas` têm extensões compiladas — com
piso mais baixo o `pip` poderia escolher uma versão sem wheel e tentar compilar do source (falha no
Windows sem MSVC Build Tools). Não há upper bounds: o resolver do pip harmoniza as versões.

---

## 3. Setup do ambiente

### Windows (PowerShell)

```powershell
git clone <url-do-repositorio>
cd CATALOGO

py -3.14 -m venv venv          # qualquer Python 3.11-3.14 serve
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements_catalog.txt
```

### Linux / macOS

```bash
git clone <url-do-repositorio>
cd CATALOGO

python3.11 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements_catalog.txt
```

---

## 4. Execução

Sempre **a partir da raiz do projeto**, com o venv ativado:

```bash
python -m streamlit run src/app.py
```

> **Use `python -m streamlit`, não `streamlit run`.**
> `src/app.py` importa os módulos como pacote (`from src.core...`). O comando `streamlit run`
> coloca apenas a pasta do script (`src/`) no `sys.path`, e a aplicação quebra com
> `ModuleNotFoundError: No module named 'src'`. Com `python -m`, o diretório atual entra no
> `sys.path` e os imports resolvem. (Alternativa equivalente: `PYTHONPATH=. streamlit run src/app.py`.)

O app sobe em `http://localhost:8501`. No menu lateral, conecte informando a string SQLAlchemy
(padrão `sqlite:///metadata.db`), clique em **Conectar** e escolha a tela em "Modo de Análise".

---

## 5. Verificação de instalação limpa (reprodutível)

Procedimento para uma segunda pessoa confirmar, do zero, que o manifesto está completo.
Tempo aproximado: 5 minutos.

```powershell
# 1. Clone limpo, fora da árvore de trabalho atual
git clone <url-do-repositorio> C:\temp\catalogo-check
cd C:\temp\catalogo-check

# 2. Venv NOVO (não reutilizar o venv existente — mascara dependências faltantes)
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar SOMENTE o manifesto do app
python -m pip install -r requirements_catalog.txt

# 4. Smoke de import — precisa terminar sem nenhuma saída de erro
python -c "import src.core.db_manager, src.core.deduplicator, src.core.profiler, src.models.glossary, src.validators.docs_br, src.validators.email_val, src.validators.phone, src.validators.text_clean; print('imports OK')"

# 5. Subir o app e navegar nas DUAS telas
python -m streamlit run src/app.py
```

Na etapa 5, conecte em `sqlite:///metadata.db`, selecione uma tabela e execute
**Executar Data Discovery** (tela 1) e **Buscar Duplicidades** (tela 2).
Critério de aceite: nenhuma das telas exibe `ImportError` / `ModuleNotFoundError`.

**Armadilha conhecida no Windows:** se o caminho do venv for muito profundo, o `pip` falha ao
instalar `scikit-learn` com `OSError: [Errno 2] No such file or directory: ...\_radius_neighbors_classmode.cp314-win_amd64.lib`.
É o limite de 260 caracteres do Windows, não um problema do manifesto — use um caminho curto
(ex.: `C:\temp\...`) ou habilite o suporte a long paths.

---

## 6. CI

`.github/workflows/ci.yml` roda em cada push/PR para `main`: instala `requirements_catalog.txt`
no Python 3.11 (o piso declarado) e roda `flake8` sobre `src`.

---

## 7. Documentação do projeto

- PRD e epics: `docs/prd/`
- Stories de desenvolvimento: `docs/stories/`
