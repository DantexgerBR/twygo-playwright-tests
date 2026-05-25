"""Testes do llm_client: estruturas + conversões pra Gemini com mock."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.agents.llm_client import (
    GeminiClient,
    Mensagem,
    RespostaLLM,
    Tool,
    ToolCall,
    criar_cliente,
)


def test_dataclasses_basicos():
    msg = Mensagem(role="user", text="oi")
    assert msg.role == "user"
    assert msg.text == "oi"
    assert msg.image_path is None

    tc = ToolCall(name="click", args={"selector": "#salvar"})
    assert tc.name == "click"
    assert tc.args["selector"] == "#salvar"

    resp = RespostaLLM(text="ok")
    assert resp.text == "ok"
    assert resp.tool_calls == []


def test_gemini_client_exige_api_key():
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiClient(api_key="")


def test_criar_cliente_provedor_desconhecido():
    with pytest.raises(ValueError, match="desconhecido"):
        criar_cliente(provedor="openai")


def test_gemini_client_gerar_texto_simples():
    """Mocka o SDK do google.genai e verifica que parseia texto da resposta."""
    fake_resp = MagicMock()
    fake_part = MagicMock()
    fake_part.text = "Próximo passo: clicar em Salvar."
    fake_part.function_call = None
    fake_resp.candidates = [MagicMock()]
    fake_resp.candidates[0].content.parts = [fake_part]

    with patch("google.genai.Client") as ClientMock:
        instance = ClientMock.return_value
        instance.models.generate_content.return_value = fake_resp

        client = GeminiClient(api_key="fake-key")
        resp = client.gerar(
            system_instruction="Você é QA.",
            mensagens=[Mensagem(role="user", text="oi")],
            tools=[],
        )

        assert resp.text == "Próximo passo: clicar em Salvar."
        assert resp.tool_calls == []


def test_gemini_client_gerar_com_tool_call():
    fake_resp = MagicMock()
    fake_part = MagicMock()
    fake_part.text = ""
    fake_fc = MagicMock()
    fake_fc.name = "click"
    fake_fc.args = {"selector": "#salvar"}
    fake_part.function_call = fake_fc
    fake_resp.candidates = [MagicMock()]
    fake_resp.candidates[0].content.parts = [fake_part]

    with patch("google.genai.Client") as ClientMock:
        instance = ClientMock.return_value
        instance.models.generate_content.return_value = fake_resp

        client = GeminiClient(api_key="fake-key")
        resp = client.gerar(
            system_instruction="QA",
            mensagens=[Mensagem(role="user", text="clica salvar")],
            tools=[Tool(name="click", description="clica", parameters={})],
        )

        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "click"
        assert resp.tool_calls[0].args == {"selector": "#salvar"}


def test_gemini_client_com_imagem(tmp_path):
    """Mensagem com image_path deve incluir bytes da imagem na conversão."""
    img = tmp_path / "tela.png"
    img.write_bytes(b"\x89PNG-fake-bytes")

    fake_resp = MagicMock()
    fake_resp.candidates = []  # vazia: parser não quebra

    with patch("google.genai.Client") as ClientMock:
        instance = ClientMock.return_value
        instance.models.generate_content.return_value = fake_resp

        client = GeminiClient(api_key="fake-key")
        resp = client.gerar(
            system_instruction="",
            mensagens=[Mensagem(role="user", text="o que tem na tela?", image_path=img)],
            tools=[],
        )

        # Verifica que generate_content foi chamado
        assert instance.models.generate_content.called
        call_kwargs = instance.models.generate_content.call_args.kwargs
        # contents deve ter sido construído com 1 mensagem
        assert "contents" in call_kwargs
        assert len(call_kwargs["contents"]) == 1


def test_gemini_client_candidates_vazia_nao_quebra():
    """Se a API retorna sem candidates, devolve resposta vazia em vez de crash."""
    fake_resp = MagicMock()
    fake_resp.candidates = []

    with patch("google.genai.Client") as ClientMock:
        instance = ClientMock.return_value
        instance.models.generate_content.return_value = fake_resp

        client = GeminiClient(api_key="fake-key")
        resp = client.gerar(
            system_instruction="x",
            mensagens=[Mensagem(role="user", text="oi")],
            tools=[],
        )

        assert resp.text == ""
        assert resp.tool_calls == []


def test_criar_cliente_gemini_via_factory():
    with patch("google.genai.Client"):
        client = criar_cliente(provedor="gemini", api_key="fake")
        assert isinstance(client, GeminiClient)
