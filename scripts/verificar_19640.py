"""19640 — verificacao final: (1) valores REAIS por coluna (sem regex) das inscricoes
do agents.claude pos-reinscricao; (2) abrir Historico de aprendizagem e de certificado
da inscricao anterior (44275175) pra ver se o historico preserva 100%/110.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
import _twygo as tw
_c = tw.cfg("RECERT")
BASE_URL, EMAIL, SENHA = _c["base_url"], _c["email"], _c["senha"]
TRILHA_ID = "807406"
PREV_ID = "44275175"
PASTA = ROOT / "evidencias" / "19640_pontuacao_reinscricao"


def snap(page, nome, full=False):
    p = PASTA / f"{nome}.png"; page.screenshot(path=str(p), full_page=full); print(f"   [snap] {p.name}"); return p


def dispensar_nps(page):
    for sel in ["button:has-text('Pergunte depois')", ".chakra-modal__close-btn", "[aria-label='Close']"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(): b.click(timeout=1500); page.wait_for_timeout(500)
        except Exception: pass


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=350)
    context = browser.new_context(viewport={"width": 1500, "height": 950}, locale="pt-BR")
    page = context.new_page()
    page.on("dialog", lambda d: (print(f"   [DIALOG] {d.message!r}"), d.accept()))
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded"); page.fill("#user_email", EMAIL)
    page.fill("#user_password", SENHA); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    page.goto(f"{BASE_URL}/e/{TRILHA_ID}/learning", wait_until="domcontentloaded", timeout=30000)
    try: page.wait_for_load_state("networkidle", timeout=15000)
    except Exception: pass
    page.wait_for_timeout(4000); dispensar_nps(page)

    # cabecalho de colunas + valores por TD (sem regex) das linhas do agents.claude
    dados = page.evaluate(
        r"""() => {
            const heads = Array.from(document.querySelectorAll('thead th, thead td')).map(h => (h.innerText||'').trim());
            const out = [];
            document.querySelectorAll('tr[data-item-id]').forEach(r => {
                if (!/agents\.claude@claude\.com/.test(r.innerText||'')) return;
                const tds = Array.from(r.querySelectorAll('td')).map(td => (td.innerText||'').replace(/\s+/g,' ').trim());
                // estado da aprovacao (switch)
                const sw = r.querySelector('input[type=checkbox]');
                out.push({itemId: r.getAttribute('data-item-id'), tds, aprovado: sw?sw.checked:null});
            });
            return {heads, out};
        }""")
    print(f"[colunas] {dados['heads']}")
    print("[agents.claude por TD (sem regex)]:")
    for r in dados["out"]:
        print(f"   itemId={r['itemId']} aprovado={r['aprovado']}")
        print(f"      tds={r['tds']}")
    (PASTA / "_verificacao_colunas.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    # screenshot recortado das linhas do agents.claude (zoom): rolar topo e snap
    snap(page, "17-DEPOIS-admin-full", full=True)

    # ---- abrir Historico da inscricao anterior (PREV_ID) ----
    def abrir_kebab(item_id):
        row = page.locator(f'tr[data-item-id="{item_id}"]')
        if row.count() == 0: return "no-row"
        row.locator("td", has_text="more_vert").last.click(timeout=5000, force=True)
        return "ok"

    def click_hist(palavra):
        # menu visivel -> menuitem que contem 'palavra'; clica por id exato
        rid = page.evaluate(
            r"""(pal) => {
                const menus=Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;});
                const m=menus[menus.length-1]; if(!m) return '';
                const it=Array.from(m.querySelectorAll('[role=menuitem]')).find(e=>new RegExp(pal,'i').test(e.innerText||''));
                return it? it.id : '';
            }""", palavra)
        if not rid: return False
        try:
            page.locator(f'[id="{rid}"]').click(timeout=4000); return True
        except Exception:
            return False

    for palavra, slug in [("Histórico de aprendizagem", "hist-aprendizagem"), ("Histórico de certificado", "hist-certificado")]:
        print(f"\n=== {palavra} (inscricao {PREV_ID}) ===")
        page.keyboard.press("Escape"); page.wait_for_timeout(600)
        print(f"   kebab: {abrir_kebab(PREV_ID)}")
        page.wait_for_timeout(1200)
        ok = click_hist(palavra.split()[-1])  # 'aprendizagem'/'certificado'
        print(f"   clicou hist: {ok}  url={page.url}")
        page.wait_for_timeout(2800)
        txt = page.evaluate(
            r"""() => {
                const ov=Array.from(document.querySelectorAll('.chakra-modal__content,[role=dialog],[class*="drawer"],main')).filter(e=>e.offsetParent!==null);
                const el=ov[ov.length-1];
                return el? (el.innerText||'').replace(/\n{2,}/g,'\n').slice(0,1200):'';
            }""")
        print(f"   conteudo:\n{txt[:1000]}")
        snap(page, f"18-{slug}-{PREV_ID}")
        for sel in ["[aria-label='Close']", ".chakra-modal__close-btn", "button:has-text('Fechar')", "button:has-text('Voltar')"]:
            try:
                b = page.locator(sel).first
                if b.count() and b.is_visible(): b.click(timeout=1500); page.wait_for_timeout(600); break
            except Exception: pass
        page.keyboard.press("Escape"); page.wait_for_timeout(600)

    page.wait_for_timeout(1200)
    context.close(); browser.close()
