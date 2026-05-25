"""Aba Resultado — mostra laudo do agente, comparação visual, KQA e botão de commit."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

import flet as ft

from app.icons import Icones
from app.services.git_committer import CommitFalhou, commitar_evidencias
from app.services.kqa_comment import gerar_comentario_kqa
from app.state import AppState, ResultadoExecucao
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


_CORES_LAUDO = {
    "corrigido": ("ok", Icones.OK, "Corrigido"),
    "ainda_quebrado": ("error", Icones.ERRO, "Ainda quebrado"),
    "inconclusivo": ("warn", Icones.AVISO, "Inconclusivo"),
}


def construir(page: ft.Page, state: AppState) -> ft.Control:
    inicializado = [False]
    commit_em_andamento = [False]

    def _maybe_update():
        if inicializado[0]:
            try:
                page.update()
            except Exception:
                pass

    raiz = ft.Container()

    def _comparacao_lado_a_lado(resultado: ResultadoExecucao) -> ft.Control:
        """Mostra evidência original × screenshot final do agente."""
        ev_path = resultado.evidencia_referencia
        if not ev_path or not ev_path.exists():
            # Fallback: pega a primeira evidência do state
            for ev in state.evidencias:
                if ev.tipo == "print" and ev.path.exists():
                    ev_path = ev.path
                    break

        sc_final: Optional[Path] = None
        if resultado.screenshots:
            sc_final = resultado.screenshots[-1]

        col_esquerda: list[ft.Control] = [
            ft.Text("Evidência original do bug", color=Tokens.TEXT_MUTED, size=Tokens.FONT_SM),
        ]
        if ev_path and ev_path.exists() and ev_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            col_esquerda.append(
                ft.Image(src=str(ev_path), fit=ft.BoxFit.CONTAIN, border_radius=Tokens.RADIUS_SM)
            )
        else:
            col_esquerda.append(ft.Text("(sem print)", color=Tokens.TEXT_MUTED, size=Tokens.FONT_XS))

        col_direita: list[ft.Control] = [
            ft.Text("Estado final do agente", color=Tokens.TEXT_MUTED, size=Tokens.FONT_SM),
        ]
        if sc_final and sc_final.exists():
            col_direita.append(
                ft.Image(src=str(sc_final), fit=ft.BoxFit.CONTAIN, border_radius=Tokens.RADIUS_SM)
            )
        else:
            col_direita.append(ft.Text("(sem screenshot)", color=Tokens.TEXT_MUTED, size=Tokens.FONT_XS))

        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(col_esquerda, spacing=Tokens.SPACE_2, tight=True),
                    expand=1,
                    bgcolor=Tokens.BG_PRIMARY,
                    border=_borda(),
                    border_radius=Tokens.RADIUS_MD,
                    padding=Tokens.SPACE_3,
                ),
                ft.Container(
                    content=ft.Column(col_direita, spacing=Tokens.SPACE_2, tight=True),
                    expand=1,
                    bgcolor=Tokens.BG_PRIMARY,
                    border=_borda(),
                    border_radius=Tokens.RADIUS_MD,
                    padding=Tokens.SPACE_3,
                ),
            ],
            spacing=Tokens.SPACE_3,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def _laudo_card(resultado: ResultadoExecucao) -> ft.Container:
        tipo, icone, label = _CORES_LAUDO.get(resultado.laudo, ("warn", Icones.AVISO, resultado.laudo))
        return ft.Container(
            content=status_banner(tipo, f"Laudo: {label}"),
            padding=ft.Padding(left=0, top=0, right=0, bottom=0),
        )

    def _kqa_widget(resultado: ResultadoExecucao) -> ft.Container:
        evidencias_paths = [ev.path for ev in state.evidencias if ev.path.exists()]
        evidencias_paths.extend(resultado.screenshots)

        texto_kqa = gerar_comentario_kqa(
            resultado.laudo,
            resultado.justificativa,
            evidencias_paths,
            commit_url=resultado.commit_url or "",
        )

        text_field = ft.TextField(
            value=texto_kqa,
            multiline=True,
            min_lines=10,
            max_lines=20,
            read_only=True,
            bgcolor=Tokens.BG_PRIMARY,
            color=Tokens.TEXT_PRIMARY,
            border_color=Tokens.BORDER,
            text_size=Tokens.FONT_SM,
            content_padding=ft.Padding(left=12, top=10, right=12, bottom=10),
        )

        def on_copiar(_):
            try:
                page.set_clipboard(texto_kqa)
                badge_copiou.content = status_banner("ok", "Comentário copiado pra área de transferência.")
                badge_copiou.visible = True
                _maybe_update()
            except Exception as e:
                badge_copiou.content = status_banner("error", f"Falhou copiar: {e}")
                badge_copiou.visible = True
                _maybe_update()

        badge_copiou = ft.Container(visible=False)

        return ft.Container(
            content=ft.Column(
                controls=[
                    secao_titulo("Comentário KQA (cola no Artia)", sutil=True),
                    text_field,
                    ft.Row(
                        controls=[botao_secundario("Copiar comentário", on_copiar)],
                        spacing=Tokens.SPACE_2,
                    ),
                    badge_copiou,
                ],
                spacing=Tokens.SPACE_2,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

    def _commit_widget(resultado: ResultadoExecucao) -> ft.Container:
        status_commit = ft.Container(visible=False)

        def on_commitar(_):
            if commit_em_andamento[0]:
                return
            commit_em_andamento[0] = True
            status_commit.content = status_banner("info", "Commitando evidências…")
            status_commit.visible = True
            _maybe_update()

            def rodar():
                try:
                    pasta = state.project_root / "evidencias" / "_sessao_atual"
                    mensagem = (
                        f"evidencias: laudo={resultado.laudo} - "
                        f"{(resultado.justificativa or '').splitlines()[0][:60]}"
                    )
                    result = commitar_evidencias(
                        state.project_root, pasta, mensagem, push=True
                    )
                    if result is None:
                        status_commit.content = status_banner(
                            "warn",
                            "Nada pra commitar — pasta de evidências está vazia ou já commitada.",
                        )
                    else:
                        resultado.commit_sha = result.sha
                        resultado.commit_url = result.url
                        # Notifica state pra reconstruir a UI com a URL no KQA
                        state.set_resultado(resultado)
                        link = result.url or f"(SHA {result.sha})"
                        status_commit.content = status_banner(
                            "ok", f"Commit {result.sha} feito. {link}"
                        )
                except CommitFalhou as e:
                    status_commit.content = status_banner("error", f"Commit falhou: {e}")
                except Exception as e:
                    status_commit.content = status_banner("error", f"Erro inesperado: {e}")
                finally:
                    commit_em_andamento[0] = False
                    status_commit.visible = True
                    _maybe_update()

            threading.Thread(target=rodar, daemon=True).start()

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            botao_primario(
                                "Commitar evidências",
                                on_commitar,
                                icon=Icones.SALVAR,
                            ),
                        ],
                        spacing=Tokens.SPACE_2,
                    ),
                    status_commit,
                ],
                spacing=Tokens.SPACE_2,
            ),
        )

    def _log_widget(resultado: ResultadoExecucao) -> ft.Container:
        log_text = ft.Text(
            "\n".join(resultado.log) if resultado.log else "(sem log)",
            color=Tokens.TEXT_MUTED,
            size=Tokens.FONT_XS,
            selectable=True,
            font_family="Consolas",
        )
        return ft.Container(
            content=ft.Column(
                controls=[
                    secao_titulo("Log da execução", sutil=True),
                    ft.Container(
                        content=ft.Column(controls=[log_text], scroll=ft.ScrollMode.AUTO, tight=True),
                        bgcolor=Tokens.BG_PRIMARY,
                        border=_borda(),
                        border_radius=Tokens.RADIUS_MD,
                        padding=Tokens.SPACE_3,
                        height=200,
                    ),
                ],
                spacing=Tokens.SPACE_2,
            ),
        )

    def reconstruir_view():
        resultado = state.resultado
        if resultado is None:
            raiz.content = ft.Container(
                content=empty_state(
                    Icones.RESULTADO,
                    "Sem resultado ainda",
                    "Execute um teste na aba 'Execução' — o laudo, comparação visual e comentário KQA aparecem aqui automaticamente.",
                ),
                padding=Tokens.SPACE_5,
                expand=True,
                alignment=ft.Alignment(0, 0),
            )
            _maybe_update()
            return

        meta = ft.Text(
            f"Iterações: {resultado.iteracoes} · {len(resultado.screenshots)} screenshot(s)"
            + (f" · commit {resultado.commit_sha}" if resultado.commit_sha else ""),
            color=Tokens.TEXT_MUTED,
            size=Tokens.FONT_XS,
        )

        raiz.content = ft.Container(
            content=ft.Column(
                controls=[
                    titulo_pagina("Resultado da execução", icone=Icones.RESULTADO),
                    _laudo_card(resultado),
                    ft.Text(
                        resultado.justificativa or "(sem justificativa)",
                        color=Tokens.TEXT_PRIMARY,
                        size=Tokens.FONT_SM,
                    ),
                    meta,
                    ft.Container(height=Tokens.SPACE_3),
                    secao_titulo("Comparação visual"),
                    _comparacao_lado_a_lado(resultado),
                    ft.Container(height=Tokens.SPACE_3),
                    _kqa_widget(resultado),
                    ft.Container(height=Tokens.SPACE_3),
                    _commit_widget(resultado),
                    ft.Container(height=Tokens.SPACE_3),
                    _log_widget(resultado),
                ],
                spacing=Tokens.SPACE_2,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=Tokens.SPACE_5,
            expand=True,
        )
        _maybe_update()

    state.on("resultado_changed", lambda _r: reconstruir_view())

    reconstruir_view()
    inicializado[0] = True
    return raiz
