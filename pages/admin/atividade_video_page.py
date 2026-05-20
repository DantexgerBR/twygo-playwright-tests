from playwright.sync_api import Page, Locator

from pages.base_page import BasePage


class AtividadeVideoPage(BasePage):
    """Página de edição de uma atividade do tipo vídeo (área admin)."""

    def __init__(self, page: Page):
        super().__init__(page)
        # TODO confirmar seletores reais inspecionando a UI:
        self.checkbox_marca_dagua: Locator = page.get_by_label(
            "Habilitar marca d'água no vídeo"
        )
        self.painel_config_marca_dagua: Locator = page.locator(
            "[data-testid='config-marca-dagua'], .marca-dagua-config"
        )
        self.preview_marca_dagua: Locator = page.locator(
            "[data-testid='preview-marca-dagua'], .marca-dagua-preview"
        )
        self.botao_salvar: Locator = page.get_by_role("button", name="Salvar")

    def abrir_edicao(self, base_url: str, atividade_id: str) -> None:
        # TODO confirmar rota real de edição de atividade na Twygo.
        self.page.goto(f"{base_url}admin/atividades/{atividade_id}/edit")
        self.page.wait_for_load_state("networkidle", timeout=15000)

    def desmarcar_marca_dagua(self) -> None:
        self.checkbox_marca_dagua.uncheck()

    def salvar(self) -> None:
        self.botao_salvar.click()
