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
