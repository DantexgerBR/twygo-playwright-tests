"""Twygo QA Tester — entrada do aplicativo desktop (Flet).

Rodar com:
    python -m app.main
    .\run.cmd  (atalho que pega o python do venv automaticamente)
"""
from __future__ import annotations

from pathlib import Path

import flet as ft

from app.services.credentials import Credenciais, carregar
from app.state import AppState
from app.theme import Tokens, configurar_pagina
from app.ui_kit import _borda
from app.views import (
    caso_view,
    documentacao_view,
    evidencias_view,
    execucao_view,
    resultado_view,
)
from app.views.login_view import construir_tela_login
from app.icons import Icones
from app.ui_kit import label_aba

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Seletor de modo (Retrabalho / Caso T-XXXX)
# ---------------------------------------------------------------------------


def _seletor_modo(state: AppState, on_change) -> ft.Container:
    def _botao_modo(label: str, modo: str, icone: str) -> ft.Container:
        ativo = state.modo == modo
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        icone,
                        color=Tokens.BG_PRIMARY if ativo else Tokens.TEXT_MUTED,
                        size=Tokens.FONT_BASE,
                    ),
                    ft.Text(
                        label,
                        color=Tokens.BG_PRIMARY if ativo else Tokens.TEXT_PRIMARY,
                        weight=Tokens.WEIGHT_SEMIBOLD if ativo else Tokens.WEIGHT_MEDIUM,
                        size=Tokens.FONT_SM,
                    ),
                ],
                spacing=Tokens.SPACE_1,
                tight=True,
            ),
            bgcolor=Tokens.ACCENT if ativo else "#00000000",
            border_radius=Tokens.RADIUS_SM,
            padding=ft.Padding(left=Tokens.SPACE_3, top=6, right=Tokens.SPACE_3, bottom=6),
            on_click=lambda _e: on_change(modo),
            tooltip=(
                "Validação rápida de correção de bug do Artia"
                if modo == "retrabalho"
                else "Caso de teste estruturado com objetivo, pré-condições e passos"
            ),
        )

    return ft.Container(
        content=ft.Row(
            controls=[
                _botao_modo("Retrabalho", "retrabalho", Icones.MODO_RETRABALHO),
                _botao_modo("Caso T-XXXX", "caso_teste", Icones.MODO_CASO_TESTE),
            ],
            spacing=4,
            tight=True,
        ),
        bgcolor=Tokens.BG_ELEVATED,
        border_radius=Tokens.RADIUS_MD,
        border=_borda(),
        padding=4,
    )


# ---------------------------------------------------------------------------
# Shell principal (header + abas)
# ---------------------------------------------------------------------------


def _shell_principal(page: ft.Page, state: AppState) -> ft.Control:
    seletor_container = ft.Container()

    def reconstruir_seletor() -> None:
        seletor_container.content = _seletor_modo(state, on_modo_change)
        page.update()

    def on_modo_change(novo_modo: str) -> None:
        state.set_modo(novo_modo)  # type: ignore[arg-type]
        reconstruir_seletor()

    reconstruir_seletor()

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(
                            icon=Icones.LOGO,
                            color=Tokens.ACCENT,
                            size=Tokens.FONT_XL,
                        ),
                        ft.Text(
                            "Twygo QA Tester",
                            size=Tokens.FONT_LG,
                            weight=Tokens.WEIGHT_BOLD,
                            color=Tokens.TEXT_PRIMARY,
                        ),
                    ],
                    spacing=Tokens.SPACE_2,
                    tight=True,
                ),
                ft.Container(expand=True),
                seletor_container,
                ft.IconButton(
                    icon=Icones.SETTINGS,
                    tooltip="Configurar credenciais",
                    icon_color=Tokens.TEXT_MUTED,
                    on_click=lambda _e: _mostrar_tela_login(page, state, com_cancelar=True),
                ),
            ],
            spacing=Tokens.SPACE_3,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=Tokens.BG_SURFACE,
        padding=ft.Padding(
            left=Tokens.SPACE_5,
            top=Tokens.SPACE_3,
            right=Tokens.SPACE_3,
            bottom=Tokens.SPACE_3,
        ),
        border=ft.Border(bottom=ft.BorderSide(1, Tokens.BORDER)),
    )

    # Construímos os conteúdos das 5 abas (uma vez só, mantém estado interno).
    # Cada tupla: (icone Material, label, conteúdo)
    conteudos_abas: list[tuple[str, str, ft.Control]] = [
        (Icones.DOC, "Documentação", documentacao_view.construir(page, state)),
        (Icones.CASO, "Caso", caso_view.construir(page, state)),
        (Icones.EVIDENCIAS, "Evidências", evidencias_view.construir(page, state)),
        (Icones.EXECUCAO, "Execução", execucao_view.construir(page, state)),
        (Icones.RESULTADO, "Resultado", resultado_view.construir(page, state)),
    ]

    aba_ativa = [0]  # mutable, capturado pelo closure
    conteudo_container = ft.Container(content=conteudos_abas[0][2], expand=True)
    botoes_aba_row = ft.Row(spacing=0, tight=True)

    def construir_botao_aba(idx: int) -> ft.Container:
        ativo = idx == aba_ativa[0]
        icone, texto, _ = conteudos_abas[idx]
        return ft.Container(
            content=label_aba(icone, texto, ativo),
            padding=ft.Padding(
                left=Tokens.SPACE_4,
                top=Tokens.SPACE_3,
                right=Tokens.SPACE_4,
                bottom=Tokens.SPACE_3,
            ),
            border=ft.Border(
                bottom=ft.BorderSide(
                    2 if ativo else 0,
                    Tokens.ACCENT if ativo else "#00000000",
                )
            ),
            on_click=lambda _e, i=idx: trocar_aba(i),
            ink=True,
        )

    def reconstruir_barra() -> None:
        botoes_aba_row.controls = [construir_botao_aba(i) for i in range(len(conteudos_abas))]
        page.update()

    def trocar_aba(idx: int) -> None:
        aba_ativa[0] = idx
        conteudo_container.content = conteudos_abas[idx][2]
        reconstruir_barra()

    reconstruir_barra()

    barra_abas = ft.Container(
        content=botoes_aba_row,
        bgcolor=Tokens.BG_SURFACE,
        border=ft.Border(bottom=ft.BorderSide(1, Tokens.BORDER)),
    )

    return ft.Column(
        controls=[header, barra_abas, conteudo_container],
        spacing=0,
        expand=True,
    )


