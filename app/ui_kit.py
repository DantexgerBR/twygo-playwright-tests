"""Componentes visuais reutilizáveis. Usar daqui para manter coerência."""
from __future__ import annotations

from typing import Callable, Literal, Optional

import flet as ft

from app.theme import Tokens


def _borda(color: str = Tokens.BORDER, width: int = 1) -> ft.Border:
    """Cria uma Border uniforme em todos os 4 lados."""
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def _padding(horizontal: int = 0, vertical: int = 0) -> ft.Padding:
    """Padding simétrico (horizontal × vertical)."""
    return ft.Padding(left=horizontal, top=vertical, right=horizontal, bottom=vertical)


def card(
    content: ft.Control,
    *,
    padding: int | None = None,
    elevated: bool = False,
) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=Tokens.BG_ELEVATED if elevated else Tokens.BG_SURFACE,
        border_radius=Tokens.RADIUS_LG,
        padding=padding if padding is not None else Tokens.SPACE_5,
        border=_borda(),
    )


def _botao_base(
    label: str,
    on_click: Callable,
    *,
    icon: Optional[str] = None,
    bg: str,
    fg: str,
    border_color: Optional[str] = None,
    icon_color: Optional[str] = None,
) -> ft.Container:
    """Botão usando Container clicável (não usa ElevatedButton/OutlinedButton).

    No Flet 0.85 desktop, os botões Material dentro de AlertDialog estavam não
    respondendo a cliques. Container.on_click é a primitiva mais confiável.
    """
    children: list[ft.Control] = []
    if icon:
        children.append(
            ft.Icon(icon=icon, color=icon_color or fg, size=Tokens.FONT_BASE)
        )
    children.append(
        ft.Text(
            label,
            color=fg,
            weight=Tokens.WEIGHT_SEMIBOLD,
            size=Tokens.FONT_SM,
        )
    )
    border = None
    if border_color:
        side = ft.BorderSide(1, border_color)
        border = ft.Border(top=side, right=side, bottom=side, left=side)
    return ft.Container(
        content=ft.Row(
            controls=children,
            spacing=Tokens.SPACE_2,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=bg,
        border=border,
        border_radius=Tokens.RADIUS_MD,
        padding=ft.Padding(
            left=Tokens.SPACE_4,
            top=Tokens.SPACE_3,
            right=Tokens.SPACE_4,
            bottom=Tokens.SPACE_3,
        ),
        on_click=on_click,
        ink=True,
        tooltip=label,
    )


def botao_primario(
    label: str,
    on_click: Callable,
    *,
    icon: Optional[str] = None,
) -> ft.Container:
    return _botao_base(
        label,
        on_click,
        icon=icon,
        bg=Tokens.ACCENT,
        fg=Tokens.BG_PRIMARY,
    )


def botao_secundario(label: str, on_click: Callable) -> ft.Container:
    return _botao_base(
        label,
        on_click,
        bg="#00000000",
        fg=Tokens.TEXT_PRIMARY,
        border_color=Tokens.BORDER,
    )


def botao_texto(
    label: str,
    on_click: Callable,
    *,
    icon: Optional[str] = None,
    cor: Optional[str] = None,
) -> ft.Container:
    """Botão minimalista, sem fundo nem borda. Bom para ações terciárias."""
    return _botao_base(
        label,
        on_click,
        icon=icon,
        bg="#00000000",
        fg=cor or Tokens.TEXT_MUTED,
        icon_color=cor or Tokens.TEXT_MUTED,
    )


def campo_texto(
    label: str = "",
    *,
    valor: str = "",
    senha: bool = False,
    hint: str = "",
) -> ft.TextField:
    """Cria um TextField estilizado. Largura é controlada pelo parent (Column/Row).

    NÃO usar `expand=True` em TextField — isso faz ele crescer verticalmente em
    Column e achatar/esticar o input. Em Row, controle a divisão com expand= no
    Column wrapper (via _campo_com_label).
    """
    return ft.TextField(
        label=label or None,
        value=valor,
        password=senha,
        can_reveal_password=senha,
        hint_text=hint or None,
        hint_style=ft.TextStyle(color=Tokens.TEXT_MUTED, size=Tokens.FONT_SM),
        bgcolor=Tokens.BG_PRIMARY,
        color=Tokens.TEXT_PRIMARY,
        border_color=Tokens.BORDER,
        focused_border_color=Tokens.ACCENT,
        label_style=ft.TextStyle(color=Tokens.TEXT_MUTED, size=Tokens.FONT_SM),
        text_size=Tokens.FONT_SM,
        border_radius=Tokens.RADIUS_MD,
        content_padding=ft.Padding(left=12, top=10, right=12, bottom=10),
    )


def rotulo_campo(texto: str) -> ft.Text:
    """Label que vai acima de um TextField (em vez do label flutuante interno)."""
    return ft.Text(
        texto,
        size=Tokens.FONT_SM,
        color=Tokens.TEXT_PRIMARY,
        weight=Tokens.WEIGHT_MEDIUM,
    )


def secao_titulo(texto: str, *, sutil: bool = False) -> ft.Text:
    """Título de uma seção dentro de um card/dialog."""
    return ft.Text(
        texto,
        size=Tokens.FONT_BASE,
        color=Tokens.TEXT_MUTED if sutil else Tokens.TEXT_PRIMARY,
        weight=Tokens.WEIGHT_SEMIBOLD,
    )


def status_banner(
    tipo: Literal["info", "warn", "error", "ok"],
    texto: str,
) -> ft.Container:
    cores_fundo = {
        "info": "#3B82F622",
        "warn": "#F59E0B22",
        "error": "#DC262622",
        "ok": "#16A34A22",
    }
    cores_borda = {
        "info": "#3B82F6",
        "warn": Tokens.WARNING,
        "error": Tokens.ERROR,
        "ok": Tokens.SUCCESS,
    }
    icones = {
        "info": ft.Icons.INFO_OUTLINE,
        "warn": ft.Icons.WARNING_AMBER_OUTLINED,
        "error": ft.Icons.ERROR_OUTLINE,
        "ok": ft.Icons.CHECK_CIRCLE_OUTLINE,
    }
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(
                    icon=icones[tipo],
                    color=cores_borda[tipo],
                    size=Tokens.FONT_BASE,
                ),
                ft.Text(
                    texto,
                    color=Tokens.TEXT_PRIMARY,
                    size=Tokens.FONT_SM,
                    expand=True,
                ),
            ],
            spacing=Tokens.SPACE_2,
        ),
        bgcolor=cores_fundo[tipo],
        border=_borda(color=cores_borda[tipo]),
        border_radius=Tokens.RADIUS_MD,
        padding=Tokens.SPACE_3,
    )


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
