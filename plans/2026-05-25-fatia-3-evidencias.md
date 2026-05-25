# Fatia 3 — Aba Evidências — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) ou superpowers:executing-plans. Steps usam checkbox `- [ ]`.

**Goal:** Tornar a aba Evidências funcional — anexar arquivo via diálogo nativo, colar imagem da clipboard, detectar links Jam.dev no texto do caso e tentar baixar, listar evidências com miniatura/tipo/remover. Estado em `AppState.evidencias`.

**Architecture:** O serviço `jam_fetcher.py` faz HTTP GET na URL e extrai `og:image` (print) ou `og:video` (avisa). O `clipboard.py` (já existe) pega imagem. `file_dialog.py` (já existe) abre seletor nativo. `evidencias_view.py` substitui o `empty_state` placeholder por UI funcional. State já tem `Evidencia` modelado.

**Tech Stack:** Python 3.14 + Flet 0.85 + Pillow (já instalado) + httpx (já instalado) + Material Icons via `app.icons.Icones`.

---

## Modelos e estruturas existentes (reusar)

- `app.state.Evidencia` (dataclass: path, nome, tipo, origem)
- `app.state.AppState.evidencias: list[Evidencia]` + emit `"evidencias_changed"`
- `app.services.clipboard.pegar_imagem_da_clipboard(pasta, prefixo)` → Path | None
- `app.services.file_dialog.escolher_arquivos(titulo, extensoes, multiplo)` → list[Path]
- `app.icons.Icones.EVIDENCIAS` (ícone da aba)

## Estruturas a criar

- `app.services.jam_fetcher` — função `fetch_jam_url(url)` retorna `Path | "video" | None`
- `app.state.AppState.adicionar_evidencia(path, tipo, origem)` — append + emit
- `app.state.AppState.remover_evidencia(ev)` — remove + emit

---

### Task 1: Estender AppState para gerenciar evidências

**Files:**
- Modify: `app/state.py` (adicionar métodos, não tocar nos existentes)

- [ ] **Step 1: Adicionar métodos `adicionar_evidencia` e `remover_evidencia` em `AppState`**

Localizar na classe `AppState`, depois do método `remover_doc`, adicionar:

```python
    # ---- Evidências (não persistem em disco; vivem só durante a execução) ----

    def adicionar_evidencia(
        self,
        path: Path,
        tipo: Literal["print", "video", "link"],
        origem: Literal["upload", "paste", "jam"],
    ) -> Evidencia:
        ev = Evidencia(path=path, nome=path.name, tipo=tipo, origem=origem)
        self.evidencias.append(ev)
        self.emit("evidencias_changed", self.evidencias)
        return ev

    def remover_evidencia(self, ev: Evidencia) -> None:
        self.evidencias = [e for e in self.evidencias if e.path != ev.path]
        self.emit("evidencias_changed", self.evidencias)

    def limpar_evidencias(self) -> None:
        self.evidencias = []
        self.emit("evidencias_changed", self.evidencias)
```

- [ ] **Step 2: Verificar import**

Run:
```
.\.venv\Scripts\python.exe -c "from app.state import AppState; from pathlib import Path; s = AppState(Path('.').resolve()); print('OK', hasattr(s, 'adicionar_evidencia'), hasattr(s, 'remover_evidencia'))"
```

Esperado: `OK True True`

- [ ] **Step 3: Commit**

```
git add app/state.py
git commit -m "feat(state): adiciona adicionar/remover/limpar evidencias"
```

---

### Task 2: Implementar jam_fetcher

**Files:**
- Create: `app/services/jam_fetcher.py`
- Test: `tests/app/test_jam_fetcher.py`

- [ ] **Step 1: Escrever os testes primeiro (TDD)**

Criar `tests/app/test_jam_fetcher.py`:

