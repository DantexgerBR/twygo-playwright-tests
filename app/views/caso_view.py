"""Aba 📋 Caso — recebe texto do retrabalho/caso T-XXXX e parseia."""
from __future__ import annotations

import flet as ft

from app.state import AppState, CasoParseado
from app.theme import Tokens
from app.icons import Icones
from app.ui_kit import (
    botao_primario,
    botao_secundario,
    rotulo_campo,
    secao_titulo,
    status_banner,
    titulo_pagina,
    _borda,
)


PLACEHOLDER_RETRABALHO = """:: Incidente identificado ::
Em cards de atividade do tipo Página na aba de Design de um modelo, foi observado que não exibe o texto centralizado e corta parte do texto no card.

    :: Passo a passo para reprodução ::
» Editar modelo
» Design
» Editar Página
» Inserir texto
» Visualizar card em aba Design

    :: Comportamento esperado ::
Apresentar texto centralizado possibilitando a visualização sem cortar o texto"""

PLACEHOLDER_CASO_TESTE = """Validar que a marca d'água acompanha o vídeo durante a reprodução

Pré-condições
- Existir uma atividade de vídeo com marca d'água configurada
- Estar logado como aluno

Perfil de usuário: Aluno
Tipo de ambiente: Principal (stage)

#   Ações do Passo                                Resultados Esperados             Execução  Status
1   Abrir o curso e iniciar o player              Player carrega e exibe vídeo     Manual    Passou
2   Aguardar 2 segundos                           Marca d'água aparece sobre vídeo Manual    Passou
3   Reproduzir até o meio do vídeo                Marca d'água acompanha posição   Manual    Passou"""


