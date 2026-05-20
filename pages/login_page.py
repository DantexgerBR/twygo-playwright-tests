from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    """Página de login da Twygo."""

    def __init__(self, page: Page):
        super().__init__(page)
        # TODO confirmar seletores reais inspecionando a UI:
        self.campo_email = page.get_by_label("E-mail")
        self.campo_senha = page.get_by_label("Senha")
        self.botao_entrar = page.get_by_role("button", name="Entrar")

    def login(self, base_url: str, email: str, password: str) -> None:
        self.page.goto(base_url)
        self.campo_email.fill(email)
        self.campo_senha.fill(password)
        self.botao_entrar.click()
        # Espera login concluir — assume que a URL muda para fora de /login ou /users/sign_in.
        self.page.wait_for_load_state("networkidle", timeout=15000)
