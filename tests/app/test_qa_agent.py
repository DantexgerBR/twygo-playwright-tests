"""Testes do QAAgent: orchestra LLM + Browser. Tudo mockado."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.agents.llm_client import RespostaLLM, ToolCall
from app.agents.qa_agent import QAAgent, ResultadoExecucao
from app.state import CasoParseado, Evidencia


def _make_llm_responses(*sequencias):
    """Cria um mock de LLMClient que retorna respostas em sequência."""
    llm = MagicMock()
    llm.gerar.side_effect = list(sequencias)
    return llm


def _make_browser():
    browser = MagicMock()
    browser.current_url.return_value = "https://teste.stage.twygoead.com/admin/dashboard"
    browser.get_dom_simplificado.return_value = "<button> Salvar"
    browser.screenshot.side_effect = lambda p: p  # devolve o mesmo path
    return browser


def _caso_simples():
    return CasoParseado(
        objetivo="Validar correção de bug X",
        pre_condicoes=[],
        passos=[{"n": 1, "acao": "Clicar em Salvar", "esperado": "Mensagem de sucesso"}],
        texto_bruto="bla",
    )


def test_agent_stage_down_retorna_inconclusivo(tmp_path):
    llm = MagicMock()
    browser = _make_browser()
    agent = QAAgent(llm, browser)

    with patch("app.agents.qa_agent.verificar_stage", return_value="down"):
        result = agent.executar(
            caso=_caso_simples(),
            evidencias=[],
            documentacao=[],
            base_url="https://teste.stage.twygoead.com/",
            admin_email="x@y.com",
            admin_password="senha",
            pasta_screenshots=tmp_path,
        )

    assert result.laudo == "inconclusivo"
    assert "stage" in result.justificativa.lower() or "fora" in result.justificativa.lower()
    # Browser nem deveria ter sido iniciado
    browser.start.assert_not_called()


def test_agent_finalizar_corrigido(tmp_path):
    """LLM finaliza no primeiro turn com laudo 'corrigido'."""
    resp_finalizar = RespostaLLM(
        text="Vi a tela. Sem o bug.",
        tool_calls=[
            ToolCall(
                name="finalizar",
                args={"laudo": "corrigido", "justificativa": "Texto centralizado, sem corte."},
            )
        ],
    )
    llm = _make_llm_responses(resp_finalizar)
    browser = _make_browser()
    agent = QAAgent(llm, browser)

    with patch("app.agents.qa_agent.verificar_stage", return_value="ok"):
        result = agent.executar(
            caso=_caso_simples(),
            evidencias=[],
            documentacao=[],
            base_url="https://teste.stage.twygoead.com/",
            admin_email="x@y.com",
            admin_password="senha",
            pasta_screenshots=tmp_path,
        )

    assert result.laudo == "corrigido"
    assert "centralizado" in result.justificativa
    assert result.iteracoes == 1
    browser.start.assert_called_once()
    browser.login_twygo.assert_called_once()
    browser.close.assert_called_once()


def test_agent_clica_depois_finaliza_quebrado(tmp_path):
    """Dois turns: primeiro clica, depois finaliza com 'ainda_quebrado'."""
    resp_clicar = RespostaLLM(
        text="Vou clicar em Salvar.",
        tool_calls=[ToolCall(name="clicar", args={"seletor": "#salvar"})],
    )
    resp_finalizar = RespostaLLM(
        text="Bug ainda aparece.",
        tool_calls=[
            ToolCall(
                name="finalizar",
                args={"laudo": "ainda_quebrado", "justificativa": "Texto cortado."},
            )
        ],
    )
    llm = _make_llm_responses(resp_clicar, resp_finalizar)
    browser = _make_browser()
    agent = QAAgent(llm, browser)

    with patch("app.agents.qa_agent.verificar_stage", return_value="ok"):
        result = agent.executar(
            caso=_caso_simples(),
            evidencias=[],
            documentacao=[],
            base_url="https://teste.stage.twygoead.com/",
            admin_email="x@y.com",
            admin_password="senha",
            pasta_screenshots=tmp_path,
        )

    assert result.laudo == "ainda_quebrado"
    assert "cortado" in result.justificativa.lower()
    browser.click.assert_called_with("#salvar")


def test_agent_login_falha_retorna_inconclusivo(tmp_path):
    llm = MagicMock()
    browser = _make_browser()
    browser.login_twygo.side_effect = RuntimeError("credencial inválida")
    agent = QAAgent(llm, browser)

    with patch("app.agents.qa_agent.verificar_stage", return_value="ok"):
        result = agent.executar(
            caso=_caso_simples(),
            evidencias=[],
            documentacao=[],
            base_url="https://teste.stage.twygoead.com/",
            admin_email="x@y.com",
            admin_password="errada",
            pasta_screenshots=tmp_path,
        )

    assert result.laudo == "inconclusivo"
    assert "logar" in result.justificativa.lower() or "credencial" in result.justificativa.lower()


def test_agent_timeout_apos_max_iteracoes(tmp_path):
    """LLM nunca chama finalizar — agente deve dar timeout."""
    # Sempre retorna uma ação sem finalizar
    resp_sempre_clicar = RespostaLLM(
        text="Vou tentar clicar.",
        tool_calls=[ToolCall(name="clicar", args={"seletor": "#x"})],
    )
    llm = MagicMock()
    llm.gerar.return_value = resp_sempre_clicar
    browser = _make_browser()
    agent = QAAgent(llm, browser)
    agent.MAX_ITERACOES = 3  # reduz pra teste rápido

    with patch("app.agents.qa_agent.verificar_stage", return_value="ok"):
        result = agent.executar(
            caso=_caso_simples(),
            evidencias=[],
            documentacao=[],
            base_url="https://teste.stage.twygoead.com/",
            admin_email="x@y.com",
            admin_password="senha",
            pasta_screenshots=tmp_path,
        )

    assert result.laudo == "inconclusivo"
    assert "iterações" in result.justificativa.lower() or "iteracoes" in result.justificativa.lower()
    assert result.iteracoes == 3


def test_agent_erro_llm_retorna_inconclusivo(tmp_path):
    llm = MagicMock()
    llm.gerar.side_effect = RuntimeError("API key inválida")
    browser = _make_browser()
    agent = QAAgent(llm, browser)

    with patch("app.agents.qa_agent.verificar_stage", return_value="ok"):
        result = agent.executar(
            caso=_caso_simples(),
            evidencias=[],
            documentacao=[],
            base_url="https://teste.stage.twygoead.com/",
            admin_email="x@y.com",
            admin_password="senha",
            pasta_screenshots=tmp_path,
        )

    assert result.laudo == "inconclusivo"
    assert "llm" in result.justificativa.lower() or "api" in result.justificativa.lower()


def test_agent_on_log_callback_eh_chamado(tmp_path):
    resp = RespostaLLM(
        text="",
        tool_calls=[
            ToolCall(name="finalizar", args={"laudo": "corrigido", "justificativa": "ok"})
        ],
    )
    llm = _make_llm_responses(resp)
    browser = _make_browser()

    logs: list[str] = []
    agent = QAAgent(llm, browser, on_log=logs.append)

    with patch("app.agents.qa_agent.verificar_stage", return_value="ok"):
        agent.executar(
            caso=_caso_simples(),
            evidencias=[],
            documentacao=[],
            base_url="https://teste.stage.twygoead.com/",
            admin_email="x@y.com",
            admin_password="senha",
            pasta_screenshots=tmp_path,
        )

    # Algumas mensagens de log devem ter sido emitidas
    assert len(logs) > 0
    assert any("Stage OK" in l or "Logado" in l or "Laudo" in l for l in logs)


def test_agent_request_stop_interrompe(tmp_path):
    """Se request_stop for chamado, agente para na próxima iteração."""
    resp = RespostaLLM(
        text="Vou clicar.",
        tool_calls=[ToolCall(name="clicar", args={"seletor": "#x"})],
    )
    llm = MagicMock()
    llm.gerar.return_value = resp
    browser = _make_browser()
    agent = QAAgent(llm, browser)

    # Para depois da primeira chamada
    chamadas = [0]
    original_gerar = llm.gerar

    def gerar_e_parar(*a, **k):
        chamadas[0] += 1
        if chamadas[0] == 2:
            agent.request_stop()
        return resp

    llm.gerar.side_effect = gerar_e_parar

    with patch("app.agents.qa_agent.verificar_stage", return_value="ok"):
        result = agent.executar(
            caso=_caso_simples(),
            evidencias=[],
            documentacao=[],
            base_url="https://teste.stage.twygoead.com/",
            admin_email="x@y.com",
            admin_password="senha",
            pasta_screenshots=tmp_path,
        )

    assert result.laudo == "inconclusivo"
    assert "interrompida" in result.justificativa.lower() or "usuário" in result.justificativa.lower()
