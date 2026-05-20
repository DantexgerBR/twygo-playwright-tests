# Repositório de Testes Playwright — Twygo

Este repositório automatiza casos de teste manuais da plataforma Twygo usando **Playwright + pytest**. Os casos vêm em formato estruturado (Objetivo / Pré-condições / Passos numerados com Resultado Esperado) e cada caso vira um arquivo de teste rastreável.

---

## Rules de execução (siga sempre)

### 1. Antes de rodar testes — coletar credenciais
Sempre que o usuário pedir para **rodar testes**, **gerar testes a partir de um caso novo**, ou **reproduzir um incidente**, pergunte UMA A UMA via `AskUserQuestion` (sem assumir valores anteriores):

1. URL da org (ex: `https://twygo1772627238.stage.twygoead.com/`)
2. E-mail do admin
3. Senha do admin
4. E-mail do aluno
5. Senha do aluno

Em seguida, **sobrescreva** `.env` com esses valores (o arquivo está no `.gitignore`).

> Atenção: nunca commite `.env`. Nunca registre credenciais em memória/logs.

### 2. Quando o usuário colar um caso de teste novo
O formato é:

```
<Objetivo em uma frase>

Pré-condições
<lista>

Perfil de usuário: <perfil>
Tipo de ambiente: <ambiente>

#   Ações do Passo                Resultados Esperados   Execução  Notas  Status
1   <ação>                        <esperado>             Manual    ...    Passou
2   <ação>                        <esperado>             ...
...
```

Você deve:
1. Criar `docs/casos/<slug>.md` com o caso transcrito em Markdown.
2. Criar `tests/<area>/test_<slug>.py` usando o **template obrigatório** abaixo.
3. Criar/atualizar Page Objects em `pages/<area>/` para qualquer elemento novo da UI.
4. Reutilizar fixtures (`admin_logado`, `aluno_logado`, `base_url`) — não duplicar setup.

### 3. Template obrigatório de teste

```python
"""
CASO: <objetivo do caso, literal>

PRÉ-CONDIÇÕES:
    - <pré-condição 1>
    - <pré-condição 2>

PERFIL TESTADO: <perfil>
PLATAFORMA: <plataforma>
AMBIENTE: <ambiente>

Referência: docs/casos/<slug>.md
"""
import pytest
from playwright.sync_api import expect

from pages.<area>.<page> import <PageObject>


@pytest.mark.<perfil>          # admin ou aluno
@pytest.mark.<feature>         # marca_dagua, etc
def test_<slug>(admin_logado, aluno_logado, base_url):
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
- Cada passo manual = 2 linhas de comentário (`# Passo N — ação` + `# Esperado: resultado`) seguidas das ações Playwright correspondentes.
- Nenhum seletor solto no teste — tudo via Page Object.
- Asserções espelham os "Resultados Esperados" literais do caso manual.

### 4. Quando um teste falhar — retornar bug report
Sempre que `pytest` reportar falha em algum teste, responda no chat com **exatamente este formato** (uma ocorrência por teste falhado):

```
:: Incidente identificado ::
<resumo de 1 linha — qual asserção falhou e em que passo>

    :: Passo a passo para reprodução ::
» Passo 1: <ação do passo 1>
» Passo 2: <ação do passo 2>
» ...
» Passo N: <ação do passo que falhou — destacar este passo>

    :: Comportamento esperado ::
<copiar literal o "Resultado Esperado" do passo que falhou>

    :: Informações ::
url: <BASE_URL do .env>
login: <ADMIN_EMAIL ou ALUNO_EMAIL, conforme o passo>
senha: <ADMIN_PASSWORD ou ALUNO_PASSWORD>
org_id: <ORG_ID se conhecido, senão -1>
<linha extra com info de runtime: mensagem de erro do pytest, valor recebido vs esperado>

    :: Evidência(s) ::
<descrição: screenshot/trace do passo X>
Link da evidência: <caminho relativo a test-results/, ex: test-results/marca_dagua-test_desmarcar.../trace.zip>
```

Playwright gera automaticamente:
- `test-results/<teste>/trace.zip` (devido a `--tracing retain-on-failure` em `pytest.ini`)
- `test-results/<teste>/test-failed-1.png` (devido a `--screenshot only-on-failure`)
- `test-results/<teste>/video.webm` (devido a `--video retain-on-failure`)

Use esses caminhos como "Link da evidência".

---

## Estrutura do projeto

```
~/playwright-tests/
├── CLAUDE.md                  ← este arquivo
├── .env / .env.example        ← credenciais (NÃO commitar .env)
├── .gitignore
├── requirements.txt
├── pytest.ini                 ← markers, headed, tracing, screenshots
├── conftest.py                ← fixtures globais: base_url, admin_logado, aluno_logado
│
├── docs/casos/                ← transcrição MD de cada caso de teste manual
│
├── pages/                     ← Page Objects
│   ├── base_page.py
│   ├── login_page.py
│   ├── admin/                 ← páginas da área admin
│   └── aprender/              ← páginas da área do aluno
│
├── fixtures/                  ← fixtures de domínio (futuro: organizações, dados pré-seed)
│
└── tests/
    └── <area>/
        └── test_<slug>.py
```

## Comandos úteis

```bash
# Setup inicial (uma vez)
cd ~/playwright-tests
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Rodar todos os testes
pytest -v

# Rodar uma feature específica
pytest tests/marca_dagua/ -v

# Rodar um único teste com debug visual
pytest tests/marca_dagua/test_desmarcar_marca_dagua_video.py -v --headed --slowmo 500
```
