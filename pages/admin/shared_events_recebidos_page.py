"""Aba 'Recebidos' em /o/{org}/shared_events da org destinatária."""
import re

from playwright.sync_api import Page, Locator

from pages.base_page import BasePage


class SharedEventsRecebidosPage(BasePage):
    """Lista shares recebidos pela org e permite aceitar/recusar.

    Fluxo:
        page = SharedEventsRecebidosPage(admin_dest_page)
        page.abrir(base_url_dest, org_dest_id)
        page.aba_recebidos()
        share_id, row_info = page.abrir_share_recebido("Construindo times de alta performance")
        page.aceitar()
    """

    def __init__(self, page: Page):
        super().__init__(page)

    def abrir(self, base_url: str, org_id: str) -> None:
        """Vai para /o/{org}/shared_events. Pré-condição: estar logado como Admin
        (ver fixture admin_destinataria_logado, que faz o switch de perfil)."""
        self.page.goto(
            f"{base_url}o/{org_id}/shared_events",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        self.page.wait_for_timeout(5000)

    def aba_recebidos(self) -> None:
        clicou = self.page.evaluate(
            r"""() => {
                const t = Array.from(document.querySelectorAll('button[role="tab"], .chakra-tabs__tab'))
                    .find(el => (el.innerText || '').trim() === 'Recebidos');
                if (!t) return false;
                t.click();
                return true;
            }"""
        )
        if not clicou:
            raise RuntimeError("Aba 'Recebidos' não encontrada em shared_events.")
        self.page.wait_for_timeout(5000)

    def linha_share(self, titulo_curso: str) -> dict | None:
        """Retorna info da linha do share (data-item-id, data-item-name, situação)
        ou None se não encontrou."""
        return self.page.evaluate(
            r"""(titulo) => {
                const re = new RegExp(titulo.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
                const row = Array.from(document.querySelectorAll('tr, [role=row]'))
                    .find(r => re.test(r.innerText || '') && r.offsetParent !== null);
                if (!row) return null;
                const text = (row.innerText || '');
                let situacao = 'desconhecida';
                if (/Pendente/i.test(text)) situacao = 'pendente';
                else if (/Aceito/i.test(text)) situacao = 'aceito';
                else if (/Recusado/i.test(text)) situacao = 'recusado';
                return {
                    dataItemId: row.getAttribute('data-item-id'),
                    dataItemName: row.getAttribute('data-item-name'),
                    text: text.slice(0, 500),
                    situacao,
                };
            }""",
            titulo_curso,
        )

    def abrir_share_recebido(self, titulo_curso: str) -> str:
        """Clica no ícone de edit (pencil) da linha do share e retorna o share_id
        capturado da URL `/o/{org}/shared_events/{share_id}/accept_shared_content`."""
        clicou = self.page.evaluate(
            r"""(titulo) => {
                const re = new RegExp(titulo.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
                const row = Array.from(document.querySelectorAll('tr, [role=row]'))
                    .find(r => re.test(r.innerText || '') && r.offsetParent !== null);
                if (!row) return 'sem-linha';
                const editIcon = Array.from(row.querySelectorAll('.material-symbols-outlined, span'))
                    .find(el => (el.innerText || '').trim() === 'edit');
                if (!editIcon) return 'sem-edit-icon';
                let p = editIcon;
                for (let i = 0; i < 6 && p; i++) {
                    if (p.tagName === 'BUTTON' || p.tagName === 'A' || p.onclick) break;
                    p = p.parentElement;
                }
                (p || editIcon).click();
                return 'clicado';
            }""",
            titulo_curso,
        )
        if clicou != "clicado":
            raise RuntimeError(f"Não consegui abrir share '{titulo_curso}': {clicou}")
        self.page.wait_for_url(re.compile(r"/shared_events/\d+/accept_shared_content"), timeout=15000)
        self.page.wait_for_timeout(4000)
        m = re.search(r"/shared_events/(\d+)/accept_shared_content", self.page.url)
        return m.group(1) if m else ""

    def aceitar(self) -> None:
        """Clica no botão Aceitar (✓) na tela /accept_shared_content."""
        btn = self.page.get_by_role("button", name="Aceitar").first
        btn.scroll_into_view_if_needed()
        btn.click()
        # toast: "Compartilhamento aceito com sucesso..."
        self.page.wait_for_timeout(6000)

    def listar_evento_espelhado(self, base_url: str, org_id: str, titulo_curso: str) -> str | None:
        """Após aceitar, busca o data-item-id da linha do curso em /o/{org}/events.
        Retorna o ID ou None."""
        self.page.goto(
            f"{base_url}o/{org_id}/events?tab=events",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        self.page.wait_for_timeout(6000)
        return self.page.evaluate(
            r"""(titulo) => {
                const re = new RegExp(titulo.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
                const row = Array.from(document.querySelectorAll('tr[data-item-name], tr[data-item-id]'))
                    .find(r => re.test(r.getAttribute('data-item-name') || r.innerText || '') && r.offsetParent !== null);
                return row ? row.getAttribute('data-item-id') : null;
            }""",
            titulo_curso,
        )

    def ids_atividades(self, base_url: str, evento_id: str) -> list[dict]:
        """Em /e/{evento}/contents da destinatária, lista as atividades."""
        self.page.goto(
            f"{base_url}e/{evento_id}/contents",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        self.page.wait_for_timeout(6000)
        return self.page.evaluate(
            r"""() => Array.from(document.querySelectorAll('li.dd-item[data-id]'))
                .map(li => ({
                    id: li.getAttribute('data-id'),
                    title: li.getAttribute('data-title') || (li.innerText || '').trim().slice(0,80),
                }))"""
        )