```python
"""Testes do jam_fetcher: parser de URL, parser de HTML, fluxo end-to-end com mock."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.jam_fetcher import (
    extrair_id_jam,
    extrair_og_image,
    extrair_og_video,
    fetch_jam_url,
)


def test_extrair_id_jam_url_padrao():
    assert extrair_id_jam("https://jam.dev/c/abc123") == "abc123"


def test_extrair_id_jam_com_www():
    assert extrair_id_jam("https://www.jam.dev/c/xyz789") == "xyz789"


def test_extrair_id_jam_com_query():
    assert extrair_id_jam("https://jam.dev/c/abc123?ref=foo") == "abc123"


def test_extrair_id_jam_invalida_retorna_none():
    assert extrair_id_jam("https://google.com") is None
    assert extrair_id_jam("nao-uma-url") is None


def test_extrair_og_image_html_valido():
    html = '''
    <html><head>
    <meta property="og:image" content="https://cdn.jam.dev/abc.png" />
    </head></html>
    '''
    assert extrair_og_image(html) == "https://cdn.jam.dev/abc.png"


def test_extrair_og_image_html_sem_og():
    html = "<html><head><title>foo</title></head></html>"
    assert extrair_og_image(html) is None


def test_extrair_og_video_html_com_video():
    html = '<meta property="og:video" content="https://cdn.jam.dev/v.mp4" />'
    assert extrair_og_video(html) == "https://cdn.jam.dev/v.mp4"


def test_extrair_og_video_html_sem_video():
    html = '<meta property="og:image" content="foo.png" />'
    assert extrair_og_video(html) is None


def test_fetch_jam_url_imagem_baixa_e_retorna_path(tmp_path):
    html_resp = MagicMock()
    html_resp.status_code = 200
    html_resp.text = '<meta property="og:image" content="https://cdn.jam.dev/abc.png" />'

    img_resp = MagicMock()
    img_resp.status_code = 200
    img_resp.content = b"fake-png-bytes"

    with patch("httpx.get", side_effect=[html_resp, img_resp]):
        resultado = fetch_jam_url("https://jam.dev/c/abc123", tmp_path)

    assert isinstance(resultado, Path)
    assert resultado.exists()
    assert resultado.read_bytes() == b"fake-png-bytes"
    assert resultado.suffix == ".png"


def test_fetch_jam_url_video_retorna_string_video(tmp_path):
    html_resp = MagicMock()
    html_resp.status_code = 200
    html_resp.text = '<meta property="og:video" content="https://cdn.jam.dev/v.mp4" />'

    with patch("httpx.get", return_value=html_resp):
        resultado = fetch_jam_url("https://jam.dev/c/v123", tmp_path)

    assert resultado == "video"


def test_fetch_jam_url_404_retorna_none(tmp_path):
    resp = MagicMock()
    resp.status_code = 404
    resp.text = ""

    with patch("httpx.get", return_value=resp):
        assert fetch_jam_url("https://jam.dev/c/notfound", tmp_path) is None


def test_fetch_jam_url_invalida_retorna_none(tmp_path):
    assert fetch_jam_url("https://google.com", tmp_path) is None
```

Criar pasta se não existir: `mkdir -Force tests\app`.

- [ ] **Step 2: Rodar testes — devem FALHAR (modulo não existe ainda)**

Run: `.\.venv\Scripts\python.exe -m pytest tests/app/test_jam_fetcher.py -v`
Esperado: `ImportError` ou `ModuleNotFoundError` em `app.services.jam_fetcher`

- [ ] **Step 3: Implementar `app/services/jam_fetcher.py`**

