from playwright.sync_api import Page, Locator

from pages.base_page import BasePage


class ConteudoVideoPage(BasePage):
    """Página do aluno no Aprender visualizando uma atividade de vídeo."""

    def __init__(self, page: Page):
        super().__init__(page)
        # TODO confirmar seletores reais (player Twygo pode ser custom ou um player de terceiros).
        self.player: Locator = page.locator("video, [data-testid='video-player']")
        self.overlay_marca_dagua: Locator = page.locator(
            "[data-testid='marca-dagua-overlay'], .marca-dagua-overlay, .watermark"
        )

    def abrir_atividade(self, base_url: str, atividade_id: str) -> None:
        # TODO confirmar rota real do Aprender.
        self.page.goto(f"{base_url}aprender/atividades/{atividade_id}")
        self.page.wait_for_load_state("networkidle", timeout=15000)

    def video_esta_visivel(self) -> bool:
        return self.player.first.is_visible()

    def tem_marca_dagua(self) -> bool:
        return self.overlay_marca_dagua.count() > 0
