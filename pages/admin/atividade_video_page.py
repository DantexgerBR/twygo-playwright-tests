from playwright.sync_api import Page, Locator

from pages.base_page import BasePage


class AtividadeVideoPage(BasePage):
    """Página de edição de uma atividade do tipo vídeo (área admin, Chakra UI)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.checkbox_marca_dagua_input: Locator = page.locator("#water-mark-video-enabled")
        self.checkbox_marca_dagua_label: Locator = page.locator(
            "label.chakra-checkbox", has_text="Habilitar marca d'água no vídeo"
        )
        # Asserção principal de "marcado" usa o label (input nativo é hidden).
        self.checkbox_marca_dagua: Locator = self.checkbox_marca_dagua_input
        # Painel de configuração da marca d'água: container que segue o checkbox dentro da seção.
        # TODO: refinar quando inspecionarmos a UI desmarcada.
        self.painel_config_marca_dagua: Locator = page.locator(
            "input[name='water_mark_text'], input[name='watermark_text'], [data-testid='marca-dagua-config']"
        )
        self.preview_marca_dagua: Locator = page.locator(
            "[data-testid='marca-dagua-preview'], .marca-dagua-preview, img[alt*='marca']"
        )
        self.botao_salvar: Locator = page.get_by_role("button", name="Salvar")

    def abrir_edicao(self, base_url: str, evento_id: str, atividade_id: str) -> None:
        self.page.goto(
            f"{base_url}e/{evento_id}/contents/{atividade_id}/edit",
            wait_until="networkidle",
            timeout=30000,
        )

    def desmarcar_marca_dagua(self) -> None:
        # Input nativo é hidden no Chakra — clicar no label visual.
        self.checkbox_marca_dagua_label.scroll_into_view_if_needed()
        self.checkbox_marca_dagua_label.click()

    def esta_marcado(self) -> bool:
        # data-checked no label Chakra indica estado marcado.
        return self.checkbox_marca_dagua_label.get_attribute("data-checked") is not None

    def salvar(self) -> None:
        self.botao_salvar.scroll_into_view_if_needed()
        self.botao_salvar.click()

    def aguardar_salvamento(self, texto_toast: str, timeout: int = 8000) -> bool:
        """Espera o toast de sucesso OU o redirect para a lista de contents.
        Retorna True se algum dos dois aconteceu (= save bem-sucedido)."""
        try:
            self.aguardar_toast_sucesso(texto_toast, timeout=timeout)
            return True
        except Exception:
            try:
                self.page.wait_for_url("**/contents", timeout=timeout)
                return True
            except Exception:
                return False