```python
"""Detecta links do jam.dev em texto e tenta baixar a evidência.

Jam.dev compartilha bugs via URLs como https://jam.dev/c/<id>. Cada página
tem meta tags og:image (se a evidência é um print) ou og:video (se é gravação).
Para QA, baixamos só imagens; vídeos retornamos um marcador pra a UI avisar.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Literal, Union

import httpx

JAM_URL_REGEX = re.compile(
    r"https?://(?:www\.)?jam\.dev/c/([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)
OG_IMAGE_REGEX = re.compile(
    r'<meta\s+[^>]*property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
OG_VIDEO_REGEX = re.compile(
    r'<meta\s+[^>]*property=["\']og:video["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

TIMEOUT_SEGUNDOS = 10


def extrair_id_jam(url: str) -> str | None:
    """Retorna o ID Jam se a URL casa com o padrão, senão None."""
    m = JAM_URL_REGEX.search(url)
    return m.group(1) if m else None


def encontrar_links_jam(texto: str) -> list[str]:
    """Devolve todas as URLs Jam.dev encontradas no texto."""
    return [m.group(0) for m in JAM_URL_REGEX.finditer(texto)]


def extrair_og_image(html: str) -> str | None:
    m = OG_IMAGE_REGEX.search(html)
    return m.group(1) if m else None


def extrair_og_video(html: str) -> str | None:
    m = OG_VIDEO_REGEX.search(html)
    return m.group(1) if m else None


def fetch_jam_url(url: str, pasta_destino: Path) -> Union[Path, Literal["video"], None]:
    """Tenta baixar a evidência da URL Jam.

    Retorna:
    - Path do arquivo PNG salvo se for um print
    - 'video' (string) se a página é um vídeo (UI deve avisar)
    - None se URL inválida, 404, ou sem og:image/og:video
    """
    jam_id = extrair_id_jam(url)
    if not jam_id:
        return None

    try:
        resp = httpx.get(url, timeout=TIMEOUT_SEGUNDOS, follow_redirects=True)
    except httpx.HTTPError:
        return None

    if resp.status_code != 200:
        return None

    # Preferência: og:video > og:image. Se vídeo, retorna marcador (não baixamos).
    if extrair_og_video(resp.text):
        return "video"

    img_url = extrair_og_image(resp.text)
    if not img_url:
        return None

    try:
        img_resp = httpx.get(img_url, timeout=TIMEOUT_SEGUNDOS, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if img_resp.status_code != 200:
        return None

    pasta_destino.mkdir(parents=True, exist_ok=True)
    nome = f"jam_{jam_id}_{int(time.time())}.png"
    destino = pasta_destino / nome
    destino.write_bytes(img_resp.content)
    return destino
```

- [ ] **Step 4: Rodar testes — devem PASSAR agora**

Run: `.\.venv\Scripts\python.exe -m pytest tests/app/test_jam_fetcher.py -v`
Esperado: `11 passed`

- [ ] **Step 5: Commit**

```
git add app/services/jam_fetcher.py tests/app/test_jam_fetcher.py
git commit -m "feat(jam_fetcher): detecta e baixa prints do Jam.dev"
```

---

### Task 3: Reescrever evidencias_view.py com UI funcional

**Files:**
- Overwrite: `app/views/evidencias_view.py`

- [ ] **Step 1: Substituir o placeholder pela view funcional**

