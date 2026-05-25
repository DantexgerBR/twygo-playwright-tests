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

    def _pasta_evidencias() -> Path:
        return state.project_root / "evidencias" / "_sessao_atual"

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
