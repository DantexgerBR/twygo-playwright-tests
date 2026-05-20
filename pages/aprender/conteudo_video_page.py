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
        # Botão "Baixar conteúdo" exposto no Aprender quando Segurança da
        # atividade é "Somente Baixar" ou "Visualizar e Baixar". É um Chakra
        # Button fora do Plyr, não um controle do player.
        self.botao_download: Locator = page.locator("#download-content")

    def abrir_atividade(self, base_url: str, evento_id: str, atividade_id: str) -> None:
        # TODO confirmar rota do Aprender — usando mesma rota da edição sem /edit como hipótese.
        self.page.goto(
            f"{base_url}e/{evento_id}/contents/{atividade_id}",
            wait_until="networkidle",
            timeout=30000,
        )

    def video_esta_visivel(self) -> bool:
        return self.player.first.is_visible()

    def tem_marca_dagua(self) -> bool:
        return self.overlay_marca_dagua.count() > 0
