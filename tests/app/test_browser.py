"""Testes do Browser wrapper. Mockam sync_playwright pra não abrir Chrome de verdade."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.browser import Browser


def _setup_playwright_mock(mock_sp):
    """Configura a cadeia de mocks: sync_playwright().start() → playwright → chromium → browser → context → page."""
    pw = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()
    page.url = ""

    mock_sp.return_value.start.return_value = pw
    pw.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page
    return pw, browser, context, page


def test_start_close_basico():
    with patch("playwright.sync_api.sync_playwright") as mock_sp:
        _, _, _, page = _setup_playwright_mock(mock_sp)
        b = Browser(headless=True)
        b.start()
        assert b.page is page
        b.close()
        assert b.page is None


def test_context_manager():
    with patch("playwright.sync_api.sync_playwright") as mock_sp:
        _, _, _, page = _setup_playwright_mock(mock_sp)
        with Browser(headless=True) as b:
            assert b.page is page
        # Após o with, page deve ser None
        assert b.page is None


def test_login_twygo_chama_seletores_certos():
    with patch("playwright.sync_api.sync_playwright") as mock_sp:
        _, _, _, page = _setup_playwright_mock(mock_sp)
        page.url = "https://teste.stage.twygoead.com/dashboard_students"
        with Browser(headless=True) as b:
            b.login_twygo("https://teste.stage.twygoead.com/", "foo@bar.com", "senha")

        # Verifica login (sem org_id, não troca pra admin)
        assert page.goto.called
        # fill foi chamado 2 vezes (email + senha)
        assert page.fill.call_count == 2
        # click no botão de login
        page.click.assert_called_with("#user_submit")


def test_login_twygo_com_org_id_troca_para_admin():
    with patch("playwright.sync_api.sync_playwright") as mock_sp:
        _, _, _, page = _setup_playwright_mock(mock_sp)
        page.url = "https://teste.stage.twygoead.com/dashboard_students"
        with Browser(headless=True) as b:
            b.login_twygo(
                "https://teste.stage.twygoead.com/",
                "foo@bar.com",
                "senha",
                org_id="36675",
            )

        # 1ª goto: /login, 2ª goto: /o/36675/events?...profile=admin
        urls = [c.args[0] for c in page.goto.call_args_list]
        assert any("/login" in u for u in urls)
        assert any("/o/36675/" in u and "profile=admin" in u for u in urls)


def test_login_twygo_detecta_org_id_da_url():
    """Se a URL após login tem /o/<id>/, usa esse id pra trocar pra admin."""
    with patch("playwright.sync_api.sync_playwright") as mock_sp:
        _, _, _, page = _setup_playwright_mock(mock_sp)
        # Simula que após login Twygo já redirecionou pra /o/12345/...
        page.url = "https://teste.stage.twygoead.com/o/12345/dashboard"
        with Browser(headless=True) as b:
            b.login_twygo("https://teste.stage.twygoead.com/", "foo@bar.com", "senha")

        urls = [c.args[0] for c in page.goto.call_args_list]
        assert any("/o/12345/" in u for u in urls)


def test_login_twygo_sem_start_levanta():
    b = Browser()
    with pytest.raises(RuntimeError, match="não iniciado"):
        b.login_twygo("x", "y", "z")


def test_acoes_basicas_delegam_para_page():
    with patch("playwright.sync_api.sync_playwright") as mock_sp:
        _, _, _, page = _setup_playwright_mock(mock_sp)
        with Browser(headless=True) as b:
            b.goto("https://exemplo.com")
            page.goto.assert_called_with(
                "https://exemplo.com",
                wait_until="domcontentloaded",
                timeout=30000,
            )

            b.click("#salvar")
            page.click.assert_called_with("#salvar", timeout=5000)

            b.fill("#input", "texto")
            page.fill.assert_called_with("#input", "texto", timeout=5000)


def test_screenshot_cria_pasta_e_chama_page(tmp_path):
    with patch("playwright.sync_api.sync_playwright") as mock_sp:
        _, _, _, page = _setup_playwright_mock(mock_sp)
        destino = tmp_path / "subdir" / "tela.png"
        with Browser(headless=True) as b:
            resultado = b.screenshot(destino)

        assert resultado == destino
        assert destino.parent.exists()
        page.screenshot.assert_called_once()
        screenshot_kwargs = page.screenshot.call_args.kwargs
        assert screenshot_kwargs["path"] == str(destino)


def test_get_dom_simplificado_retorna_texto():
    with patch("playwright.sync_api.sync_playwright") as mock_sp:
        _, _, _, page = _setup_playwright_mock(mock_sp)
        page.evaluate.return_value = "<button> Salvar\n<input[email]> "
        with Browser(headless=True) as b:
            dom = b.get_dom_simplificado()
        assert "Salvar" in dom


def test_get_dom_simplificado_trunca():
    with patch("playwright.sync_api.sync_playwright") as mock_sp:
        _, _, _, page = _setup_playwright_mock(mock_sp)
        page.evaluate.return_value = "x" * 20000
        with Browser(headless=True) as b:
            dom = b.get_dom_simplificado(max_chars=500)
        assert len(dom) == 500


def test_get_dom_sem_browser_retorna_vazio():
    b = Browser()
    assert b.get_dom_simplificado() == ""


def test_current_url_sem_browser_retorna_vazio():
    b = Browser()
    assert b.current_url() == ""
