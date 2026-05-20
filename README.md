# twygo-playwright-tests

Automação de testes da plataforma **Twygo** usando [Playwright](https://playwright.dev/python/) com Python + pytest.

Cada caso manual (no padrão Objetivo / Pré-condições / Passos numerados com Resultado Esperado) é traduzido para um arquivo de teste **rastreável** — quem lê o código consegue bater 1:1 com o caso manual. Quando um teste falha, o resultado vira um relatório de incidente no formato `:: Incidente identificado ::`.

Há dois modos de uso:
- **Manual (pytest)**: você escreve o arquivo de teste seguindo o padrão e roda com `pytest` — bom pra testes que viraram regressão.
- **UI (Gradio + Claude)**: cola o caso, o sistema parseia, executa cada passo dirigindo Playwright via Claude API, gera o arquivo pytest persistente e retorna bug report no formato `:: Incidente identificado ::` se algo falhar.

---

## Pré-requisitos

- **Python 3.10+** (testado em 3.12)
- **pip** e **venv**:
  ```bash
  sudo apt-get install -y python3.12-venv
  ```
- Acesso a uma org de stage da Twygo (URL, e-mail/senha de admin e de aluno).

## Setup inicial (uma vez)

```bash
git clone https://github.com/DantexgerBR/twygo-playwright-tests.git
cd twygo-playwright-tests

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

## Configurar credenciais

Copie o template e preencha:

```bash
cp .env.example .env
```

Edite `.env`:

```env
BASE_URL=https://twygo<sua-org>.stage.twygoead.com/
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=...
ALUNO_EMAIL=aluno@example.com
ALUNO_PASSWORD=...
ORG_ID=-1
ATIVIDADE_VIDEO_MARCA_DAGUA_ID=<id-da-atividade-pre-cadastrada>
```

> O `.env` está no `.gitignore` — **nunca** será commitado.

## Modo UI (Gradio + Claude)

Para colar um caso de teste e rodar dinamicamente:

```bash
source .venv/bin/activate
PYTHONPATH=. python -m ui.app
```

Abre `http://127.0.0.1:7860`. Cole o caso na textarea, confira os campos (já vêm pré-populados do `.env`), e clique **Executar**. A UI:

1. Parseia o caso (objetivo, pré-condições, passos).
2. Para cada passo: captura snapshot da página → manda para Claude (`claude-opus-4-7`) com prompt caching → executa as ações Playwright que ele retornar.
3. Verifica as asserções declaradas pelo modelo.
4. Gera `tests/gerado/test_<slug>.py` + `docs/casos/<slug>.md`.
5. Se algum passo falhar, retorna bug report no formato `:: Incidente identificado ::` + screenshot.

Requer `ANTHROPIC_API_KEY` no `.env`.

## Rodar testes manuais

```bash
source .venv/bin/activate

# Todos os testes
pytest -v

# Uma feature
pytest tests/marca_dagua/ -v

# Um teste específico, com debug visual mais lento
pytest tests/marca_dagua/test_desmarcar_marca_dagua_video.py -v --headed --slowmo 500

# Filtrar por marker
pytest -m marca_dagua -v
pytest -m admin -v
```

Em caso de falha, o Playwright gera automaticamente:
- `test-results/<teste>/trace.zip` — abra em https://trace.playwright.dev/
- `test-results/<teste>/test-failed-1.png` — screenshot do momento da falha
- `test-results/<teste>/video.webm` — vídeo da execução

---

## Estrutura

```
twygo-playwright-tests/
├── CLAUDE.md                  # Rules estritas para Claude Code (templates, fluxo, formato de bug report)
├── README.md                  # Este arquivo
├── .env.example               # Variáveis de ambiente (template, sem credenciais)
├── pytest.ini                 # Markers + opções (--headed, --tracing retain-on-failure)
├── requirements.txt           # pytest, pytest-playwright, playwright, python-dotenv
├── conftest.py                # Fixtures globais: base_url, admin_logado, aluno_logado
│
├── docs/casos/                # Transcrição em Markdown de cada caso manual
│
├── pages/                     # Page Objects (todos os seletores ficam aqui)
│   ├── base_page.py
│   ├── login_page.py
│   ├── admin/                 # Páginas da área administrativa
│   │   └── atividade_video_page.py
│   └── aprender/              # Páginas da área do aluno
│       └── conteudo_video_page.py
│
├── fixtures/                  # Fixtures de domínio (futuras: organizações, dados pré-seed)
│
└── tests/
    └── <area>/
        └── test_<slug>.py     # Um arquivo por caso de teste manual
```

---

## Como adicionar um caso de teste novo

Use este passo a passo sempre que tiver um caso manual novo:

### 1. Transcreva o caso manual

Crie `docs/casos/<slug>.md` com o caso em Markdown (Objetivo + Pré-condições + tabela de passos).

### 2. Crie/atualize Page Objects

Em `pages/<area>/<nome>_page.py`, exponha os elementos da UI como atributos do Page Object — **nunca** use seletores soltos no teste.

```python
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage

class MinhaPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.botao_x: Locator = page.get_by_role("button", name="X")
```

### 3. Crie o arquivo de teste

Em `tests/<area>/test_<slug>.py`, siga o **template obrigatório**:

```python
"""
CASO: <objetivo literal do caso manual>

PRÉ-CONDIÇÕES:
    - <pré-condição 1>
    - <pré-condição 2>

PERFIL TESTADO: <Administrador / Aluno / ...>
PLATAFORMA: Desktop
AMBIENTE: Principal (stage)

Referência: docs/casos/<slug>.md
"""
import pytest
from playwright.sync_api import expect

from pages.<area>.<page> import <PageObject>


@pytest.mark.<perfil>          # admin ou aluno
@pytest.mark.<feature>         # marca_dagua, etc
def test_<slug>(admin_logado, base_url):
    pagina = <PageObject>(admin_logado)

    # Passo 1 — <ação literal do caso>
    # Esperado: <resultado esperado literal>
    pagina.<ação>()
    expect(pagina.<elemento>).<asserção>()

    # Passo 2 — ...
    # Esperado: ...
    ...
```

**Regras inegociáveis:**
- Docstring no topo = transcrição literal (objetivo + pré-condições + perfil + plataforma + ambiente).
- Cada passo manual = `# Passo N — <ação>` + `# Esperado: <resultado>` + ações/asserções.
- Pré-condições atendidas por **fixtures** (`admin_logado`, `aluno_logado`, `base_url`).
- Nenhum seletor solto — tudo via Page Object.

### 4. Rode o teste

```bash
pytest tests/<area>/test_<slug>.py -v --headed
```

---

## Formato de relatório quando um teste falha

Quando algum teste falha, o relatório de incidente segue este formato:

```
:: Incidente identificado ::
<resumo do que falhou em 1 linha>

    :: Passo a passo para reprodução ::
» Passo 1: <ação do passo 1>
» Passo 2: <ação do passo 2>
» Passo N: <passo que falhou — destacar>

    :: Comportamento esperado ::
<Resultado Esperado literal do passo que falhou>

    :: Informações ::
url: <BASE_URL>
login: <e-mail usado no passo>
senha: <senha correspondente>
org_id: <ORG_ID ou -1>
<linha extra com info de runtime>

    :: Evidência(s) ::
<descrição da evidência>
Link da evidência: test-results/<...>/trace.zip
```

---

## Fixtures disponíveis

| Fixture | O que devolve | Quando usar |
|---------|---------------|-------------|
| `base_url` | URL da org (do `.env`) | Para navegar para rotas absolutas |
| `admin_credentials` | dict `{email, password}` | Quando precisar das credenciais cruas |
| `aluno_credentials` | dict `{email, password}` | Idem |
| `admin_logado` | `Page` já logada como admin | Maioria dos testes de admin |
| `aluno_logado` | `Page` já logada como aluno | Testes do Aprender |

Contextos de admin e aluno são **isolados** (cada um tem o próprio `BrowserContext`), então dá pra logar os dois ao mesmo tempo no mesmo teste sem conflito de sessão.

---

## Markers

Definidos em `pytest.ini`:

- `@pytest.mark.admin` — perfil administrador
- `@pytest.mark.aluno` — perfil aluno
- `@pytest.mark.marca_dagua` — feature de marca d'água

Rode subconjuntos com `pytest -m <marker>`.

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| `BASE_URL não definida no .env` | `cp .env.example .env` e preencher |
| `playwright: command not found` | Ative o venv: `source .venv/bin/activate` |
| Browsers não baixados | `playwright install chromium` |
| Teste flake por timing | Use `expect(...).to_be_visible(timeout=...)` em vez de `assert .is_visible()` |
| Quero ver o trace | Abra `test-results/<...>/trace.zip` em https://trace.playwright.dev/ |

---

## Licença

Uso interno Twygo.
