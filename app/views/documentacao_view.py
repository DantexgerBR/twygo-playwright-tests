"""Aba 📚 Documentação — gerencia docs persistentes por projeto."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import flet as ft

from app.services.clipboard import pegar_imagem_da_clipboard
from app.state import AppState, Documento
from app.theme import Tokens
from app.icons import Icones
from app.ui_kit import (
    botao_primario,
    botao_secundario,
    campo_texto,
    card,
    empty_state,
    rotulo_campo,
    secao_titulo,
    status_banner,
    titulo_pagina,
    _borda,
)


def _icone_por_tipo(tipo: str) -> str:
    return {
        "md": ft.Icons.ARTICLE_OUTLINED,
        "txt": ft.Icons.DESCRIPTION_OUTLINED,
        "pdf": ft.Icons.PICTURE_AS_PDF_OUTLINED,
        "imagem": ft.Icons.IMAGE_OUTLINED,
    }.get(tipo, ft.Icons.INSERT_DRIVE_FILE_OUTLINED)


def _formato_tamanho(path: Path) -> str:
    try:
        size = path.stat().st_size
    except OSError:
        return "?"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _item_doc(doc: Documento, on_remover) -> ft.Container:
    detalhes = [
        ft.Text(doc.tipo.upper(), size=Tokens.FONT_XS, color=Tokens.TEXT_MUTED),
        ft.Text("•", size=Tokens.FONT_XS, color=Tokens.TEXT_MUTED),
        ft.Text(_formato_tamanho(doc.path), size=Tokens.FONT_XS, color=Tokens.TEXT_MUTED),
    ]
    if doc.tokens_estimados:
        detalhes.append(ft.Text("•", size=Tokens.FONT_XS, color=Tokens.TEXT_MUTED))
        detalhes.append(
            ft.Text(
                f"~{doc.tokens_estimados:,} tokens".replace(",", "."),
                size=Tokens.FONT_XS,
                color=Tokens.TEXT_MUTED,
            )
        )

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(_icone_por_tipo(doc.tipo), color=Tokens.ACCENT, size=Tokens.FONT_LG),
                ft.Column(
                    controls=[
                        ft.Text(
                            doc.nome,
                            size=Tokens.FONT_SM,
                            color=Tokens.TEXT_PRIMARY,
                            weight=Tokens.WEIGHT_MEDIUM,
                        ),
                        ft.Row(detalhes, spacing=Tokens.SPACE_1, tight=True),
                    ],
                    spacing=2,
                    tight=True,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=Tokens.ERROR,
                    icon_size=Tokens.FONT_BASE,
                    tooltip="Remover do projeto",
                    on_click=lambda _e, d=doc: on_remover(d),
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
    # Dropdown de projetos
    dropdown_projetos = ft.Dropdown(
        label="Projeto ativo",
        options=[ft.dropdown.Option(p) for p in state.listar_projetos()],
        value=state.projeto_ativo,
        bgcolor=Tokens.BG_SURFACE,
        color=Tokens.TEXT_PRIMARY,
        border_color=Tokens.BORDER,
        focused_border_color=Tokens.ACCENT,
        label_style=ft.TextStyle(color=Tokens.TEXT_MUTED, size=Tokens.FONT_SM),
        text_size=Tokens.FONT_SM,
        expand=True,
    )

    # Container que vai segurar a lista (atualiza dinamicamente)
    lista_docs_container = ft.Column(spacing=Tokens.SPACE_2, tight=True)

    # Banner de status
    status_container = ft.Container(visible=False)

    inicializado = [False]

    def _maybe_update() -> None:
        """Só faz page.update() depois que a view ja foi anexada ao page tree."""
        if inicializado[0]:
            try:
                page.update()
            except Exception:
                pass

    def mostrar_status(tipo: str, texto: str) -> None:
        status_container.content = status_banner(tipo, texto)
        status_container.visible = True
        _maybe_update()

    def esconder_status() -> None:
        status_container.visible = False
        _maybe_update()

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

    def atualizar_resumo() -> None:
        if not state.projeto_ativo:
            resumo_text.value = "Nenhum projeto carregado."
        else:
            n = len(state.documentacao)
            tokens = state.total_tokens_docs()
            resumo_text.value = (
                f"Projeto {state.projeto_ativo}: {n} documento{'s' if n != 1 else ''} "
                f"persistido{'s' if n != 1 else ''} (~{tokens:,} tokens).".replace(",", ".")
            )
        _maybe_update()

    # ---- Handlers ----

    def on_projeto_change(e: ft.ControlEvent) -> None:
        state.set_projeto_ativo(dropdown_projetos.value or None)
        esconder_status()
        atualizar_lista()
        atualizar_resumo()

    dropdown_projetos.on_select = on_projeto_change

    def on_novo_projeto(_: ft.ControlEvent) -> None:
        nome_field = campo_texto(hint="ex: modelos, certificados, aprender-mobile")

        def confirmar(_e):
            nome = (nome_field.value or "").strip()
            if not nome:
                return
            ok = state.criar_projeto(nome)
            if not ok:
                mostrar_status("error", f"Projeto '{nome}' já existe ou nome inválido.")
                return
            # Recarrega dropdown e seleciona
            dropdown_projetos.options = [
                ft.dropdown.Option(p) for p in state.listar_projetos()
            ]
            dropdown_projetos.value = nome
            state.set_projeto_ativo(nome)
            page.pop_dialog()
            atualizar_lista()
            atualizar_resumo()
            mostrar_status("ok", f"Projeto '{nome}' criado.")

        def cancelar(_e):
            page.pop_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=Tokens.BG_SURFACE,
            title=ft.Text("Novo projeto", color=Tokens.TEXT_PRIMARY),
            content=ft.Container(
                content=ft.Column(
                    controls=[rotulo_campo("Nome do projeto"), nome_field],
                    spacing=6,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                width=400,
                padding=Tokens.SPACE_2,
            ),
            actions=[
                ft.Row(
                    controls=[
                        ft.Container(expand=True),
                        botao_secundario("Cancelar", cancelar),
                        botao_primario("Criar", confirmar, icon=ft.Icons.ADD),
                    ],
                    spacing=Tokens.SPACE_2,
                )
            ],
        )
        page.show_dialog(dialog)

    def on_anexar(_: ft.ControlEvent) -> None:
        if not state.projeto_ativo:
            mostrar_status("warn", "Crie ou selecione um projeto antes de anexar.")
            return

        from app.services.file_dialog import escolher_arquivos

        paths = escolher_arquivos(
            titulo="Adicionar documento ao projeto",
            extensoes=[
                ("Documentos", "*.md *.markdown *.txt *.pdf *.png *.jpg *.jpeg"),
                ("Markdown / Texto", "*.md *.markdown *.txt"),
                ("PDF", "*.pdf"),
                ("Imagens", "*.png *.jpg *.jpeg"),
            ],
            multiplo=True,
        )
        if not paths:
            return

        adicionados = 0
        for path in paths:
            try:
                state.adicionar_doc(path)
                adicionados += 1
            except ValueError as err:
                mostrar_status("error", f"{path.name}: {err}")

        if adicionados:
            atualizar_lista()
            atualizar_resumo()
            mostrar_status(
                "ok",
                f"{adicionados} arquivo{'s' if adicionados != 1 else ''} "
                f"adicionado{'s' if adicionados != 1 else ''}.",
            )

    def on_colar_imagem(_: ft.ControlEvent) -> None:
        if not state.projeto_ativo:
            mostrar_status("warn", "Crie ou selecione um projeto antes de colar.")
            return
        destino = state.pasta_do_projeto(state.projeto_ativo)
        path = pegar_imagem_da_clipboard(destino, prefixo="imagem")
        if path is None:
            mostrar_status("warn", "Nenhuma imagem na área de transferência.")
            return
        try:
            state.adicionar_doc(path)
        except ValueError as e:
            mostrar_status("error", str(e))
            return
        atualizar_lista()
        atualizar_resumo()
        mostrar_status("ok", f"Imagem colada como {path.name}.")

    def on_colar_texto(_: ft.ControlEvent) -> None:
        if not state.projeto_ativo:
            mostrar_status("warn", "Crie ou selecione um projeto antes de colar.")
            return

        texto_field = ft.TextField(
            multiline=True,
            min_lines=10,
            max_lines=20,
            hint_text="Cole aqui a regra de negócio, discovery, especificação...",
            bgcolor=Tokens.BG_PRIMARY,
            color=Tokens.TEXT_PRIMARY,
            border_color=Tokens.BORDER,
            focused_border_color=Tokens.ACCENT,
            text_size=Tokens.FONT_SM,
        )

        def confirmar(_e):
            texto = (texto_field.value or "").strip()
            if not texto:
                return
            import time
            destino = state.pasta_do_projeto(state.projeto_ativo)
            destino.mkdir(parents=True, exist_ok=True)
            nome = f"colado_{int(time.time())}.md"
            arquivo = destino / nome
            arquivo.write_text(texto, encoding="utf-8")
            state.adicionar_doc(arquivo)
            page.pop_dialog()
            atualizar_lista()
            atualizar_resumo()
            mostrar_status("ok", f"Texto salvo como {nome}.")

        def cancelar(_e):
            page.pop_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=Tokens.BG_SURFACE,
            title=ft.Text("Colar texto como documento", color=Tokens.TEXT_PRIMARY),
            content=ft.Container(
                content=ft.Column(
                    controls=[texto_field],
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                width=600,
                padding=Tokens.SPACE_2,
            ),
            actions=[
                ft.Row(
                    controls=[
                        ft.Container(expand=True),
                        botao_secundario("Cancelar", cancelar),
                        botao_primario("Salvar", confirmar, icon=ft.Icons.SAVE_OUTLINED),
                    ],
                    spacing=Tokens.SPACE_2,
                )
            ],
        )
        page.show_dialog(dialog)

    def on_remover_doc(doc: Documento) -> None:
        state.remover_doc(doc)
        atualizar_lista()
        atualizar_resumo()
        mostrar_status("warn", f"'{doc.nome}' removido.")

    # ---- Estado inicial ----

    resumo_text = ft.Text(
        "",
        color=Tokens.TEXT_MUTED,
        size=Tokens.FONT_SM,
        selectable=True,
    )
    atualizar_resumo()
    atualizar_lista()

    # Reage a mudanças externas no state
    state.on("documentacao_changed", lambda _docs: (atualizar_lista(), atualizar_resumo()))
    state.on(
        "projetos_lista_changed",
        lambda _lst: setattr(
            dropdown_projetos,
            "options",
            [ft.dropdown.Option(p) for p in state.listar_projetos()],
        ),
    )

    # ---- Layout ----

    topo = ft.Row(
        controls=[
            dropdown_projetos,
            botao_secundario("+ Novo projeto", on_novo_projeto),
        ],
        spacing=Tokens.SPACE_3,
    )

    botoes_adicionar = ft.Row(
        controls=[
            botao_primario(
                "Anexar arquivo",
                on_anexar,
                icon=Icones.ANEXAR,
            ),
            botao_secundario("Colar imagem", on_colar_imagem),
            botao_secundario("Colar texto", on_colar_texto),
        ],
        spacing=Tokens.SPACE_2,
    )

    # Marca como inicializado para que próximas chamadas possam fazer page.update().
    # (As chamadas durante construir() acima foram silenciosas via _maybe_update.)
    inicializado[0] = True

    return ft.Container(
        content=ft.Column(
            controls=[
                titulo_pagina("Documentação do projeto", icone=Icones.DOC),
                ft.Text(
                    "Regras de negócio, discovery, usabilidade. Persistido em "
                    "docs/projetos/<projeto>/ — anexe uma vez e nunca mais reanexe.",
                    color=Tokens.TEXT_MUTED,
                    size=Tokens.FONT_SM,
                ),
                ft.Container(height=Tokens.SPACE_2),
                topo,
                ft.Container(height=Tokens.SPACE_2),
                resumo_text,
                ft.Container(height=Tokens.SPACE_3),
                botoes_adicionar,
                ft.Container(height=Tokens.SPACE_3),
                status_container,
                lista_docs_container,
            ],
            spacing=Tokens.SPACE_2,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        padding=Tokens.SPACE_5,
        expand=True,
    )
