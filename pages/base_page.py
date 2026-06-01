import re

from playwright.sync_api import Page, Locator, expect

# Botões que fecham as várias modais de NPS/pesquisa do Twygo.
_NPS_BOTOES = ["Pergunte depois", "Perguntar depois", "Agora não", "Pular",
               "Não, obrigado", "Fechar", "Depois"]
_NPS_FECHAR_SEL = [".chakra-modal__close-btn", "[aria-label='Close']",
                   "[aria-label='Fechar']", "button[aria-label*='ech']"]


def _dispensar_nps(page: Page) -> None:
    """Fecha modais de NPS/pesquisa bloqueantes (várias variantes). Best-effort:
    tenta botões conhecidos, depois o X de fechar, depois Escape se houver modal."""
    for _ in range(2):
        fechou = False
        for txt in _NPS_BOTOES:
            try:
                b = page.get_by_role("button", name=re.compile(txt, re.I)).first
                if b.count() and b.is_visible():
                    b.click(timeout=1500); page.wait_for_timeout(500); fechou = True; break
            except Exception:
                pass
        if not fechou:
            for sel in _NPS_FECHAR_SEL:
                try:
                    b = page.locator(sel).first
                    if b.count() and b.is_visible():
                        b.click(timeout=1500); page.wait_for_timeout(500); fechou = True; break
                except Exception:
                    pass
        if not fechou:
            try:
                if page.locator(".chakra-modal__content, [role=dialog], [role=alertdialog]").filter(
                    visible=True
                ).count():
                    page.keyboard.press("Escape"); page.wait_for_timeout(500); fechou = True
            except Exception:
                pass
        if not fechou:
            break


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def toast(self, texto: str) -> Locator:
        return self.page.get_by_text(texto, exact=False)

    def aguardar_toast_sucesso(self, texto: str, timeout: int = 10000) -> None:
        expect(self.toast(texto)).to_be_visible(timeout=timeout)

    def dispensar_nps(self) -> None:
        """Fecha modais de NPS / pesquisa bloqueantes do Twygo (várias variantes),
        se aparecerem. Mesmo comportamento de `scripts/_twygo.dispensar_nps`."""
        _dispensar_nps(self.page)
