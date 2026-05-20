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