```python
"""Aba Evidências — gerencia evidências do bug (prints, vídeos, Jam links)."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import flet as ft

from app.icons import Icones
from app.services.clipboard import pegar_imagem_da_clipboard
from app.services.file_dialog import escolher_arquivos
from app.services.jam_fetcher import encontrar_links_jam, fetch_jam_url
from app.state import AppState, Evidencia
from app.theme import Tokens
from app.ui_kit import (
    botao_primario,
    botao_secundario,
    empty_state,
    secao_titulo,
    status_banner,
    titulo_pagina,
    _borda,
)


def _icone_por_tipo_evid(tipo: str) -> str:
    return {
        "print": ft.Icons.IMAGE_OUTLINED,
        "video": ft.Icons.VIDEOCAM_OUTLINED,
        "link": ft.Icons.LINK_OUTLINED,
    }.get(tipo, ft.Icons.INSERT_DRIVE_FILE_OUTLINED)


def _badge_origem(origem: str) -> ft.Container:
    cores = {
        "upload": ("#3B82F622", "#3B82F6"),
        "paste": ("#22C55E22", "#22C55E"),
        "jam": ("#F59E0B22", "#F59E0B"),
    }
    bg, fg = cores.get(origem, ("#A1A1AA22", "#A1A1AA"))
    rotulo = {"upload": "ANEXADO", "paste": "COLADO", "jam": "JAM"}.get(origem, origem.upper())
    return ft.Container(
        content=ft.Text(rotulo, size=Tokens.FONT_XS, color=fg, weight=Tokens.WEIGHT_SEMIBOLD),
        bgcolor=bg,
        border_radius=Tokens.RADIUS_SM,
        padding=ft.Padding(left=6, top=2, right=6, bottom=2),
    )


def _item_evidencia(ev: Evidencia, on_remover: Callable[[Evidencia], None]) -> ft.Container:
    # Miniatura para imagem; ícone para vídeo/link
    if ev.tipo == "print" and ev.path.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        thumb: ft.Control = ft.Image(
            src=str(ev.path),
            width=80,
            height=60,
            fit=ft.ImageFit.COVER,
            border_radius=Tokens.RADIUS_SM,
        )
    else:
        thumb = ft.Container(
            content=ft.Icon(icon=_icone_por_tipo_evid(ev.tipo), color=Tokens.ACCENT, size=32),
            width=80,
            height=60,
            bgcolor=Tokens.BG_PRIMARY,
            border=_borda(),
            border_radius=Tokens.RADIUS_SM,
            alignment=ft.Alignment(0, 0),
        )

    return ft.Container(
        content=ft.Row(
            controls=[
                thumb,
                ft.Column(
                    controls=[
                        ft.Text(
                            ev.nome,
                            color=Tokens.TEXT_PRIMARY,
                            size=Tokens.FONT_SM,
                            weight=Tokens.WEIGHT_MEDIUM,
                        ),
                        ft.Row(
                            controls=[_badge_origem(ev.origem)],
                            spacing=Tokens.SPACE_1,
                            tight=True,
                        ),
                    ],
                    spacing=4,
                    tight=True,
                    expand=True,
                ),
                ft.IconButton(
                    icon=Icones.APAGAR,
                    icon_color=Tokens.ERROR,
                    icon_size=Tokens.FONT_BASE,
                    tooltip="Remover evidência",
                    on_click=lambda _e, e=ev: on_remover(e),
                ),
            ],
            spacing=Tokens.SPACE_3,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=Tokens.BG_PRIMARY,
        border=_borda(),
        border_radius=Tokens.RADIUS_MD,
        padding=Tokens.SPACE_3,
    )


def construir(page: ft.Page, state: AppState) -> ft.Control:
    lista_container = ft.Column(spacing=Tokens.SPACE_2, tight=True)
    status_container = ft.Container(visible=False)

    inicializado = [False]

    def _maybe_update() -> None:
        if inicializado[0]:
            try:
                page.update()
            except Exception:
                pass

    def mostrar(tipo: str, texto: str) -> None:
        status_container.content = status_banner(tipo, texto)
        status_container.visible = True
        _maybe_update()

    def atualizar_lista() -> None:
        if not state.evidencias:
            lista_container.controls = [
                empty_state(
                    Icones.EVIDENCIAS,
                    "Nenhuma evidência ainda",
                    "Anexe um arquivo, cole um print do clipboard, ou cole um link do Jam.dev no caso (aba Caso) e clique em 'Buscar links Jam'.",
                )
            ]
        else:
            lista_container.controls = [_item_evidencia(ev, on_remover) for ev in state.evidencias]
        _maybe_update()

    # ---- Handlers ----

    def _pasta_evidencias() -> Path:
        return state.project_root / "evidencias" / "_sessao_atual"

    def on_anexar(_: ft.ControlEvent) -> None:
        paths = escolher_arquivos(
            titulo="Anexar evidência do bug",
            extensoes=[
                ("Imagens / Vídeos", "*.png *.jpg *.jpeg *.gif *.webp *.mp4 *.mov *.webm"),
                ("Imagens", "*.png *.jpg *.jpeg *.gif *.webp"),
                ("Vídeos", "*.mp4 *.mov *.webm"),
            ],
            multiplo=True,
        )
        if not paths:
            return
        adicionados = 0
        for p in paths:
            tipo = "video" if p.suffix.lower() in (".mp4", ".mov", ".webm") else "print"
            state.adicionar_evidencia(p, tipo, "upload")
            adicionados += 1
        mostrar("ok", f"{adicionados} evidência{'s' if adicionados != 1 else ''} anexada{'s' if adicionados != 1 else ''}.")

    def on_colar(_: ft.ControlEvent) -> None:
        destino = _pasta_evidencias()
        path = pegar_imagem_da_clipboard(destino, prefixo="paste")
        if path is None:
            mostrar("warn", "Nenhuma imagem na área de transferência.")
            return
        state.adicionar_evidencia(path, "print", "paste")
        mostrar("ok", f"Imagem colada como {path.name}.")

    def on_buscar_jam(_: ft.ControlEvent) -> None:
        if not state.caso or not state.caso.texto_bruto:
            mostrar("warn", "Cole um caso na aba 'Caso' e clique Analisar — depois volte aqui.")
            return
        links = encontrar_links_jam(state.caso.texto_bruto)
        if not links:
            mostrar("info", "Nenhum link do Jam.dev encontrado no texto do caso.")
            return
        destino = _pasta_evidencias()
        ok_count = 0
        video_count = 0
        falha_count = 0
        for url in links:
            resultado = fetch_jam_url(url, destino)
            if isinstance(resultado, Path):
                state.adicionar_evidencia(resultado, "print", "jam")
                ok_count += 1
            elif resultado == "video":
                # Cria placeholder simbólico — não baixamos vídeo
                destino.mkdir(parents=True, exist_ok=True)
                marcador = destino / f"video_{len(state.evidencias)}.url"
                marcador.write_text(url, encoding="utf-8")
                state.adicionar_evidencia(marcador, "video", "jam")
                video_count += 1
            else:
                falha_count += 1
        msgs = []
        if ok_count:
            msgs.append(f"{ok_count} print(s) baixado(s)")
        if video_count:
            msgs.append(f"{video_count} vídeo(s) detectado(s) (não analisáveis automaticamente)")
        if falha_count:
            msgs.append(f"{falha_count} falha(s)")
        if msgs:
            tipo = "warn" if video_count or falha_count else "ok"
            mostrar(tipo, "; ".join(msgs) + ".")

    def on_limpar(_: ft.ControlEvent) -> None:
        if not state.evidencias:
            return
        state.limpar_evidencias()
        mostrar("warn", "Todas as evidências foram removidas.")

    def on_remover(ev: Evidencia) -> None:
        state.remover_evidencia(ev)
        mostrar("warn", f"'{ev.nome}' removida.")

    # ---- Inscrições ----

    state.on("evidencias_changed", lambda _lst: atualizar_lista())

    # ---- Layout ----

    botoes = ft.Row(
        controls=[
            botao_primario("Anexar arquivo", on_anexar, icon=Icones.ANEXAR),
            botao_secundario("Colar imagem", on_colar),
            botao_secundario("Buscar links Jam", on_buscar_jam),
            botao_secundario("Limpar tudo", on_limpar),
        ],
        spacing=Tokens.SPACE_2,
        wrap=True,
    )

    atualizar_lista()
    inicializado[0] = True

    return ft.Container(
        content=ft.Column(
            controls=[
                titulo_pagina("Evidências do bug", icone=Icones.EVIDENCIAS),
                ft.Text(
                    "Prints colados, arquivos anexados, ou links do Jam.dev detectados no texto do caso.",
                    color=Tokens.TEXT_MUTED,
                    size=Tokens.FONT_SM,
                ),
                ft.Container(height=Tokens.SPACE_3),
                botoes,
                ft.Container(height=Tokens.SPACE_2),
                status_container,
                lista_container,
            ],
            spacing=Tokens.SPACE_2,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        ),
        padding=Tokens.SPACE_5,
        expand=True,
    )
```

