"""Listagem de atividades de um curso: /e/{evento}/contents."""
from playwright.sync_api import Page, Locator

from pages.base_page import BasePage


class ListagemAtividadesPage(BasePage):
    """Página de listagem de atividades do curso (admin, legacy Rails + jQuery)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.botao_copiar_atividade: Locator = page.locator(".copy_content_btn")
        # Modal de copy (simplemodal jQuery)
        self.modal_copy: Locator = page.locator(".simplemodal-container, #simplemodal-container")
        self.botao_salvar_copy: Locator = page.locator(".save_copy_content_btn")
        self.itens_lista: Locator = page.locator("li.dd-item")

    def abrir(self, base_url: str, evento_id: str) -> None:
        self.page.goto(
            f"{base_url}e/{evento_id}/contents",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        self.page.wait_for_timeout(6000)

    def ids_atividades(self) -> list[str]:
        return self.page.evaluate(
            "() => Array.from(document.querySelectorAll('li.dd-item[data-id]'))"
            ".map(li => li.getAttribute('data-id'))"
        )

    def abrir_modal_copiar(self) -> None:
        self.botao_copiar_atividade.click()
        # simplemodal anima — espera o container aparecer
        self.modal_copy.first.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(1500)

    def selecionar_curso_origem(self, evento_origem_id: str) -> None:
        """Clica no <li> do curso de origem dentro do modal aberto.
        O modal lista todos os cursos OUTROS que o atual com o formato 'ID - Título'."""
        # O overlay pode interceptar o click — usar disparo direto via JS no <li>
        clicou = self.page.evaluate(
            """(eventoId) => {
                const m = document.querySelector('#simplemodal-container, .simplemodal-container');
                if (!m) return false;
                const re = new RegExp('^' + eventoId + '\\\\s*-');
                const items = Array.from(m.querySelectorAll('li, a, div'))
                    .filter(el => re.test((el.innerText || '').trim()));
                if (!items.length) return false;
                // pega o mais específico (menor)
                items.sort((a, b) => (a.innerText || '').length - (b.innerText || '').length);
                items[0].click();
                return true;
            }""",
            evento_origem_id,
        )
        if not clicou:
            raise RuntimeError(f"Curso origem {evento_origem_id} não encontrado no modal de cópia")
        self.page.wait_for_timeout(3000)

    def selecionar_atividade_no_modal(self, atividade_id: str) -> None:
        """Após escolher o curso, o modal lista as atividades — selecionar a alvo."""
        clicou = self.page.evaluate(
            """(ativId) => {
                const m = document.querySelector('#simplemodal-container, .simplemodal-container');
                if (!m) return false;
                // procura li/input que tenha o id da atividade como data-id, value, ou texto
                const candidatos = Array.from(m.querySelectorAll('li, a, input, label, div'))
                    .filter(el => {
                        if (el.getAttribute('data-id') === ativId) return true;
                        if (el.value === ativId) return true;
                        if ((el.innerText || '').trim().startsWith(ativId)) return true;
                        return false;
                    });
                if (!candidatos.length) return false;
                candidatos[0].click();
                return true;
            }""",
            atividade_id,
        )
        if not clicou:
            # fallback: clicar no PRIMEIRO item disponível (caso a lista mostre só atividades do curso já selecionado)
            self.page.evaluate(
                """() => {
                    const m = document.querySelector('#simplemodal-container, .simplemodal-container');
                    if (!m) return;
                    const items = Array.from(m.querySelectorAll('li[data-id], input[type="checkbox"], input[type="radio"]'));
                    if (items.length) items[0].click();
                }"""
            )
        self.page.wait_for_timeout(2000)

    def salvar_copy(self) -> None:
        self.botao_salvar_copy.click()
        # após salvar, o JS recarrega a listagem ou faz reload — esperar
        self.page.wait_for_timeout(6000)
