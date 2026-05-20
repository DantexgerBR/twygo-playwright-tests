"""Aba 'Compartilhar' do curso (admin): /e/{evento}/edit?tab=share e /e/{evento}/shared_events/new."""
from playwright.sync_api import Page, Locator

from pages.base_page import BasePage


class CompartilharCursoPage(BasePage):
    """Compartilhar um curso com outra organização (interna ou externa).

    Fluxo:
        page = CompartilharCursoPage(admin_page)
        page.abrir_aba_share(base_url, evento_id)
        page.clicar_adicionar()
        page.escolher_consumer_type("interno"|"externo")
        page.escolher_shared_type("copia_livre"|"controlado")
        page.escolher_ambiente_destino("Nome da org")  # via react-select
        page.salvar()
    """

    SHARED_TYPE = {
        "copia_livre": "0",
        "controlado": "1",
    }
    CONSUMER_TYPE = {
        "interno": "0",
        "externo": "1",
    }

    def __init__(self, page: Page):
        super().__init__(page)
        self.tab_compartilhar: Locator = page.locator('button[data-test-id="tab-share"]')
        self.botao_adicionar: Locator = page.locator("#shared-events-add-button")
        self.botao_salvar: Locator = page.locator("#save-shared-events-form-button")
        self.botao_cancelar: Locator = page.locator("#cancel-shared-events-form-button")
        self.botao_voltar: Locator = page.locator("#back-to-shared-events")
        self.combobox_ambientes: Locator = page.locator('input[role="combobox"]').first
        # Modo externo
        self.input_token_externo: Locator = page.locator("#external_environment_token")
        self.checkbox_termos: Locator = page.locator("#shared-events-terms-checkbox")

    def abrir_aba_share(self, base_url: str, evento_id: str) -> None:
        """Vai direto para /e/{evento}/edit?tab=share."""
        self.page.goto(
            f"{base_url}e/{evento_id}/edit?tab=share",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        self.page.wait_for_timeout(6000)

    def existe_share_para(self, nome_org: str) -> bool:
        """Verifica na listagem 'Concedidos' (aba share atual) se já há um share
        para a org `nome_org`. Útil para pular passo 2 quando o share já existe."""
        return bool(self.page.evaluate(
            r"""(nome) => {
                const re = new RegExp(nome.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
                return Array.from(document.querySelectorAll('tr'))
                    .some(r => re.test(r.innerText || '') && r.offsetParent !== null);
            }""",
            nome_org,
        ))

    def clicar_adicionar(self) -> None:
        """Clica em Adicionar e aguarda navegação para /shared_events/new."""
        self.page.evaluate(
            "() => document.querySelector('#shared-events-add-button')?.click()"
        )
        self.page.wait_for_url("**/shared_events/new", timeout=15000)
        self.page.wait_for_timeout(4000)

    def escolher_consumer_type(self, modo: str) -> None:
        """modo: 'interno' ou 'externo'."""
        valor = self.CONSUMER_TYPE[modo]
        self.page.evaluate(
            "(v) => document.querySelector(`input[name='consumer_type'][value='${v}']`)?.click()",
            valor,
        )
        self.page.wait_for_timeout(1000)

    def escolher_shared_type(self, modo: str) -> None:
        """modo: 'copia_livre' ou 'controlado' (espelhado)."""
        valor = self.SHARED_TYPE[modo]
        self.page.evaluate(
            "(v) => document.querySelector(`input[name='shared_type'][value='${v}']`)?.click()",
            valor,
        )
        self.page.wait_for_timeout(1000)

    def listar_opcoes_ambientes(self) -> list[str]:
        """Abre o react-select de Ambientes e retorna o texto das opções disponíveis.
        Retorna [] se nenhuma org destinatária está acessível."""
        self.combobox_ambientes.click()
        self.page.wait_for_timeout(2500)
        opcoes = self.page.evaluate(
            r"""() => Array.from(document.querySelectorAll(
                '[role="option"], [class*="select__option"], .chakra-react-select__option'
            )).map(el => (el.innerText || '').trim()).filter(Boolean)"""
        )
        return opcoes or []

    def escolher_ambiente_destino(self, nome_org: str) -> bool:
        """Seleciona a org destinatária pelo nome no react-select. Retorna True se
        encontrou a opção; False se a lista está vazia ou o nome não bate."""
        self.combobox_ambientes.click()
        self.page.wait_for_timeout(2500)
        self.combobox_ambientes.fill(nome_org)
        self.page.wait_for_timeout(2500)
        clicou = self.page.evaluate(
            r"""(nome) => {
                const opts = Array.from(document.querySelectorAll(
                    '[role="option"], [class*="select__option"], .chakra-react-select__option'
                ));
                const alvo = opts.find(el =>
                    (el.innerText || '').trim().toLowerCase().includes(nome.toLowerCase())
                );
                if (!alvo) return false;
                alvo.click();
                return true;
            }""",
            nome_org,
        )
        self.page.wait_for_timeout(1500)
        return bool(clicou)

    def preencher_token_externo(self, token: str) -> None:
        """Preenche o campo 'Token do ambiente externo' (válido só com consumer_type=externo)."""
        self.input_token_externo.scroll_into_view_if_needed()
        self.input_token_externo.fill(token)
        self.page.wait_for_timeout(1000)

    def aceitar_termos(self) -> None:
        """Marca o checkbox de aceite dos termos (obrigatório em compartilhamento externo)."""
        # O input nativo costuma ser hidden; usar click direto via JS é mais robusto.
        self.page.evaluate(
            "() => document.querySelector('#shared-events-terms-checkbox')?.click()"
        )
        self.page.wait_for_timeout(800)

    def ler_estado_form(self) -> dict:
        """Snapshot dos radios e do select para asserções."""
        return self.page.evaluate(r"""() => {
            const radios = Array.from(document.querySelectorAll('input[type=radio]'))
                .map(r => ({name: r.name, value: r.value, checked: r.checked}));
            const combo = document.querySelector('input[role="combobox"]');
            const token = document.querySelector('#external_environment_token');
            const terms = document.querySelector('#shared-events-terms-checkbox');
            return {
                radios,
                ambientes_value: combo?.value || '',
                token_value: token?.value || '',
                termos_checked: terms?.checked ?? null,
            };
        }""")

    def salvar(self) -> None:
        self.botao_salvar.scroll_into_view_if_needed()
        self.botao_salvar.click()
        self.page.wait_for_timeout(5000)