- [ ] **Step 2: Verificar import**

Run: `.\.venv\Scripts\python.exe -c "import app.views.evidencias_view; print('OK')"`
Esperado: `OK`

- [ ] **Step 3: Boot 8s**

Run:
```powershell
$proc = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m","app.main" -PassThru -RedirectStandardError "_err.log" -RedirectStandardOutput "_out.log" -NoNewWindow; Start-Sleep -Seconds 8; if ($proc.HasExited) { "FALHOU"; Get-Content _err.log } else { Stop-Process -Id $proc.Id -Force; "OK 8s"; $e = Get-Content _err.log -ErrorAction SilentlyContinue; if ($e) { "STDERR:"; $e } else { "(stderr vazio)" } }; Remove-Item _err.log, _out.log -ErrorAction SilentlyContinue
```

Esperado: `OK 8s` + `(stderr vazio)`

- [ ] **Step 4: Commit**

```
git add app/views/evidencias_view.py
git commit -m "feat(evidencias): aba funcional com paste, anexar e busca Jam"
```

---

### Task 4: Adicionar `evidencias/_sessao_atual/` no .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Adicionar linha**

Anexar ao final do `.gitignore`:

```
evidencias/_sessao_atual/
```

- [ ] **Step 2: Commit**

```
git add .gitignore
git commit -m "chore(gitignore): ignora evidencias/_sessao_atual"
```

