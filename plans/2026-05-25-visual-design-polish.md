# Visual Design Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir todos os emojis do app (tabs, header, mode selector, hint texts) por ícones Material (`ft.Icons.*`) e melhorar a hierarquia visual de tipografia/empty states/feedback visual.

**Architecture:** Centralizar o mapeamento emoji → ícone Material em `app/icons.py`. Refatorar cada view pra consumir essa biblioteca. Adicionar helpers em `ui_kit.py` (`label_com_icone`, `empty_state`). Atualizar `theme.py` com tokens de tipografia mais expressivos.

**Tech Stack:** Python 3.14 + Flet 0.85 + Material Icons (built-in no Flet via `ft.Icons.*`)

---

## Mapa emoji → ícone Material

Catalogado uma vez, usado em todo o app:

| Emoji atual | Significado | `ft.Icons.*` |
|---|---|---|
| 📚 | Documentação | `MENU_BOOK_OUTLINED` |
| 📋 | Caso de teste | `DESCRIPTION_OUTLINED` |
| 🖼️ | Evidências | `IMAGE_OUTLINED` |
| ▶ | Execução | `PLAY_CIRCLE_OUTLINE` |
| 📊 | Resultado | `INSIGHTS_OUTLINED` |
| 🔁 | Retrabalho (modo) | `AUTORENEW` |
| 📐 | Caso T-XXXX (modo) | `RULE_OUTLINED` |
| 🧪 | Logo do app | `SCIENCE_OUTLINED` |
| ⚙ | Configurações | `SETTINGS_OUTLINED` |
| 💾 | Salvar | `SAVE_OUTLINED` |
| 🗑️ | Apagar | `DELETE_OUTLINE` |
| ✅ | Sucesso | `CHECK_CIRCLE_OUTLINE` |
| ❌ | Falha | `ERROR_OUTLINE` |
| ⚠️ | Aviso | `WARNING_AMBER_OUTLINED` |
| ⇝/⇜ | KQA delimitadores | (mantém texto puro — não substituir) |

---

### Task 1: Centralizar mapeamento de ícones

**Files:**
- Create: `app/icons.py`

- [ ] **Step 1: Criar `app/icons.py`**

```python
"""Mapeamento centralizado de ícones do app.

Importar daqui em vez de espalhar ft.Icons.* pelas views. Mantém consistência
e facilita trocar um conjunto de ícones inteiro depois (light/colorido/outline).
"""
from __future__ import annotations

import flet as ft


class Icones:
    # Abas / seções principais
    DOC = ft.Icons.MENU_BOOK_OUTLINED
    CASO = ft.Icons.DESCRIPTION_OUTLINED
    EVIDENCIAS = ft.Icons.IMAGE_OUTLINED
    EXECUCAO = ft.Icons.PLAY_CIRCLE_OUTLINE
    RESULTADO = ft.Icons.INSIGHTS_OUTLINED

    # Modos
    MODO_RETRABALHO = ft.Icons.AUTORENEW
    MODO_CASO_TESTE = ft.Icons.RULE_OUTLINED

    # App / chrome
    LOGO = ft.Icons.SCIENCE_OUTLINED
    SETTINGS = ft.Icons.SETTINGS_OUTLINED

    # Ações
    SALVAR = ft.Icons.SAVE_OUTLINED
    APAGAR = ft.Icons.DELETE_OUTLINE
    ANEXAR = ft.Icons.UPLOAD_FILE_OUTLINED
    COLAR = ft.Icons.CONTENT_PASTE_OUTLINED
    NOVO = ft.Icons.ADD_OUTLINED
    ANALISAR = ft.Icons.AUTO_FIX_HIGH_OUTLINED
    LIMPAR = ft.Icons.CLEAR_OUTLINED
    EXECUTAR = ft.Icons.PLAY_ARROW_OUTLINED

    # Status / feedback
    OK = ft.Icons.CHECK_CIRCLE_OUTLINE
    ERRO = ft.Icons.ERROR_OUTLINE
    AVISO = ft.Icons.WARNING_AMBER_OUTLINED
    INFO = ft.Icons.INFO_OUTLINE

    # Empty states
    PASTA_VAZIA = ft.Icons.FOLDER_OPEN_OUTLINED
    UPLOAD_VAZIO = ft.Icons.UPLOAD_FILE_OUTLINED
    BUSCA_VAZIA = ft.Icons.SEARCH_OFF_OUTLINED
```

