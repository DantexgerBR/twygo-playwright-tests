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
