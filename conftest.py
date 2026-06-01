import os
import pytest
from dotenv import load_dotenv
from playwright.sync_api import BrowserContext, Page

from pages.login_page import LoginPage

load_dotenv()


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.environ.get("BASE_URL")
    if not url:
        pytest.fail("BASE_URL não definida no .env")
    return url.rstrip("/") + "/"


@pytest.fixture(scope="session")
def admin_credentials() -> dict:
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    if not email or not password:
        pytest.fail("ADMIN_EMAIL/ADMIN_PASSWORD não definidos no .env")
    return {"email": email, "password": password}


@pytest.fixture(scope="session")
def aluno_credentials() -> dict:
    email = os.environ.get("ALUNO_EMAIL")
    password = os.environ.get("ALUNO_PASSWORD")
    if not email or not password:
        pytest.fail("ALUNO_EMAIL/ALUNO_PASSWORD não definidos no .env")
    return {"email": email, "password": password}


@pytest.fixture(scope="session")
def base_url_destinataria() -> str:
    url = os.environ.get("BASE_URL_DESTINATARIA")
    if not url:
        pytest.fail("BASE_URL_DESTINATARIA não definida no .env")
    return url.rstrip("/") + "/"


@pytest.fixture(scope="session")
def admin_destinataria_credentials() -> dict:
    email = os.environ.get("ADMIN_DESTINATARIA_EMAIL")
    password = os.environ.get("ADMIN_DESTINATARIA_PASSWORD")
    if not email or not password:
        pytest.fail("ADMIN_DESTINATARIA_EMAIL/ADMIN_DESTINATARIA_PASSWORD não definidos no .env")
    return {"email": email, "password": password}


@pytest.fixture
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1366, "height": 768},
        "locale": "pt-BR",
    }


def _login(context: BrowserContext, base_url: str, creds: dict) -> Page:
    page = context.new_page()
    LoginPage(page).login(base_url, creds["email"], creds["password"])
    return page


@pytest.fixture
def admin_logado(browser, browser_context_args, base_url, admin_credentials) -> Page:
    context = browser.new_context(**browser_context_args)
    page = _login(context, base_url, admin_credentials)
    yield page
    context.close()


@pytest.fixture
def aluno_logado(browser, browser_context_args, base_url, aluno_credentials) -> Page:
    context = browser.new_context(**browser_context_args)
    page = _login(context, base_url, aluno_credentials)
    yield page
    context.close()


@pytest.fixture
def admin_em(browser, browser_context_args):
    """Factory de login admin por ambiente (perfil do .env).

        page, base = admin_em("RECERT")   # usa RECERT_BASE_URL/ORG_ID/EMAIL/SENHA
        page, base = admin_em("EDUAPI")    # idem EDUAPI_*

    Faz `pytest.skip` (não falha) se as credenciais do perfil não estiverem no .env —
    assim os testes E2E de stage não viram falso negativo em quem não tem o ambiente.
    """
    contexts = []

    def _logar(prefix: str):
        base = os.environ.get(f"{prefix}_BASE_URL")
        org = os.environ.get(f"{prefix}_ORG_ID")
        email = os.environ.get(f"{prefix}_EMAIL")
        senha = os.environ.get(f"{prefix}_SENHA")
        if not (base and email and senha):
            pytest.skip(f"Credenciais {prefix}_* ausentes no .env (veja .env.example)")
        base = base.rstrip("/") + "/"
        ctx = browser.new_context(**browser_context_args)
        contexts.append(ctx)
        page = _login(ctx, base, {"email": email, "password": senha})
        if org:
            page.goto(
                f"{base}o/{org}/events?tab=events&profile=admin",
                wait_until="domcontentloaded", timeout=30000,
            )
            page.wait_for_timeout(4000)
        return page, base

    yield _logar
    for c in contexts:
        c.close()


@pytest.fixture
def admin_destinataria_logado(
    browser, browser_context_args, base_url_destinataria, admin_destinataria_credentials
) -> Page:
    """Loga na org destinatária e troca o perfil para Administrador.

    Após o login Twygo cai em /dashboard_students. O switch para admin é via
    /o/{ORG_DESTINATARIA_ID}/events?profile=admin. Requer ORG_DESTINATARIA_ID no .env.
    """
    org_id = os.environ.get("ORG_DESTINATARIA_ID")
    if not org_id:
        pytest.fail("ORG_DESTINATARIA_ID não definido no .env")

    context = browser.new_context(**browser_context_args)
    page = _login(context, base_url_destinataria, admin_destinataria_credentials)
    page.goto(
        f"{base_url_destinataria}o/{org_id}/events?tab=events&profile=admin",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    page.wait_for_timeout(5000)
    yield page
    context.close()