- [ ] **Step 2: Verificar import**

Run: `.\.venv\Scripts\python.exe -c "from app.icons import Icones; print('OK:', Icones.DOC)"`
Expected: `OK: <MaterialIcons.MENU_BOOK_OUTLINED>` (ou similar)

- [ ] **Step 3: Commit**

```bash
git add app/icons.py
git commit -m "feat(app): adiciona mapa central de icones Material"
```

---

### Task 2: Helpers visuais em ui_kit.py

**Files:**
- Modify: `app/ui_kit.py` (adicionar funções, não remover nada existente)

- [ ] **Step 1: Adicionar `label_aba`, `empty_state` e `titulo_pagina`**

Append ao final de `app/ui_kit.py`:

```python
def label_aba(icone: str, texto: str, ativo: bool) -> ft.Row:
    """Conteúdo de uma aba: ícone + texto, com cor de acento quando ativo."""
    cor = Tokens.ACCENT if ativo else Tokens.TEXT_MUTED
    peso = Tokens.WEIGHT_SEMIBOLD if ativo else Tokens.WEIGHT_MEDIUM
    return ft.Row(
        controls=[
            ft.Icon(icon=icone, color=cor, size=Tokens.FONT_BASE),
            ft.Text(texto, color=cor, weight=peso, size=Tokens.FONT_SM),
        ],
        spacing=Tokens.SPACE_2,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def empty_state(icone: str, titulo: str, descricao: str) -> ft.Container:
    """Placeholder para áreas vazias: ícone grande + título + descrição."""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(icon=icone, size=56, color=Tokens.TEXT_MUTED),
                ft.Container(height=Tokens.SPACE_2),
                ft.Text(
                    titulo,
                    color=Tokens.TEXT_PRIMARY,
                    size=Tokens.FONT_BASE,
                    weight=Tokens.WEIGHT_SEMIBOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    descricao,
                    color=Tokens.TEXT_MUTED,
                    size=Tokens.FONT_SM,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        ),
        padding=ft.Padding(left=Tokens.SPACE_5, top=Tokens.SPACE_6, right=Tokens.SPACE_5, bottom=Tokens.SPACE_6),
    )


def titulo_pagina(texto: str, *, icone: str | None = None) -> ft.Row:
    """Título grande de seção (h1): opcional ícone à esquerda."""
    controles: list[ft.Control] = []
    if icone:
        controles.append(ft.Icon(icon=icone, color=Tokens.ACCENT, size=Tokens.FONT_LG))
    controles.append(
        ft.Text(
            texto,
            color=Tokens.TEXT_PRIMARY,
            size=Tokens.FONT_LG,
            weight=Tokens.WEIGHT_BOLD,
        )
    )
    return ft.Row(controls=controles, spacing=Tokens.SPACE_2, tight=True)
```

- [ ] **Step 2: Verificar import**

Run: `.\.venv\Scripts\python.exe -c "from app.ui_kit import label_aba, empty_state, titulo_pagina; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/ui_kit.py
git commit -m "feat(ui_kit): adiciona label_aba, empty_state e titulo_pagina"
```

---

### Task 3: Trocar emojis das abas e mode selector em main.py

**Files:**
- Modify: `app/main.py` (header + mode selector + tab labels)

- [ ] **Step 1: Substituir emojis dos `conteudos_abas`**

