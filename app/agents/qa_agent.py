"""Agente QA — orquestra LLM + Playwright em loop ReAct.

Recebe caso, evidências e documentação do projeto. Faz login no stage,
e em loop pergunta ao LLM "qual o próximo passo?" passando o estado atual
(screenshot + DOM simplificado). Executa as ações que o LLM retornar via
tool calls. Termina quando o LLM chama `finalizar` com laudo, ou quando
atinge o limite de iterações (inconclusivo).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, Optional

from app.agents.llm_client import LLMClient, Mensagem, RespostaLLM, Tool, ToolCall
from app.services.browser import Browser
from app.services.stage_health import verificar_stage
from app.state import (
    CasoParseado,
    Documento,
    Evidencia,
    Laudo,
    ResultadoExecucao,
)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------


SYSTEM_PROMPT_RETRABALHO = """Você é um QA Engineer da Twygo. Sua tarefa: validar se um bug reportado num retrabalho foi corrigido no ambiente de stage.

Você recebe:
- Descrição do retrabalho (passos pra reproduzir + comportamento esperado)
- Evidência visual do bug original (print de como o bug aparece)
- Documentação do projeto (regras de negócio relevantes)
- Screenshot atual da página + DOM simplificado (elementos clicáveis)

Você usa as ferramentas (tool calls) para interagir com a página:
- clicar(seletor) — clica num elemento (use seletor CSS, id #foo, ou texto via :has-text("..."))
- preencher(seletor, valor) — preenche um input
- navegar(url) — vai pra uma URL
- aguardar(segundos) — espera animação/carga
- tirar_screenshot() — atualiza sua visão da tela
- finalizar(laudo, justificativa) — emite laudo final

REGRAS:
1. Execute UM passo de cada vez. Após cada ação, espere ~500ms.
2. Compare visualmente com a evidência do bug original ao chegar no estado final.
3. Use a documentação do projeto pra entender o comportamento esperado correto.
4. Laudo possíveis: "corrigido", "ainda_quebrado", "inconclusivo".
5. Em dúvida ou se não conseguir reproduzir → "inconclusivo" com explicação.
6. NUNCA invente resultado positivo. Bug em QA é coisa séria.
7. Quando chegar no comportamento final esperado, chame `finalizar` com o laudo.
"""


# ---------------------------------------------------------------------------
# Tools que o agente pode chamar
# ---------------------------------------------------------------------------


def _construir_tools() -> list[Tool]:
    return [
        Tool(
            name="clicar",
            description="Clica em um elemento. Use seletor CSS ou ID (ex: '#salvar', 'button:has-text(\"Aplicar\")').",
            parameters={
                "type": "object",
                "properties": {
                    "seletor": {"type": "string", "description": "Seletor CSS do elemento."},
                },
                "required": ["seletor"],
            },
        ),
        Tool(
            name="preencher",
            description="Preenche um input com um valor.",
            parameters={
                "type": "object",
                "properties": {
                    "seletor": {"type": "string"},
                    "valor": {"type": "string"},
                },
                "required": ["seletor", "valor"],
            },
        ),
        Tool(
            name="navegar",
            description="Navega para uma URL específica.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="aguardar",
            description="Espera N segundos (para animações ou carga).",
            parameters={
                "type": "object",
                "properties": {
                    "segundos": {"type": "number"},
                },
                "required": ["segundos"],
            },
        ),
        Tool(
            name="tirar_screenshot",
            description="Tira novo screenshot pra atualizar sua visão da tela.",
            parameters={"type": "object", "properties": {}},
        ),
        Tool(
            name="finalizar",
            description="Encerra a execução emitindo o laudo final.",
            parameters={
                "type": "object",
                "properties": {
                    "laudo": {
                        "type": "string",
                        "enum": ["corrigido", "ainda_quebrado", "inconclusivo"],
                    },
                    "justificativa": {"type": "string"},
                },
                "required": ["laudo", "justificativa"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Agente
# ---------------------------------------------------------------------------


class QAAgent:
    MAX_ITERACOES = 25
    PAUSA_APOS_ACAO_SEG = 0.5

    def __init__(
        self,
        llm: LLMClient,
        browser: Browser,
        *,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.llm = llm
        self.browser = browser
        self.on_log = on_log or (lambda _msg: None)
        self.screenshots: list[Path] = []
        self.log: list[str] = []
        self._stop_requested = False
        self._resultado_final: Optional[ResultadoExecucao] = None

    def _logar(self, msg: str) -> None:
        self.log.append(msg)
        try:
            self.on_log(msg)
        except Exception:
            pass

    def request_stop(self) -> None:
        """Sinaliza para parar no próximo turno (chamado de outra thread)."""
        self._stop_requested = True

    def executar(
        self,
        *,
        caso: CasoParseado,
        evidencias: list[Evidencia],
        documentacao: list[Documento],
        base_url: str,
        admin_email: str,
        admin_password: str,
        pasta_screenshots: Path,
    ) -> ResultadoExecucao:
        try:
            return self._executar_inner(
                caso=caso,
                evidencias=evidencias,
                documentacao=documentacao,
                base_url=base_url,
                admin_email=admin_email,
                admin_password=admin_password,
                pasta_screenshots=pasta_screenshots,
            )
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self._logar(f"EXCEÇÃO no agente: {e}")
            self._logar(tb)
            try:
                self.browser.close()
            except Exception:
                pass
            return ResultadoExecucao(
                laudo="inconclusivo",
                justificativa=f"Exceção não tratada no agente: {e}",
                screenshots=self.screenshots,
                log=self.log,
            )

    def _executar_inner(
        self,
        *,
        caso: CasoParseado,
        evidencias: list[Evidencia],
        documentacao: list[Documento],
        base_url: str,
        admin_email: str,
        admin_password: str,
        pasta_screenshots: Path,
    ) -> ResultadoExecucao:
        # 1. Verifica stage
        self._logar("Verificando se stage está no ar…")
        status = verificar_stage(base_url)
        if status == "down":
            return ResultadoExecucao(
                laudo="inconclusivo",
                justificativa="Stage da Twygo está fora do ar (devs costumam reiniciar). Tente em 2-5 minutos.",
            )
        if status == "erro":
            return ResultadoExecucao(
                laudo="inconclusivo",
                justificativa="Erro de rede ao tentar acessar o stage. Verifique sua conexão.",
            )
        self._logar("Stage OK.")

        # 2. Login
        self._logar("Iniciando browser e fazendo login…")
        try:
            self.browser.start()
            self.browser.login_twygo(base_url, admin_email, admin_password)
            self._logar(f"Logado. URL atual: {self.browser.current_url()}")
        except Exception as e:
            self._logar(f"Falha no login: {e}")
            self.browser.close()
            return ResultadoExecucao(
                laudo="inconclusivo",
                justificativa=f"Não consegui logar no stage: {e}",
            )

        # 3. Screenshot inicial
        primeiro = self._capturar(pasta_screenshots, "inicial")

        # 4. Monta histórico de conversa
        contexto_inicial = self._formatar_contexto_inicial(caso, evidencias, documentacao)

        mensagens: list[Mensagem] = [
            Mensagem(role="user", text=contexto_inicial),
        ]
        # Adiciona evidências como imagens
        for ev in evidencias:
            if ev.tipo == "print" and ev.path.exists():
                mensagens.append(
                    Mensagem(
                        role="user",
                        text=f"Evidência do bug original ({ev.origem}): {ev.nome}",
                        image_path=ev.path,
                    )
                )
        # Adiciona screenshot inicial
        mensagens.append(
            Mensagem(
                role="user",
                text="Screenshot atual da página (após login):",
                image_path=primeiro,
            )
        )
        # Adiciona DOM simplificado
        dom = self.browser.get_dom_simplificado()
        mensagens.append(Mensagem(role="user", text=f"Elementos interativos visíveis:\n{dom}"))

        tools = _construir_tools()

        # 5. Loop ReAct
        for iteracao in range(1, self.MAX_ITERACOES + 1):
            if self._stop_requested:
                self._logar("Parada solicitada pelo usuário.")
                self.browser.close()
                return ResultadoExecucao(
                    laudo="inconclusivo",
                    justificativa="Execução interrompida pelo usuário.",
                    screenshots=self.screenshots,
                    log=self.log,
                    iteracoes=iteracao - 1,
                )

            self._logar(f"--- Iteração {iteracao} ---")
            self._logar(f"  Chamando LLM ({len(mensagens)} mensagens, {len(tools)} tools)…")
            try:
                resp = self.llm.gerar(SYSTEM_PROMPT_RETRABALHO, mensagens, tools)
            except Exception as e:
                import traceback
                self._logar(f"Erro chamando LLM: {type(e).__name__}: {e}")
                self._logar(traceback.format_exc())
                self.browser.close()
                return ResultadoExecucao(
                    laudo="inconclusivo",
                    justificativa=f"Erro chamando LLM: {e}",
                    screenshots=self.screenshots,
                    log=self.log,
                    iteracoes=iteracao,
                )

            self._logar(
                f"  LLM respondeu: text={len(resp.text)} chars, "
                f"tool_calls={len(resp.tool_calls)}"
            )
            if resp.text:
                self._logar(f"Agente: {resp.text[:300]}")
            if resp.tool_calls:
                # Acrescenta o turn do model ao histórico
                mensagens.append(Mensagem(role="model", text=resp.text or "(tool calls)"))
                novas_mensagens = self._executar_tool_calls(resp.tool_calls, pasta_screenshots)
                mensagens.extend(novas_mensagens)
                if self._resultado_final is not None:
                    # finalizar foi chamado
                    self.browser.close()
                    self._resultado_final.screenshots = self.screenshots
                    self._resultado_final.log = self.log
                    self._resultado_final.iteracoes = iteracao
                    return self._resultado_final
            else:
                # LLM não emitiu tool calls — provavelmente texto livre
                # Adiciona um nudge pra ele continuar
                self._logar("LLM não retornou tool calls. Pedindo pra continuar…")
                mensagens.append(Mensagem(role="model", text=resp.text or ""))
                mensagens.append(
                    Mensagem(
                        role="user",
                        text="Continue: chame uma tool (clicar/preencher/navegar/finalizar). Sem prosa.",
                    )
                )

        # Timeout
        self.browser.close()
        return ResultadoExecucao(
            laudo="inconclusivo",
            justificativa=f"Excedeu {self.MAX_ITERACOES} iterações sem chegar ao final.",
            screenshots=self.screenshots,
            log=self.log,
            iteracoes=self.MAX_ITERACOES,
        )

    # ---- Helpers internos ----

    def _formatar_contexto_inicial(
        self,
        caso: CasoParseado,
        evidencias: list[Evidencia],
        documentacao: list[Documento],
    ) -> str:
        partes = []
        if documentacao:
            partes.append("## Documentação do projeto")
            for doc in documentacao:
                if doc.conteudo:
                    partes.append(f"### {doc.nome}\n{doc.conteudo[:3000]}")
        partes.append("## Retrabalho / Caso")
        if caso.objetivo:
            partes.append(f"**Objetivo:** {caso.objetivo}")
        if caso.pre_condicoes:
            partes.append("**Pré-condições:**")
            for pc in caso.pre_condicoes:
                partes.append(f"- {pc}")
        if caso.passos:
            partes.append("**Passos esperados:**")
            for p in caso.passos:
                partes.append(f"{p['n']}. {p['acao']} → esperado: {p['esperado']}")
        elif caso.texto_bruto:
            partes.append(f"**Texto bruto do retrabalho:**\n{caso.texto_bruto}")
        partes.append(
            f"\n## Evidências anexadas\n"
            f"{len(evidencias)} evidência(s) — vou enviar imagens na sequência."
        )
        partes.append(
            "\nAgora analise a tela inicial (próximo screenshot) e chame a primeira tool."
        )
        return "\n\n".join(partes)

    def _capturar(self, pasta: Path, prefixo: str) -> Path:
        nome = f"{prefixo}_{int(time.time())}_{len(self.screenshots)+1}.png"
        path = self.browser.screenshot(pasta / nome)
        self.screenshots.append(path)
        return path

    def _executar_tool_calls(
        self,
        chamadas: list[ToolCall],
        pasta_screenshots: Path,
    ) -> list[Mensagem]:
        """Executa uma lista de tool calls, devolvendo mensagens de feedback pro LLM."""
        novas: list[Mensagem] = []
        for tc in chamadas:
            try:
                args_repr = json.dumps(tc.args, ensure_ascii=False, default=str)
            except Exception:
                args_repr = repr(tc.args)
            self._logar(f"Tool call: {tc.name}({args_repr})")
            try:
                if tc.name == "clicar":
                    self.browser.click(tc.args["seletor"])
                    time.sleep(self.PAUSA_APOS_ACAO_SEG)
                    novas.append(Mensagem(role="user", text=f"clicar OK em {tc.args['seletor']}"))
                elif tc.name == "preencher":
                    self.browser.fill(tc.args["seletor"], tc.args["valor"])
                    time.sleep(self.PAUSA_APOS_ACAO_SEG)
                    novas.append(Mensagem(role="user", text=f"preencher OK em {tc.args['seletor']}"))
                elif tc.name == "navegar":
                    self.browser.goto(tc.args["url"])
                    time.sleep(self.PAUSA_APOS_ACAO_SEG)
                    novas.append(Mensagem(role="user", text=f"navegar OK para {tc.args['url']}"))
                elif tc.name == "aguardar":
                    segundos = float(tc.args.get("segundos", 1))
                    time.sleep(min(segundos, 5.0))
                    novas.append(Mensagem(role="user", text=f"aguardei {segundos}s"))
                elif tc.name == "tirar_screenshot":
                    path = self._capturar(pasta_screenshots, "iter")
                    dom = self.browser.get_dom_simplificado()
                    novas.append(
                        Mensagem(
                            role="user",
                            text=f"Screenshot atual ({path.name}) e DOM:\n{dom}",
                            image_path=path,
                        )
                    )
                elif tc.name == "finalizar":
                    laudo = str(tc.args.get("laudo", "inconclusivo")).lower()
                    if laudo not in ("corrigido", "ainda_quebrado", "inconclusivo"):
                        laudo = "inconclusivo"
                    self._resultado_final = ResultadoExecucao(
                        laudo=laudo,  # type: ignore[arg-type]
                        justificativa=str(tc.args.get("justificativa", "")),
                    )
                    self._logar(f"Laudo: {laudo} — {tc.args.get('justificativa', '')}")
                    break
                else:
                    novas.append(
                        Mensagem(role="user", text=f"tool desconhecida: {tc.name}")
                    )
            except Exception as e:
                self._logar(f"Erro executando {tc.name}: {e}")
                novas.append(
                    Mensagem(role="user", text=f"erro em {tc.name}: {e}. Tente outro caminho.")
                )

            # Após cada ação, anexa um novo screenshot pra próxima iteração ter visão atualizada
            if tc.name in ("clicar", "preencher", "navegar"):
                try:
                    path = self._capturar(pasta_screenshots, "iter")
                    dom = self.browser.get_dom_simplificado()
                    novas.append(
                        Mensagem(
                            role="user",
                            text=f"Estado atual após {tc.name}:\n{dom}",
                            image_path=path,
                        )
                    )
                except Exception:
                    pass

        return novas
