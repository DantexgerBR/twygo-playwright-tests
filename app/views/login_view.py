"""Tela de login e configuração de credenciais.

Renderizada como TELA (não dialog) — evita bugs de hit-testing do Flet 0.85
com botões dentro de AlertDialog. Persiste em .env após validar o .gitignore.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import flet as ft

from app.services.credentials import (
    Credenciais,
    GitignoreNaoProteje,
    apagar_salvas,
    carregar,
    salvar,
)
from app.theme import Tokens
from app.ui_kit import (
    botao_primario,
    botao_secundario,
    botao_texto,
    campo_texto,
    rotulo_campo,
    secao_titulo,
    status_banner,
    _borda,
)


def _campo_com_label(
    label: str,
    tf: ft.TextField,
    *,
    expand: int | None = None,
) -> ft.Column:
    return ft.Column(
        controls=[rotulo_campo(label), tf],
        spacing=6,
        tight=True,
        expand=expand,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def _par_email_senha(
    label_email: str,
    email_tf: ft.TextField,
    label_senha: str,
    senha_tf: ft.TextField,
) -> ft.Row:
    return ft.Row(
        controls=[
            _campo_com_label(label_email, email_tf, expand=1),
            _campo_com_label(label_senha, senha_tf, expand=1),
        ],
        spacing=Tokens.SPACE_3,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )


def construir_tela_login(
    page: ft.Page,
    project_root: Path,
    on_success: Callable[[Credenciais], None],
    on_cancelar: Callable[[], None] | None = None,
) -> ft.Control:
    """Constrói a tela inteira de login. Não é dialog — é uma view normal."""
    cred = carregar(project_root)

    base_url_tf = campo_texto(
        valor=cred.base_url,
        hint="https://twygo<sua-org>.stage.twygoead.com/",
    )
    admin_email_tf = campo_texto(valor=cred.admin_email, hint="admin@empresa.com")
    admin_password_tf = campo_texto(valor=cred.admin_password, senha=True)
    aluno_email_tf = campo_texto(valor=cred.aluno_email, hint="aluno@empresa.com")
    aluno_password_tf = campo_texto(valor=cred.aluno_password, senha=True)
    gemini_key_tf = campo_texto(
        valor=cred.gemini_api_key,
        hint="AIza... (grátis em aistudio.google.com — recomendado)",
        senha=True,
    )
    anthropic_key_tf = campo_texto(
        valor=cred.anthropic_api_key,
        hint="sk-ant-... (opcional, pago — só se quiser usar Claude)",
        senha=True,
    )
    org_id_tf = campo_texto(
        valor=cred.org_id,
        hint="opcional, em branco se a URL já tem",
    )

    feedback = ft.Container(visible=False)

    def mostrar(tipo: str, texto: str) -> None:
        feedback.content = status_banner(tipo, texto)
        feedback.visible = True
        page.update()

    def on_click_salvar(_: ft.ControlEvent) -> None:
        print("[login] on_click_salvar disparado", flush=True)
        try:
            nova = Credenciais(
                base_url=(base_url_tf.value or "").strip(),
                admin_email=(admin_email_tf.value or "").strip(),
                admin_password=admin_password_tf.value or "",
                aluno_email=(aluno_email_tf.value or "").strip(),
                aluno_password=aluno_password_tf.value or "",
                anthropic_api_key=(anthropic_key_tf.value or "").strip(),
                gemini_api_key=(gemini_key_tf.value or "").strip(),
                org_id=(org_id_tf.value or "").strip(),
            )
            if not nova.completo_para_admin():
                mostrar(
                    "error",
                    "Preencha URL, e-mail/senha do admin e pelo menos uma chave (GEMINI ou ANTHROPIC).",
                )
                return
            try:
                salvar(project_root, nova)
            except GitignoreNaoProteje as e:
                mostrar(
                    "error",
                    f"Salvamento bloqueado: .gitignore não cobre {', '.join(e.faltando)}.",
                )
                return
            print("[login] credenciais salvas, chamando on_success", flush=True)
            on_success(nova)
        except Exception as exc:
            import traceback
            print(f"[login] EXCEÇÃO: {exc}", flush=True)
            traceback.print_exc()
            mostrar("error", f"Erro inesperado: {exc}")

    def on_click_apagar(_: ft.ControlEvent) -> None:
        print("[login] on_click_apagar disparado", flush=True)
        apagar_salvas(project_root)
        base_url_tf.value = ""
        admin_email_tf.value = ""
        admin_password_tf.value = ""
        aluno_email_tf.value = ""
        aluno_password_tf.value = ""
        anthropic_key_tf.value = ""
        gemini_key_tf.value = ""
        org_id_tf.value = ""
        mostrar("warn", "Credenciais apagadas. Preencha de novo para usar o app.")

    def on_click_cancelar(_: ft.ControlEvent) -> None:
        print("[login] on_click_cancelar disparado", flush=True)
        if on_cancelar:
            on_cancelar()

    botoes_acao: list[ft.Control] = [
        botao_texto(
            "Esquecer credenciais",
            on_click_apagar,
            icon=ft.Icons.DELETE_OUTLINE,
            cor=Tokens.ERROR,
        ),
        ft.Container(expand=True),
    ]
    if on_cancelar is not None:
        botoes_acao.append(botao_secundario("Cancelar", on_click_cancelar))
    botoes_acao.append(
        botao_primario("Salvar", on_click_salvar, icon=ft.Icons.SAVE_OUTLINED)
    )

    rodape = ft.Row(
        controls=botoes_acao,
        spacing=Tokens.SPACE_2,
        alignment=ft.MainAxisAlignment.START,
    )

    corpo = ft.Column(
        controls=[
            ft.Text(
                "Configurar acesso ao Twygo",
                size=Tokens.FONT_XL,
                weight=Tokens.WEIGHT_BOLD,
                color=Tokens.TEXT_PRIMARY,
            ),
            ft.Text(
                "Credenciais ficam em .env (já no .gitignore). Nunca serão commitadas.",
                color=Tokens.TEXT_MUTED,
                size=Tokens.FONT_SM,
            ),
            ft.Container(height=Tokens.SPACE_3),
            _campo_com_label("URL da org", base_url_tf),
            ft.Container(height=Tokens.SPACE_3),
            secao_titulo("Admin"),
            _par_email_senha("E-mail", admin_email_tf, "Senha", admin_password_tf),
            ft.Container(height=Tokens.SPACE_3),
            secao_titulo("Aluno (opcional — usa admin se vazio)", sutil=True),
            _par_email_senha("E-mail", aluno_email_tf, "Senha", aluno_password_tf),
            ft.Container(height=Tokens.SPACE_3),
            secao_titulo("API do agente QA"),
            _campo_com_label("GEMINI_API_KEY (recomendado — grátis)", gemini_key_tf),
            _campo_com_label("ANTHROPIC_API_KEY (opcional — pago)", anthropic_key_tf),
            ft.Container(height=Tokens.SPACE_3),
            secao_titulo("Outros"),
            _campo_com_label("ORG_ID (opcional)", org_id_tf),
            ft.Container(height=Tokens.SPACE_3),
            feedback,
            rodape,
        ],
        spacing=Tokens.SPACE_2,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        tight=True,
    )

    # Layout simples: padding + Column com tudo dentro. Sem nesting de Row/expand
    # que confundia o Flet desktop e travava em "Working...".
    return ft.Container(
        content=corpo,
        bgcolor=Tokens.BG_PRIMARY,
        padding=Tokens.SPACE_6,
    )
