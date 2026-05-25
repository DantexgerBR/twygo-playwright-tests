"""Aba Execução — dispara o QAAgent e mostra log em tempo real."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

import flet as ft

from app.agents.llm_client import criar_cliente
from app.agents.qa_agent import QAAgent
from app.icons import Icones
from app.services.browser import Browser
from app.services.stage_health import verificar_stage
from app.state import AppState, ResultadoExecucao
from app.theme import Tokens
from app.ui_kit import (
    botao_primario,
    botao_secundario,
    secao_titulo,
    status_banner,
    titulo_pagina,
    _borda,
)


def construir(page: ft.Page, state: AppState) -> ft.Control:
    # ---- Estado da view ----
    agente_em_execucao: list[Optional[QAAgent]] = [None]
    thread_atual: list[Optional[threading.Thread]] = [None]
    inicializado = [False]

    def _maybe_update():
        if inicializado[0]:
            try:
                page.update()
            except Exception:
                pass

    # ---- Componentes ----
    badge_stage = ft.Container(visible=False)
    resumo_contexto = ft.Text("", color=Tokens.TEXT_MUTED, size=Tokens.FONT_SM)

    headless_cb = ft.Checkbox(
        label="Headless (sem janela do browser)",
        value=False,
        label_style=ft.TextStyle(color=Tokens.TEXT_PRIMARY, size=Tokens.FONT_SM),
        active_color=Tokens.ACCENT,
    )
    slowmo_cb = ft.Checkbox(
        label="Slow motion (500ms entre ações)",
        value=False,
        label_style=ft.TextStyle(color=Tokens.TEXT_PRIMARY, size=Tokens.FONT_SM),
        active_color=Tokens.ACCENT,
    )

    log_text = ft.Text(
        "",
        color=Tokens.TEXT_PRIMARY,
        size=Tokens.FONT_XS,
        selectable=True,
        font_family="Consolas",
    )
    log_container = ft.Container(
        content=ft.Column(
            controls=[log_text],
            scroll=ft.ScrollMode.AUTO,
            tight=True,
        ),
        bgcolor=Tokens.BG_PRIMARY,
        border=_borda(),
        border_radius=Tokens.RADIUS_MD,
        padding=Tokens.SPACE_3,
        height=300,
    )

    status_container = ft.Container(visible=False)

    laudo_container = ft.Container(visible=False)

    # ---- Helpers ----

    def _atualizar_resumo():
        n_docs = len(state.documentacao)
        n_ev = len(state.evidencias)
        tem_caso = state.caso is not None and bool(state.caso.texto_bruto)
        partes = []
        if n_docs:
            partes.append(f"📚 {n_docs} doc{'s' if n_docs != 1 else ''}")
        partes.append("✓ Caso pronto" if tem_caso else "⚠ Sem caso")
        partes.append(f"{n_ev} evidência{'s' if n_ev != 1 else ''}")
        resumo_contexto.value = " · ".join(partes)
        _maybe_update()

    def _verificar_stage_e_atualizar():
        base_url = state.credenciais.base_url
        if not base_url:
            badge_stage.content = status_banner("warn", "BASE_URL não configurada (clique ⚙ no header).")
            badge_stage.visible = True
            _maybe_update()
            return
        status = verificar_stage(base_url)
        if status == "ok":
            badge_stage.content = status_banner("ok", f"Stage OK: {base_url}")
        elif status == "down":
            badge_stage.content = status_banner(
                "warn",
                "Stage parece fora do ar (devs costumam reiniciar). Aguarde 2-5 minutos e tente de novo.",
            )
        else:
            badge_stage.content = status_banner("error", f"Erro de rede ao acessar {base_url}.")
        badge_stage.visible = True
        _maybe_update()

    def _adicionar_log(linha: str):
        log_text.value = (log_text.value or "") + linha + "\n"
        _maybe_update()

    def _mostrar_laudo(resultado: ResultadoExecucao):
        cores = {
            "corrigido": ("ok", "Corrigido", Icones.OK),
            "ainda_quebrado": ("error", "Ainda quebrado", Icones.ERRO),
            "inconclusivo": ("warn", "Inconclusivo", Icones.AVISO),
        }
        tipo, label, _icone = cores.get(resultado.laudo, ("warn", resultado.laudo, Icones.AVISO))
        laudo_container.content = ft.Column(
            controls=[
                status_banner(tipo, f"Laudo: {label}"),
                ft.Container(height=Tokens.SPACE_2),
                ft.Text(
                    resultado.justificativa or "(sem justificativa)",
                    color=Tokens.TEXT_PRIMARY,
                    size=Tokens.FONT_SM,
                ),
                ft.Text(
                    f"Iterações: {resultado.iteracoes} · {len(resultado.screenshots)} screenshot(s)",
                    color=Tokens.TEXT_MUTED,
                    size=Tokens.FONT_XS,
                ),
            ],
            spacing=Tokens.SPACE_2,
        )
        laudo_container.visible = True
        _maybe_update()

    # ---- Handlers ----

    def on_verificar_stage(_):
        _verificar_stage_e_atualizar()

    def on_executar(_):
        # Validação básica
        cred = state.credenciais
        if not cred.completo_para_admin():
            status_container.content = status_banner(
                "error",
                "Credenciais incompletas. Clique no ⚙ no header e preencha.",
            )
            status_container.visible = True
            _maybe_update()
            return
        if not state.caso or not state.caso.texto_bruto:
            status_container.content = status_banner(
                "warn",
                "Cole um caso na aba 'Caso' e clique Analisar antes de executar.",
            )
            status_container.visible = True
            _maybe_update()
            return
        if not state.evidencias:
            status_container.content = status_banner(
                "warn",
                "Anexe ao menos uma evidência na aba 'Evidências' (o agente compara com ela).",
            )
            status_container.visible = True
            _maybe_update()
            return
        if not (cred.groq_api_key or cred.gemini_api_key or cred.anthropic_api_key):
            status_container.content = status_banner(
                "error",
                "Nenhuma chave de LLM configurada. Preencha GROQ ou GEMINI no ⚙.",
            )
            status_container.visible = True
            _maybe_update()
            return

        status_container.visible = False
        laudo_container.visible = False
        log_text.value = ""
        botao_executar.disabled = True
        botao_parar.visible = True
        _maybe_update()

        # Cria cliente LLM — prioridade: Groq > Gemini > Claude
        try:
            if cred.groq_api_key:
                _adicionar_log("Usando provedor: Groq (Llama 4)")
                llm = criar_cliente(provedor="groq", api_key=cred.groq_api_key)
            elif cred.gemini_api_key:
                _adicionar_log("Usando provedor: Gemini 2.5 Flash")
                llm = criar_cliente(provedor="gemini", api_key=cred.gemini_api_key)
            else:
                _adicionar_log("Claude API ainda não está suportado no MVP.")
                botao_executar.disabled = False
                botao_parar.visible = False
                _maybe_update()
                return
        except Exception as e:
            _adicionar_log(f"Erro criando cliente LLM: {e}")
            botao_executar.disabled = False
            botao_parar.visible = False
            _maybe_update()
            return

        browser = Browser(
            headless=headless_cb.value or False,
            slow_mo_ms=500 if (slowmo_cb.value or False) else 0,
        )
        agente = QAAgent(llm, browser, on_log=_adicionar_log)
        agente_em_execucao[0] = agente

        pasta_screenshots = state.project_root / "evidencias" / "_sessao_atual" / "agente"
        pasta_screenshots.mkdir(parents=True, exist_ok=True)

        def rodar():
            try:
                resultado = agente.executar(
                    caso=state.caso,  # type: ignore[arg-type]
                    evidencias=state.evidencias,
                    documentacao=state.documentacao,
                    base_url=cred.base_url,
                    admin_email=cred.admin_email,
                    admin_password=cred.admin_password,
                    pasta_screenshots=pasta_screenshots,
                    org_id=cred.org_id,
                )
                # Define evidência de referência (primeira print do bug original)
                for ev in state.evidencias:
                    if ev.tipo == "print" and ev.path.exists():
                        resultado.evidencia_referencia = ev.path
                        break
                _mostrar_laudo(resultado)
                # Publica no state pra aba Resultado se atualizar
                state.set_resultado(resultado)
                _adicionar_log("→ Veja detalhes completos na aba 'Resultado'.")
            except Exception as e:
                _adicionar_log(f"ERRO INESPERADO: {e}")
            finally:
                agente_em_execucao[0] = None
                botao_executar.disabled = False
                botao_parar.visible = False
                _maybe_update()

        t = threading.Thread(target=rodar, daemon=True)
        thread_atual[0] = t
        t.start()

    def on_parar(_):
        if agente_em_execucao[0] is not None:
            agente_em_execucao[0].request_stop()
            _adicionar_log("Parada solicitada — aguardando agente terminar o passo atual…")

    # ---- Componentes interativos ----

    botao_verificar_stage = botao_secundario("Verificar stage", on_verificar_stage)
    botao_executar = botao_primario("Executar reprodução", on_executar, icon=Icones.EXECUTAR)
    botao_parar_inner = botao_secundario("Parar", on_parar)
    botao_parar = ft.Container(content=botao_parar_inner, visible=False)

    # Inscreve em mudanças de estado pra atualizar resumo
    state.on("caso_changed", lambda _: _atualizar_resumo())
    state.on("evidencias_changed", lambda _: _atualizar_resumo())
    state.on("documentacao_changed", lambda _: _atualizar_resumo())
    state.on("credenciais_changed", lambda _: _verificar_stage_e_atualizar())

    # Estado inicial
    _atualizar_resumo()
    if state.credenciais.base_url:
        _verificar_stage_e_atualizar()
    inicializado[0] = True

    # ---- Layout ----
    return ft.Container(
        content=ft.Column(
            controls=[
                titulo_pagina("Execução do agente QA", icone=Icones.EXECUCAO),
                ft.Text(
                    "Dispara o agente Gemini guiando Playwright no stage. "
                    "Vê o caso, evidências e documentação carregados nas outras abas.",
                    color=Tokens.TEXT_MUTED,
                    size=Tokens.FONT_SM,
                ),
                ft.Container(height=Tokens.SPACE_3),

                secao_titulo("Stage"),
                ft.Row(
                    controls=[botao_verificar_stage],
                    spacing=Tokens.SPACE_2,
                ),
                badge_stage,

                ft.Container(height=Tokens.SPACE_3),
                secao_titulo("Contexto carregado"),
                resumo_contexto,

                ft.Container(height=Tokens.SPACE_3),
                secao_titulo("Opções"),
                ft.Row(controls=[headless_cb, slowmo_cb], spacing=Tokens.SPACE_5, wrap=True),

                ft.Container(height=Tokens.SPACE_3),
                ft.Row(
                    controls=[botao_executar, botao_parar],
                    spacing=Tokens.SPACE_2,
                ),

                status_container,

                ft.Container(height=Tokens.SPACE_3),
                secao_titulo("Log em tempo real"),
                log_container,

                ft.Container(height=Tokens.SPACE_3),
                laudo_container,
            ],
            spacing=Tokens.SPACE_2,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=Tokens.SPACE_5,
        expand=True,
    )
