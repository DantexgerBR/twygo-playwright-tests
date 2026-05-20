from playwright.sync_api import Page

from pages.base_page import BasePage


class LoginPage(BasePage):
    """Tela de login da Twygo (rota /login)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.campo_email = page.locator("#user_email")
        self.campo_senha = page.locator("#user_password")
        self.botao_entrar = page.locator("#user_submit")

    def login(self, base_url: str, email: str, password: str) -> None:
        self.page.goto(base_url + "login", wait_until="domcontentloaded")
        self.campo_email.fill(email)
        self.campo_senha.fill(password)
        self.botao_entrar.click()
        self.page.wait_for_load_state("networkidle", timeout=20000)
