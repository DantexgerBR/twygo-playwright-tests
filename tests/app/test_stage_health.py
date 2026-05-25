"""Testes do stage_health: classifica respostas HTTP em ok/down/erro."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from app.services.stage_health import verificar_stage


def _resp(status: int) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    return r


def test_url_vazia_retorna_erro():
    assert verificar_stage("") == "erro"


def test_status_200_retorna_ok():
    with patch("httpx.get", return_value=_resp(200)):
        assert verificar_stage("https://teste.stage.twygoead.com/") == "ok"


def test_status_302_redirect_retorna_ok():
    """Login redirect: stage está vivo, só pedindo auth."""
    with patch("httpx.get", return_value=_resp(302)):
        assert verificar_stage("https://teste.stage.twygoead.com/") == "ok"


def test_status_401_retorna_ok():
    """Stage respondeu com auth required — está vivo."""
    with patch("httpx.get", return_value=_resp(401)):
        assert verificar_stage("https://teste.stage.twygoead.com/") == "ok"


def test_status_500_retorna_down():
    with patch("httpx.get", return_value=_resp(500)):
        assert verificar_stage("https://teste.stage.twygoead.com/") == "down"


def test_status_502_retorna_down():
    with patch("httpx.get", return_value=_resp(502)):
        assert verificar_stage("https://teste.stage.twygoead.com/") == "down"


def test_connect_error_retorna_down():
    """Servidor inacessível (devs reiniciando) → down."""
    with patch("httpx.get", side_effect=httpx.ConnectError("recusou")):
        assert verificar_stage("https://teste.stage.twygoead.com/") == "down"


def test_timeout_retorna_down():
    with patch("httpx.get", side_effect=httpx.TimeoutException("demorou")):
        assert verificar_stage("https://teste.stage.twygoead.com/") == "down"


def test_outro_http_error_retorna_erro():
    """Erro genérico de protocolo HTTP — classificado como erro do cliente."""
    with patch("httpx.get", side_effect=httpx.HTTPError("xpto")):
        assert verificar_stage("https://teste.stage.twygoead.com/") == "erro"


def test_excecao_inesperada_retorna_erro():
    with patch("httpx.get", side_effect=ValueError("boom")):
        assert verificar_stage("https://teste.stage.twygoead.com/") == "erro"