# ---------------------------------------------------------------------------
# Login (Fatia 1)
# ---------------------------------------------------------------------------


def _mostrar_tela_login(
    page: ft.Page, state: AppState, *, com_cancelar: bool = False
) -> None:
    """Substitui o conteúdo da página pela tela de login.

    Se com_cancelar=True (usuário abriu via ⚙), Cancelar volta para a shell.
    Se False (primeira execução, sem creds), Cancelar é omitido — não há shell pra voltar.
    """
    def on_success(nova_cred: Credenciais) -> None:
        state.set_credenciais(nova_cred)
        page.controls.clear()
        page.controls.append(_shell_principal(page, state))
        page.update()

    def on_cancelar_volta() -> None:
        page.controls.clear()
        page.controls.append(_shell_principal(page, state))
        page.update()

    tela = construir_tela_login(
        page,
        PROJECT_ROOT,
        on_success,
        on_cancelar=on_cancelar_volta if com_cancelar else None,
    )
    page.controls.clear()
    page.controls.append(tela)
    page.update()


def _tela_inicial_vazia() -> ft.Control:
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "Twygo QA Tester",
                    size=Tokens.FONT_XXL,
                    weight=Tokens.WEIGHT_BOLD,
                    color=Tokens.TEXT_PRIMARY,
                ),
                ft.Container(height=Tokens.SPACE_2),
                ft.Text(
                    "Preencha o dialog de configuração para começar.",
                    color=Tokens.TEXT_MUTED,
                    size=Tokens.FONT_SM,
                ),
            ],
        ),
        padding=Tokens.SPACE_6,
        expand=True,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(page: ft.Page) -> None:
    print("[main] inicio", flush=True)
    page.title = "Twygo QA Tester"
    # Nota: page.window.* não existe mais no Flet 0.85; tamanho da janela
    # fica no default do Flet desktop. Pode ser ajustado depois via ft.Window.
    configurar_pagina(page)
    print("[main] pagina configurada", flush=True)

    state = AppState(PROJECT_ROOT)
    state.restaurar()
    print("[main] state restaurado", flush=True)

    cred = carregar(PROJECT_ROOT)
    state.set_credenciais(cred)
    print(f"[main] cred completo? {cred.completo_para_admin()}", flush=True)

    if not cred.completo_para_admin():
        print("[main] mostrando tela login", flush=True)
        _mostrar_tela_login(page, state, com_cancelar=False)
        print("[main] tela login montada", flush=True)
    else:
        print("[main] construindo shell", flush=True)
        page.controls.append(_shell_principal(page, state))
        page.update()
        print("[main] shell montada e atualizada", flush=True)

    print("[main] fim de main()", flush=True)


if __name__ == "__main__":
    ft.run(main)
