"""Prova visual final: revelar o item 'Iniciar reinscricao' rolando TODOS os
ancestrais scrollaveis, screenshot full-page, e hover por bounding-box.
Edu (elegivel) vs Danilo (nao-elegivel). Garante 1 menu aberto por vez (Escape+wait).
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://eduapi.stage.twygoead.com"
CID = "798476"
EMAIL, SENHA = "eduardo.schmidt@twygo.com", "123456"
PASTA = ROOT / "evidencias" / "19638_botao_reinscricao"


def dispensar_nps(page):
    for sel in ["button:has-text('Pergunte depois')", "[aria-label='Close']", ".chakra-modal__close-btn"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(): b.click(timeout=2000); page.wait_for_timeout(400)
        except Exception: pass


REVEAL_AND_READ = r"""() => {
    // chakra mantem TODOS os menus montados; o ABERTO tem visibility:visible + opacity~1
    const menus = Array.from(document.querySelectorAll('[role=menu]')).filter(m => {
        const cs = getComputedStyle(m);
        return cs.visibility === 'visible' && parseFloat(cs.opacity) > 0.5;
    });
    if (menus.length !== 1) return {menusAbertos: menus.length, achou:false};
    const m = menus[0];
    const items = Array.from(m.querySelectorAll('[role=menuitem]'));
    const el = items.find(it => it.querySelector('[data-icon="replay"]') || /reinscri/i.test(it.innerText||''));
    if (!el) return {achou:false};
    el.scrollIntoView({block:'center'});
    let p = el.parentElement;
    while (p) { if (p.scrollHeight > p.clientHeight + 2) p.scrollTop = p.scrollHeight; p = p.parentElement; }
    const icon = el.querySelector('[data-icon="replay"]');
    // texto label = elemento <p>/<span> que contem 'reinscri'
    let label = null;
    el.querySelectorAll('p,span').forEach(s => { if (/reinscri/i.test((s.textContent||'').trim())) label = s; });
    const cc = e => e ? getComputedStyle(e).color : null;
    const r = el.getBoundingClientRect();
    return {
        achou:true, menusAbertos:1,
        texto:(el.innerText||'').replace(/\s+/g,' ').trim(),
        corMenuitem: getComputedStyle(el).color,
        corIcone: cc(icon),
        corLabel: cc(label), labelTxt: label ? (label.textContent||'').trim() : null,
        cx: r.x + r.width/2, cy: r.y + r.height/2,
    };
}"""


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    context = browser.new_context(viewport={"width": 1500, "height": 1000}, locale="pt-BR")
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
        # garantir nenhum menu aberto antes
        page.keyboard.press("Escape"); page.wait_for_timeout(500)
        kebabs.nth(idx).click(force=True)
        page.wait_for_timeout(1500)
        est = page.evaluate(REVEAL_AND_READ)
        page.wait_for_timeout(800)
        print(f"   estado: {est}")
        page.screenshot(path=str(PASTA / f"06-{tag}-menu.png"))
        print(f"   [snap] 06-{tag}-menu.png")
        # hover por coordenada no centro do item p/ tooltip
        if est.get("achou") and est.get("cx"):
            page.mouse.move(est["cx"], est["cy"])
            page.wait_for_timeout(1600)
            tip = page.evaluate(
                """() => Array.from(document.querySelectorAll('[role=tooltip], .chakra-tooltip'))
                    .filter(e => e.offsetParent !== null).map(e => (e.innerText||'').trim()).filter(Boolean)""")
            print(f"   tooltip: {tip}")
            page.screenshot(path=str(PASTA / f"06-{tag}-tooltip.png"))

    page.wait_for_timeout(800)
    context.close(); browser.close()
