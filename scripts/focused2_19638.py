"""Prova objetiva do par de contraste: cor do SPAN/TEXTO interno do item
'Iniciar reinscricao' (o que fica cinza quando bloqueado) + screenshot do proprio
menuitem (auto-scroll) + tooltip confiavel. Edu (elegivel) vs Gabriel/Danilo (nao).
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
import _twygo as tw
_c = tw.cfg("EDUAPI")
BASE_URL, EMAIL, SENHA = _c["base_url"], _c["email"], _c["senha"]
CID = "798476"
PASTA = ROOT / "evidencias" / "19638_botao_reinscricao"


def dispensar_nps(page):
    for sel in ["button:has-text('Pergunte depois')", "[aria-label='Close']", ".chakra-modal__close-btn"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(): b.click(timeout=2000); page.wait_for_timeout(400)
        except Exception: pass


def estado_item_reinscricao(page):
    """Le cor computada do icone e do texto interno do item de reinscricao."""
    return page.evaluate(
        r"""() => {
            const items = Array.from(document.querySelectorAll('[role=menu] [role=menuitem]'))
                .filter(m => m.offsetParent !== null);
            const el = items.find(it => {
                const di = it.querySelector('[data-icon]');
                return (di && di.getAttribute('data-icon')==='replay') || /reinscri/i.test(it.innerText||'');
            });
            if (!el) return {achou:false};
            const icon = el.querySelector('[data-icon="replay"]');
            // o texto label: ultimo elemento com texto que nao seja o icone
            let label = null;
            el.querySelectorAll('p, span').forEach(s => {
                const t=(s.textContent||'').trim();
                if (/reinscri/i.test(t)) label = s;
            });
            const cc = e => e ? getComputedStyle(e).color : null;
            const op = e => e ? getComputedStyle(e).opacity : null;
            return {
                achou:true,
                texto:(el.innerText||'').replace(/\s+/g,' ').trim(),
                corMenuitem: getComputedStyle(el).color,
                corIcone: cc(icon), opacIcone: op(icon),
                corLabel: cc(label), opacLabel: op(label),
                labelTxt: label ? (label.textContent||'').trim() : null,
            };
        }""")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    context = browser.new_context(viewport={"width": 1500, "height": 1600}, locale="pt-BR")
    page = context.new_page()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded"); page.fill("#user_email", EMAIL)
    page.fill("#user_password", SENHA); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    page.goto(f"{BASE_URL}/e/{CID}/learning", wait_until="domcontentloaded", timeout=30000)
    try: page.wait_for_load_state("networkidle", timeout=15000)
    except Exception: pass
    page.wait_for_timeout(4000); dispensar_nps(page)

    kebabs = page.locator("table button:has-text('more_vert'), tbody button:has-text('more_vert')")
    alvos = {0: "edu-ELEGIVEL", 5: "danilo-NAOELEG"}

    for idx, tag in alvos.items():
        print(f"\n=== idx={idx} ({tag}) ===")
        kebabs.nth(idx).click(force=True)
        page.wait_for_timeout(1200)
        item = page.locator("[role=menu] [role=menuitem]").filter(
            has=page.locator("[data-icon='replay']")).last
        # screenshot do PROPRIO item (auto-scroll into view)
        try:
            item.scroll_into_view_if_needed(timeout=4000)
            page.wait_for_timeout(500)
            item.screenshot(path=str(PASTA / f"05-{tag}-item.png"))
            print(f"   [snap-item] 05-{tag}-item.png")
        except Exception as e:
            print(f"   item.screenshot err: {repr(e)[:90]}")
        est = estado_item_reinscricao(page)
        print(f"   estado: {est}")
        # hover confiavel (item ja scrollado)
        try:
            item.hover(force=True, timeout=3000); page.wait_for_timeout(1500)
        except Exception as e:
            print(f"   hover err: {repr(e)[:80]}")
        tip = page.evaluate(
            """() => Array.from(document.querySelectorAll('[role=tooltip], .chakra-tooltip'))
                .filter(e => e.offsetParent !== null).map(e => (e.innerText||'').trim()).filter(Boolean)""")
        print(f"   tooltip: {tip}")
        page.screenshot(path=str(PASTA / f"05-{tag}-full.png"))
        page.keyboard.press("Escape"); page.wait_for_timeout(600)

    page.wait_for_timeout(800)
    context.close(); browser.close()
