from playwright.sync_api import Page, Locator, expect


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def toast(self, texto: str) -> Locator:
        return self.page.get_by_text(texto, exact=False)

    def aguardar_toast_sucesso(self, texto: str, timeout: int = 10000) -> None:
        expect(self.toast(texto)).to_be_visible(timeout=timeout)