---

### Task 5: Verificação manual

- [ ] **Step 1: Rodar app**

```
.\run.cmd
```

- [ ] **Step 2: Roteiro manual**

1. App abre na shell. Clica aba **Evidências**.
2. Espera ver: título "Evidências do bug" com ícone de imagem, descrição em cinza, 4 botões (Anexar arquivo, Colar imagem, Buscar links Jam, Limpar tudo), empty state centralizado abaixo.
3. **Testar paste**: tira print com Win+Shift+S → clica **Colar imagem**. Esperado: aparece um item na lista com miniatura, nome `paste_<timestamp>.png`, badge verde "COLADO", botão de lixeira.
4. **Testar anexar**: clica **Anexar arquivo**. Abre seletor nativo do Windows. Escolhe um arquivo PNG. Esperado: aparece novo item com badge azul "ANEXADO".
5. **Testar Jam (sem link)**: clica **Buscar links Jam**. Esperado: banner amarelo "Cole um caso na aba 'Caso' e clique Analisar — depois volte aqui."
6. **Testar Jam (com link)**: vai pra aba Caso, cola um texto contendo `https://jam.dev/c/algumacoisa`, clica Analisar. Volta pra aba Evidências, clica Buscar links Jam. Esperado: tenta baixar (vai falhar com `None` pois é link fake — banner amarelo informando 1 falha). Pra testar caminho feliz seria com um link Jam real.
7. **Testar remover**: clica lixeira de um item. Esperado: item some, banner amarelo "removida".
8. **Testar limpar tudo**: clica Limpar tudo. Esperado: lista volta a empty state.

- [ ] **Step 3: Capturar prints (opcional)**

Salvar em `evidencias/_polish/fatia3-*.png` se quiser registrar.

---

## Fora do escopo (próximo)

- **Drag-and-drop** do explorer pro app — Flet 0.85 não tem widget pronto consistente. Se for crítico, fazer task separada com `flet_drag_drop` package.
- **Persistência das evidências entre runs** — hoje vivem só em memória durante a sessão. Quando Fatia 4/5 chegar, salvar em `evidencias/<T-XXXX>/`.
- **Preview ao clicar** numa evidência (lightbox) — futuro.