Em `_shell_principal()` (procurar `conteudos_abas:`), trocar:

```python
conteudos_abas: list[tuple[str, ft.Control]] = [
    ("📚 Documentação", documentacao_view.construir(page, state)),
    ("📋 Caso", caso_view.construir(page, state)),
    ("🖼️ Evidências", evidencias_view.construir(page, state)),
    ("▶ Execução", execucao_view.construir(page, state)),
    ("📊 Resultado", resultado_view.construir(page, state)),
]
```

por:

```python
from app.icons import Icones

conteudos_abas: list[tuple[str, str, ft.Control]] = [
    (Icones.DOC, "Documentação", documentacao_view.construir(page, state)),
    (Icones.CASO, "Caso", caso_view.construir(page, state)),
    (Icones.EVIDENCIAS, "Evidências", evidencias_view.construir(page, state)),
    (Icones.EXECUCAO, "Execução", execucao_view.construir(page, state)),
    (Icones.RESULTADO, "Resultado", resultado_view.construir(page, state)),
]
```

- [ ] **Step 2: Atualizar `construir_botao_aba` para usar `label_aba`**

Trocar:

```python
def construir_botao_aba(idx: int) -> ft.Container:
    ativo = idx == aba_ativa[0]
    return ft.Container(
        content=ft.Text(
            conteudos_abas[idx][0],
            color=Tokens.ACCENT if ativo else Tokens.TEXT_MUTED,
            weight=Tokens.WEIGHT_SEMIBOLD if ativo else Tokens.WEIGHT_MEDIUM,
            size=Tokens.FONT_SM,
        ),
        # ...
    )
```

por:

```python
from app.ui_kit import label_aba

def construir_botao_aba(idx: int) -> ft.Container:
    ativo = idx == aba_ativa[0]
    icone, texto, _ = conteudos_abas[idx]
    return ft.Container(
        content=label_aba(icone, texto, ativo),
        padding=ft.Padding(left=Tokens.SPACE_4, top=Tokens.SPACE_3, right=Tokens.SPACE_4, bottom=Tokens.SPACE_3),
        border=ft.Border(
            bottom=ft.BorderSide(2 if ativo else 0, Tokens.ACCENT if ativo else "#00000000")
        ),
        on_click=lambda _e, i=idx: trocar_aba(i),
        ink=True,
    )
```

Também ajustar `trocar_aba`:

```python
def trocar_aba(idx: int) -> None:
    aba_ativa[0] = idx
    conteudo_container.content = conteudos_abas[idx][2]  # índice 2 agora (era 1)
    reconstruir_barra()
```

E o conteúdo inicial:

```python
conteudo_container = ft.Container(content=conteudos_abas[0][2], expand=True)
```

- [ ] **Step 3: Atualizar mode selector pra usar Icones**

Procurar `_botao_modo` em `_seletor_modo`. Já usa `ft.Icons.AUTORENEW` e `ft.Icons.RULE_OUTLINED`. Trocar pra:

```python
_botao_modo("Retrabalho", "retrabalho", Icones.MODO_RETRABALHO),
_botao_modo("Caso T-XXXX", "caso_teste", Icones.MODO_CASO_TESTE),
```

(import já adicionado no topo do arquivo no Step 1)

- [ ] **Step 4: Atualizar logo do header**

Procurar `ft.Icons.SCIENCE_OUTLINED` no header e trocar:

```python
ft.Icon(icon=Icones.LOGO, color=Tokens.ACCENT, size=Tokens.FONT_XL),
```

E o `SETTINGS_OUTLINED` do IconButton:

```python
ft.IconButton(icon=Icones.SETTINGS, ...)
```

- [ ] **Step 5: Rodar app e verificar visualmente**

Run: `.\run.cmd`
Expected: app abre na shell com as 5 abas mostrando ícone Material à esquerda do texto (em vez de emoji). Mode selector mostra ícones de seta circular e régua. Logo do header é o frasco de ciência.

