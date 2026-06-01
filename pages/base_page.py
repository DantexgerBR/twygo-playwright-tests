from playwright.sync_api import Page, Locator, expect


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def toast(self, texto: str) -> Locator:
        return self.page.get_by_text(texto, exact=False)

    def aguardar_toast_sucesso(self, texto: str, timeout: int = 10000) -> None:
        expect(self.toast(texto)).to_be_visible(timeout=timeout)

    def dispensar_nps(self) -> None:
        """Fecha a modal de NPS / modais bloqueantes do Twygo, se aparecerem.
        Mesmo comportamento de `scripts/_twygo.dispensar_nps`, para uso no POM."""
        for sel in (
            "button:has-text('Pergunte depois')",
            ".chakra-modal__close-btn",
            "[aria-label='Close']",
        ):
            loc = self.page.locator(sel).first
            try:
                if loc.count() and loc.is_visible():
                    loc.click(timeout=1500)
                    self.page.wait_for_timeout(500)
            except Exception:
                pass