def construir(page: ft.Page, state: AppState) -> ft.Control:
    # Textarea principal
    texto_field = ft.TextField(
        multiline=True,
        min_lines=14,
        max_lines=20,
        hint_text=PLACEHOLDER_RETRABALHO,
        hint_style=ft.TextStyle(color=Tokens.TEXT_MUTED, size=Tokens.FONT_SM),
        bgcolor=Tokens.BG_PRIMARY,
        color=Tokens.TEXT_PRIMARY,
        border_color=Tokens.BORDER,
        focused_border_color=Tokens.ACCENT,
        text_size=Tokens.FONT_SM,
        border_radius=Tokens.RADIUS_MD,
        content_padding=ft.Padding(left=12, top=10, right=12, bottom=10),
    )

    # Banner de status (parse OK / erro)
    status_container = ft.Container(visible=False)

    # Painel de resumo (objetivo + passos)
    resumo_objetivo = ft.Text(
        "",
        color=Tokens.TEXT_PRIMARY,
        size=Tokens.FONT_SM,
        weight=Tokens.WEIGHT_MEDIUM,
    )
    resumo_pre = ft.Text("", color=Tokens.TEXT_MUTED, size=Tokens.FONT_SM)
    lista_passos = ft.Column(spacing=Tokens.SPACE_2, tight=True)
    container_resumo = ft.Container(visible=False)

    # Hint sobre o modo atual
    hint_modo = ft.Text(
        "",
        color=Tokens.TEXT_MUTED,
        size=Tokens.FONT_SM,
    )

    inicializado = [False]

    def _maybe_update() -> None:
        if inicializado[0]:
            try:
                page.update()
            except Exception:
                pass

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

    def mostrar_status(tipo: str, texto: str) -> None:
        status_container.content = status_banner(tipo, texto)
        status_container.visible = True
        _maybe_update()

    def esconder_status() -> None:
        status_container.visible = False
        _maybe_update()

    def _item_passo(n: int, acao: str, esperado: str) -> ft.Container:
        coluna_texto = [
            ft.Text(
                acao,
                color=Tokens.TEXT_PRIMARY,
                size=Tokens.FONT_SM,
                weight=Tokens.WEIGHT_MEDIUM,
            ),
        ]
        if esperado:
            coluna_texto.append(
                ft.Text(
                    f"Esperado: {esperado}",
                    color=Tokens.TEXT_MUTED,
                    size=Tokens.FONT_XS,
                )
            )
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            str(n),
                            color=Tokens.BG_PRIMARY,
                            size=Tokens.FONT_SM,
                            weight=Tokens.WEIGHT_BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        bgcolor=Tokens.ACCENT,
                        border_radius=Tokens.RADIUS_SM,
                        width=28,
                        height=28,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(
                        controls=coluna_texto,
                        spacing=2,
                        tight=True,
                        expand=True,
                    ),
                ],
                spacing=Tokens.SPACE_3,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor=Tokens.BG_PRIMARY,
            border=_borda(),
            border_radius=Tokens.RADIUS_MD,
            padding=Tokens.SPACE_3,
        )

    def on_analisar(_: ft.ControlEvent) -> None:
        texto = (texto_field.value or "").strip()
        if not texto:
            mostrar_status("warn", "Cole o texto do caso antes de analisar.")
            container_resumo.visible = False
            _maybe_update()
            return

        try:
            if state.modo == "retrabalho":
                from app.services.retrabalho_parser import parse_retrabalho
                caso = parse_retrabalho(texto)
            else:
                from ui.parser import parse_caso
                caso_raw = parse_caso(texto)
                caso = CasoParseado(
                    objetivo=caso_raw.objetivo or "",
                    pre_condicoes=list(caso_raw.pre_condicoes),
                    passos=[
                        {"n": p.n, "acao": p.acao, "esperado": p.esperado}
                        for p in caso_raw.passos
                    ],
                    perfil=caso_raw.perfil,
                    plataforma=caso_raw.plataforma,
                    ambiente=caso_raw.ambiente,
                    texto_bruto=texto,
                )
        except Exception as e:
            mostrar_status("error", f"Parser falhou: {e}")
            return

        state.set_caso(caso)

        if not caso.tem_passos:
            if state.modo == "retrabalho":
                msg = (
                    "Não encontrei passos no texto. Em modo Retrabalho, espero "
                    "linhas começando com » dentro de uma seção `:: Passo a passo "
                    "para reprodução ::`."
                )
            else:
                msg = (
                    "Não encontrei passos no texto. Em modo Caso T-XXXX, espero "
                    "uma tabela com colunas 'Ações do Passo' e 'Resultados Esperados'."
                )
            mostrar_status("warn", msg)
            container_resumo.visible = False
            _maybe_update()
            return

        # Popula resumo
        resumo_objetivo.value = caso.objetivo or "(sem objetivo identificado)"
        if caso.pre_condicoes:
            resumo_pre.value = f"Pré-condições: {len(caso.pre_condicoes)}"
        else:
            resumo_pre.value = "Sem pré-condições explícitas."

        lista_passos.controls = [
            _item_passo(p["n"], p["acao"], p["esperado"]) for p in caso.passos
        ]
        container_resumo.visible = True
        mostrar_status("ok", f"Caso parseado: {len(caso.passos)} passos.")

    def on_limpar(_: ft.ControlEvent) -> None:
        texto_field.value = ""
        state.set_caso(None)
        container_resumo.visible = False
        esconder_status()

    botoes = ft.Row(
        controls=[
            botao_primario("Analisar", on_analisar, icon=Icones.ANALISAR),
            botao_secundario("Limpar", on_limpar),
        ],
        spacing=Tokens.SPACE_2,
    )

    container_resumo.content = ft.Column(
        controls=[
            secao_titulo("Resumo do caso", sutil=True),
            resumo_objetivo,
            resumo_pre,
            ft.Container(height=Tokens.SPACE_2),
            ft.Text(
                "Passos detectados:",
                color=Tokens.TEXT_MUTED,
                size=Tokens.FONT_SM,
            ),
            lista_passos,
        ],
        spacing=Tokens.SPACE_2,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    # Reage a mudanças de modo
    state.on("modo_changed", lambda _m: atualizar_hint_modo())
    atualizar_hint_modo()

    # Daqui pra frente, page.update() é seguro (a view sera anexada)
    inicializado[0] = True

    return ft.Container(
        content=ft.Column(
            controls=[
                titulo_pagina("Caso de teste", icone=Icones.CASO),
                hint_modo,
                ft.Container(height=Tokens.SPACE_2),
                rotulo_campo("Cole o texto do caso abaixo"),
                texto_field,
                botoes,
                status_container,
                container_resumo,
            ],
            spacing=Tokens.SPACE_2,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=Tokens.SPACE_5,
        expand=True,
    )