- [ ] **Step 6: Commit**

```bash
git add app/main.py
git commit -m "feat(main): troca emojis por icones Material em abas, modo e header"
```

---

### Task 4: Substituir emojis e ícones em `documentacao_view.py`

**Files:**
- Modify: `app/views/documentacao_view.py`

- [ ] **Step 1: Importar Icones e helpers**

Adicionar no topo:

```python
from app.icons import Icones
from app.ui_kit import empty_state, titulo_pagina  # além dos já existentes
```

- [ ] **Step 2: Trocar `_icone_por_tipo`**

```python
def _icone_por_tipo(tipo: str) -> str:
    return {
        "md": ft.Icons.ARTICLE_OUTLINED,
        "txt": ft.Icons.DESCRIPTION_OUTLINED,
        "pdf": ft.Icons.PICTURE_AS_PDF_OUTLINED,
        "imagem": ft.Icons.IMAGE_OUTLINED,
    }.get(tipo, ft.Icons.INSERT_DRIVE_FILE_OUTLINED)
```

Não precisa mexer — já usa Material Icons. Manter como está.

- [ ] **Step 3: Trocar título `secao_titulo("Documentação do projeto")`**

Por:

```python
titulo_pagina("Documentação do projeto", icone=Icones.DOC),
```

- [ ] **Step 4: Substituir empty states inline pelo helper `empty_state`**

Procurar onde monta o estado vazio em `atualizar_lista()` — substituir as duas variantes (sem projeto, projeto sem docs):

```python
def atualizar_lista() -> None:
    if not state.projeto_ativo:
        lista_docs_container.controls = [
            empty_state(
                Icones.PASTA_VAZIA,
                "Nenhum projeto selecionado",
                "Escolha um projeto no dropdown acima ou crie um novo.",
            )
        ]
    elif not state.documentacao:
        lista_docs_container.controls = [
            empty_state(
                Icones.UPLOAD_VAZIO,
                f"Projeto '{state.projeto_ativo}' sem documentos ainda",
                "Use os botões abaixo para adicionar regras de negócio, discovery, etc.",
            )
        ]
    else:
        lista_docs_container.controls = [
            _item_doc(doc, on_remover_doc) for doc in state.documentacao
        ]
    _maybe_update()
```

- [ ] **Step 5: Atualizar botões de ação com ícones**

Procurar `botoes_adicionar`:

```python
botoes_adicionar = ft.Row(
    controls=[
        botao_primario("Anexar arquivo", on_anexar, icon=Icones.ANEXAR),
        botao_secundario("Colar imagem", on_colar_imagem),
        botao_secundario("Colar texto", on_colar_texto),
    ],
    spacing=Tokens.SPACE_2,
)
```

(Trocar `ft.Icons.UPLOAD_FILE_OUTLINED` por `Icones.ANEXAR`)

E botão "+ Novo projeto":

```python
botao_secundario("Novo projeto", on_novo_projeto),  # remover o + do texto
```

(O ícone vai entrar via parâmetro num próximo passo se quisermos — botao_secundario hoje não aceita icon. Manter texto puro.)

- [ ] **Step 6: Rodar app e verificar aba Documentação**

Run: `.\run.cmd`
Expected: aba Documentação mostra título grande "Documentação do projeto" com ícone de livro. Empty state tem ícone grande de pasta. Botão "Anexar arquivo" tem ícone de upload.

- [ ] **Step 7: Commit**

```bash
git add app/views/documentacao_view.py
git commit -m "feat(doc-view): substitui emojis por icones Material e usa empty_state helper"
```

---

### Task 5: Substituir emojis em `caso_view.py`

**Files:**
- Modify: `app/views/caso_view.py`

- [ ] **Step 1: Importar Icones e titulo_pagina**

```python
from app.icons import Icones
from app.ui_kit import titulo_pagina  # além dos já existentes
```

