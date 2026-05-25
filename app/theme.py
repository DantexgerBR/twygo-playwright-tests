"""Tokens de design do app QA. Importar daqui para manter consistência visual.

Default: tema escuro com paleta roxa da Twygo.
"""
from __future__ import annotations

import flet as ft


class Tokens:
    BG_PRIMARY = "#0F1014"
    BG_SURFACE = "#1A1B22"
    BG_ELEVATED = "#23252E"
    TEXT_PRIMARY = "#F4F4F5"
    TEXT_MUTED = "#A1A1AA"
    ACCENT = "#A78BFA"
    ACCENT_HOVER = "#C4B5FD"
    SUCCESS = "#22C55E"
    WARNING = "#FBBF24"
    ERROR = "#EF4444"
    BORDER = "#27272A"

    FONT_FAMILY = "Inter"

    FONT_XS = 12
    FONT_SM = 14
    FONT_BASE = 16
    FONT_LG = 20
    FONT_XL = 24
    FONT_XXL = 32

    WEIGHT_NORMAL = ft.FontWeight.W_400
    WEIGHT_MEDIUM = ft.FontWeight.W_500
    WEIGHT_SEMIBOLD = ft.FontWeight.W_600
    WEIGHT_BOLD = ft.FontWeight.W_700

    # ---- Escala de tipografia sugerida (usar conforme contexto) ----
    # H1 (título de página): FONT_LG (20) com WEIGHT_BOLD
    # H2 (título de seção): FONT_BASE (16) com WEIGHT_SEMIBOLD
    # Body: FONT_SM (14) com WEIGHT_NORMAL
    # Caption: FONT_XS (12) com WEIGHT_NORMAL ou WEIGHT_MEDIUM
    # Destaque grande (laudo, preço): FONT_XXL (32) com WEIGHT_BOLD

    SPACE_1 = 4
    SPACE_2 = 8
    SPACE_3 = 12
    SPACE_4 = 16
    SPACE_5 = 24
    SPACE_6 = 32
    SPACE_8 = 48
    SPACE_10 = 64

    RADIUS_SM = 6
    RADIUS_MD = 8
    RADIUS_LG = 12


def configurar_pagina(page: ft.Page) -> None:
    """Aplica defaults visuais na página, sem nada que dependa de rede.

    NÃO carregar fontes via URL (Google Fonts) aqui — Flutter trava na render
    enquanto baixa, e se a rede for lenta/bloqueada, fica em 'Working...'
    infinito no desktop. Usa a fonte do sistema (Segoe UI no Windows).
    """
    page.bgcolor = Tokens.BG_PRIMARY
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
