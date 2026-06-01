"""Page Object da aba Aprendizagem (visão admin) de um conteúdo/trilha.

Encapsula a tabela de participantes (uma linha por inscrição/geração), o kebab
(menu Chakra) de cada linha e a aba "Respostas de questionário". A lógica espelha
`scripts/_twygo.py` (que serve os scripts adhoc); este POM serve os testes pytest.

Rota: /e/{evento_id}/learning
"""
from playwright.sync_api import Page

from pages.base_page import BasePage

# JS: o Chakra mantém TODOS os menus montados; só 1 fica realmente visível.
_JS_MENU_VISIVEL = (
    "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
    "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;})"
)


class AprendizagemPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.aba_aprendizagem = page.get_by_text("Aprendizagem", exact=True)
        self.aba_respostas = page.get_by_text("Respostas de questionário", exact=False)

    # ---- navegação ----
    def abrir(self, base_url: str, evento_id: str) -> None:
        self.page.goto(
            f"{base_url.rstrip('/')}/e/{evento_id}/learning",
            wait_until="domcontentloaded", timeout=30000,
        )
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        self.page.wait_for_timeout(4000)
        self.dispensar_nps()

    def ir_para_respostas_questionario(self) -> None:
        self.aba_respostas.first.click(timeout=8000)
        self.page.wait_for_timeout(4000)
        self.dispensar_nps()

    # ---- tabela de participantes (colunas mapeadas pelo CABEÇALHO, não regex) ----
    def participantes(self, filtro_email: str = None) -> list:
        """[{itemId, email, progresso, desempenho, pontuacao, certificado, aprovado}]."""
        return self.page.evaluate(
            r"""(filtro)=>{
                const heads=Array.from(document.querySelectorAll('thead th,thead td')).map(h=>(h.innerText||'').replace(/\s+/g,' ').trim());
                const iP=heads.findIndex(h=>/Progresso/i.test(h)), iD=heads.findIndex(h=>/Desempenho/i.test(h)),
                      iPt=heads.findIndex(h=>/Pontua/i.test(h)), iC=heads.findIndex(h=>/Certificado/i.test(h));
                const out=[];
                document.querySelectorAll('tr[data-item-id]').forEach(r=>{
                    const email=((r.innerText||'').match(/[\w.\-]+@[\w.\-]+/)||[''])[0];
                    if(filtro && email!==filtro) return;
                    const tds=Array.from(r.querySelectorAll('td')).map(td=>(td.innerText||'').replace(/\s+/g,' ').trim());
                    const sw=r.querySelector('input[type=checkbox]');
                    out.push({itemId:r.getAttribute('data-item-id'),email,
                        progresso:iP>=0?tds[iP]:'',desempenho:iD>=0?tds[iD]:'',
                        pontuacao:iPt>=0?tds[iPt]:'',certificado:iC>=0?tds[iC]:'',
                        aprovado:sw?sw.checked:null});
                });
                return out;
            }""",
            filtro_email,
        )

    def respostas_questionario(self, filtro_email: str = None) -> list:
        """Linhas da aba 'Respostas de questionário' (desempenho/resultado real por
        questionário/tentativa). [{email, texto}]."""
        return self.page.evaluate(
            r"""(filtro)=>{
                const out=[];
                document.querySelectorAll('tr').forEach(r=>{
                    const t=(r.innerText||'').replace(/\s+/g,' ').trim();
                    if(!/@/.test(t)) return;
                    const email=(t.match(/[\w.\-]+@[\w.\-]+/)||[''])[0];
                    if(filtro && email!==filtro) return;
                    out.push({email, texto:t});
                });
                return out;
            }""",
            filtro_email,
        )

    # ---- kebab / menu Chakra ----
    def abrir_kebab(self, item_id: str) -> None:
        row = self.page.locator(f'tr[data-item-id="{item_id}"]')
        row.locator("td", has_text="more_vert").last.click(timeout=5000, force=True)
        self.page.wait_for_timeout(1200)

    def itens_menu_visivel(self) -> list:
        return self.page.evaluate(
            "()=>{const ms=" + _JS_MENU_VISIVEL + ";const m=ms[ms.length-1];return m?"
            "Array.from(m.querySelectorAll('[role=menuitem]')).map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()):[];}"
        )

    def clicar_menuitem(self, texto: str) -> bool:
        rid = self.page.evaluate(
            "(pal)=>{const ms=" + _JS_MENU_VISIVEL + ";const m=ms[ms.length-1];if(!m)return '';"
            "const it=Array.from(m.querySelectorAll('[role=menuitem]'))"
            ".find(e=>new RegExp(pal,'i').test(e.innerText||''));return it?it.id:'';}",
            texto,
        )
        if not rid:
            return False
        try:
            self.page.locator(f'[id="{rid}"]').click(timeout=4000)
            return True
        except Exception:
            return False

    def item_reinscricao(self) -> dict:
        """{achou, texto, corIcone, id} do item 'Iniciar reinscrição' (ícone replay)."""
        return self.page.evaluate(
            "()=>{const ms=" + _JS_MENU_VISIVEL + ";const m=ms[ms.length-1];if(!m)return {achou:false};"
            "const items=Array.from(m.querySelectorAll('[role=menuitem]'));"
            "const el=items.find(it=>it.querySelector('[data-icon=\"replay\"]')||/reinscri/i.test(it.innerText||''));"
            "if(!el)return {achou:false};el.scrollIntoView({block:'center'});"
            "const ic=el.querySelector('[data-icon=\"replay\"]');"
            "return {achou:true,texto:(el.innerText||'').replace(/\\s+/g,' ').trim(),id:el.id,"
            "corIcone:ic?getComputedStyle(ic).color:null};}"
        )

    @staticmethod
    def reinscricao_bloqueada(cor_icone: str) -> bool:
        """True se o ícone está cinza (R≈G≈B) = bloqueado; azul = habilitado."""
        import re
        m = re.findall(r"\d+", cor_icone or "")
        return len(m) >= 3 and abs(int(m[0]) - int(m[1])) < 12 and abs(int(m[1]) - int(m[2])) < 12