- [ ] **Step 2: Trocar título e hints de modo**

Substituir `secao_titulo("Caso de teste")` por `titulo_pagina("Caso de teste", icone=Icones.CASO)`.

Em `atualizar_hint_modo`, remover os emojis 🔁 e 📐:

```python
def atualizar_hint_modo() -> None:
    if state.modo == "retrabalho":
        hint_modo.value = (
            "Modo Retrabalho: cole o texto do incidente como vem do Artia "
            "(:: Incidente identificado :: ...)."
        )
        texto_field.hint_text = PLACEHOLDER_RETRABALHO
    else:
        hint_modo.value = (
            "Modo Caso de teste T-XXXX: cole o caso completo com Objetivo, "
            "Pré-condições e tabela de passos."
        )
        texto_field.hint_text = PLACEHOLDER_CASO_TESTE
    _maybe_update()
```

(Pode já estar sem emoji da última iteração — confirmar e ajustar.)

- [ ] **Step 3: Trocar `secao_titulo("Resumo do caso", sutil=True)`**

Manter `secao_titulo` (é um subtítulo, não título de página).

- [ ] **Step 4: Atualizar botões com ícones consistentes**

```python
botao_primario("Analisar", on_analisar, icon=Icones.ANALISAR),
botao_secundario("Limpar", on_limpar),
```

(`ft.Icons.AUTO_FIX_HIGH` virou `Icones.ANALISAR`.)

- [ ] **Step 5: Rodar app e verificar aba Caso**

Run: `.\run.cmd` → clica aba Caso
Expected: título com ícone de descrição. Botão "Analisar" com ícone de varinha mágica.

- [ ] **Step 6: Commit**

```bash
git add app/views/caso_view.py
git commit -m "feat(caso-view): substitui emojis e padroniza icones"
```

---

### Task 6: Polish dos placeholders de Evidências/Execução/Resultado

**Files:**
- Modify: `app/views/evidencias_view.py`
- Modify: `app/views/execucao_view.py`
- Modify: `app/views/resultado_view.py`

- [ ] **Step 1: `evidencias_view.py`**

Reescrever para usar `empty_state` helper:

```python
"""Aba Evidências — placeholder, será implementado na Fatia 3."""
from __future__ import annotations

import flet as ft

from app.icons import Icones
from app.state import AppState
from app.theme import Tokens
from app.ui_kit import empty_state


def construir(page: ft.Page, state: AppState) -> ft.Control:
    return ft.Container(
        content=empty_state(
            Icones.EVIDENCIAS,
            "Aba Evidências",
            "Será implementada na Fatia 3: paste de imagem, drag-and-drop, fetch de links do Jam.",
        ),
        padding=Tokens.SPACE_5,
        expand=True,
        alignment=ft.Alignment(0, 0),
    )
```

- [ ] **Step 2: `execucao_view.py`**

```python
"""Aba Execução — placeholder, será implementado na Fatia 4."""
from __future__ import annotations

import flet as ft

from app.icons import Icones
from app.state import AppState
from app.theme import Tokens
from app.ui_kit import empty_state


def construir(page: ft.Page, state: AppState) -> ft.Control:
    return ft.Container(
        content=empty_state(
            Icones.EXECUCAO,
            "Aba Execução",
            "Será implementada na Fatia 4: agente QA, Playwright, log em tempo real e detecção de stage down.",
        ),
        padding=Tokens.SPACE_5,
        expand=True,
        alignment=ft.Alignment(0, 0),
    )
```

- [ ] **Step 3: `resultado_view.py`**

