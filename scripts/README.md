# scripts/ — validações adhoc (Playwright)

Scripts de validação de retrabalhos/casos Twygo. Rode sempre por caminho, de dentro
da raiz do projeto, com o venv:

```powershell
.\.venv\Scripts\python.exe scripts/<arquivo>.py
```

## `_twygo.py` — helpers compartilhados (use sempre)

Centraliza o que os scripts repetiam e **tira credenciais do código** (tudo vem do
`.env`; veja `.env.example`). Ao rodar por caminho, `scripts/` já entra no `sys.path`,
então basta `import _twygo`.

```python
from playwright.sync_api import sync_playwright
import _twygo as tw

c = tw.cfg("RECERT")              # perfis: "" (principal), "RECERT", "EDUAPI"
with sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)        # headless=False, slow_mo=350
    tw.login(page, c)                             # loga + troca pra admin
    tw.ir_learning(page, c, "807406")             # aba Aprendizagem do conteúdo
    linhas = tw.extrair_tabela(page)              # colunas mapeadas pelo cabeçalho
    # kebab/menu Chakra:
    tw.abrir_kebab(page, page.locator('tr[data-item-id="44275175"]'))
    tw.click_menuitem(page, "Histórico de aprendizagem")
    info = tw.item_reinscricao(page)              # {achou, corIcone, id, ...}
    bloqueado = tw.item_bloqueado_por_cor(info["corIcone"])  # cinza=bloqueado, azul=ok
    tw.snap(page, "evidencias/meu_caso", "01-estado")
    ctx.close(); browser.close()
```

Funções: `cfg`, `nova_pagina`, `login`, `ir_learning`, `dispensar_nps`,
`abrir_kebab`, `menu_visivel`, `click_menuitem`, `item_reinscricao`,
`item_bloqueado_por_cor`, `extrair_tabela`, `snap`.

## Credenciais

Nunca hardcode credencial. Adicione o perfil no `.env` (e a chave correspondente no
`.env.example`, sem valor). Perfis atuais: principal (`BASE_URL`/`ADMIN_*`),
`RECERT_*` (org 37048), `EDUAPI_*` (org 36912).

## `_archive/`

Scripts de inspeção/debug one-off (`inspect_*`, `debug_*`, `find_*`, `compare_*`,
`screenshot_*`) ficam aqui só como referência histórica — não fazem parte do fluxo.