```python
"""Aba Resultado — placeholder, será implementado na Fatia 5."""
from __future__ import annotations

import flet as ft

from app.icons import Icones
from app.state import AppState
from app.theme import Tokens
from app.ui_kit import empty_state


def construir(page: ft.Page, state: AppState) -> ft.Control:
    return ft.Container(
        content=empty_state(
            Icones.RESULTADO,
            "Aba Resultado",
            "Será implementada na Fatia 5: laudo, comentário KQA, comparação visual lado a lado, auto-commit.",
        ),
        padding=Tokens.SPACE_5,
        expand=True,
        alignment=ft.Alignment(0, 0),
    )
```

- [ ] **Step 4: Rodar e verificar as 3 abas**

Run: `.\run.cmd` → clicar em Evidências, Execução, Resultado
Expected: cada uma mostra um empty state centralizado com ícone grande + título + descrição.

- [ ] **Step 5: Commit**

```bash
git add app/views/evidencias_view.py app/views/execucao_view.py app/views/resultado_view.py
git commit -m "feat(placeholders): empty_state nas 3 abas pendentes"
```

---

### Task 7: Ajustar tipografia em `theme.py`

**Files:**
- Modify: `app/theme.py`

- [ ] **Step 1: Adicionar tokens de tipografia mais explícitos**

Em `class Tokens`, adicionar logo após os FONT_*:

```python
    # Pesos
    WEIGHT_NORMAL = ft.FontWeight.W_400
    WEIGHT_MEDIUM = ft.FontWeight.W_500
    WEIGHT_SEMIBOLD = ft.FontWeight.W_600
    WEIGHT_BOLD = ft.FontWeight.W_700

    # Escala de tipografia (sugerida — usar conforme contexto)
    # H1 (página): FONT_LG (20) com WEIGHT_BOLD
    # H2 (seção): FONT_BASE (16) com WEIGHT_SEMIBOLD
    # Body: FONT_SM (14) com WEIGHT_NORMAL
    # Caption: FONT_XS (12) com WEIGHT_NORMAL ou MEDIUM
    # Preço/destaque: FONT_XXL (32) com WEIGHT_BOLD
```

(O bloco já existe — só adicionar o comentário de escala como referência rápida.)

- [ ] **Step 2: Verificar import**

Run: `.\.venv\Scripts\python.exe -c "from app.theme import Tokens; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/theme.py
git commit -m "docs(theme): documenta escala de tipografia em comentario"
```

---

### Task 8: Verificação final end-to-end

- [ ] **Step 1: Apagar `.env` para testar fluxo completo**

Run: `if (Test-Path .env) { Remove-Item .env }`

- [ ] **Step 2: Rodar app**

Run: `.\run.cmd`

Esperado (roteiro manual):

1. Tela de login aparece sem emojis — botões "Salvar" e "Cancelar" com ícones Material.
2. Preencher campos (qualquer coisa) e clicar Salvar.
3. Shell aparece. Header tem ícone de frasco (LOGO), título "Twygo QA Tester", mode selector com ícones de seta circular e régua, ícone de engrenagem (SETTINGS) à direita.
4. Barra de abas: 5 abas, cada uma com ícone Material à esquerda do texto. Aba ativa em roxo com sublinhado.
5. Aba **Documentação**: título com ícone de livro, dropdown vazio, empty state com ícone grande de pasta.
6. Aba **Caso**: título com ícone de descrição.
7. Abas **Evidências/Execução/Resultado**: empty state centralizado com ícone grande + descrição.

- [ ] **Step 3: Capturar print da tela final pra registro**

(Manual: usuário tira print das 5 abas e do header, anexa em `evidencias/_polish/` ou similar.)

- [ ] **Step 4: Commit do estado verificado**

Se tiver criado arquivos novos de evidência:

```bash
git add evidencias/_polish/
git commit -m "docs: prints do polish visual aplicado"
```

---

## Próximos passos (fora do escopo deste plano)

- Tema claro (toggle no header)
- Animações de transição entre abas
- Estados de hover/focus mais ricos nos botões
- Tipografia: bundle de fonte custom localmente (sem URL) se quiser fugir do Segoe UI
