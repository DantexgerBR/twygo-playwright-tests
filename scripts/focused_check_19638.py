"""Foco: revelar o item 'Iniciar reinscricao' (ultimo do kebab) de um participante
ELEGIVEL (Edu, 100%+aprovado) e um NAO-ELEGIVEL (Danilo, 92% pendente), via tecla
ArrowUp (foca o ultimo item do chakra-menu => scrolla pra view), e capturar
estado (habilitado/bloqueado) + tooltip no hover.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://eduapi.stage.twygoead.com"
ORG_ID = "36912"
EMAIL, SENHA = "eduardo.schmidt@twygo.com", "123456"
CID = "798476"
PASTA = ROOT / "evidencias" / "19638_botao_reinscricao"


def snap(page, nome):
    p = PASTA / f"{nome}.png"; page.screenshot(path=str(p)); print(f"   [snap] {p.name}"); return p


def dispensar_nps(page):
    for sel in ["button:has-text('Pergunte depois')", "[aria-label='Close']", ".chakra-modal__close-btn"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(): b.click(timeout=2000); page.wait_for_timeout(500)
        except Exception: pass


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=350)
    context = browser.new_context(viewport={"width": 1500, "height": 950}, locale="pt-BR")
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
    alvos = {0: "edu-ELEGIVEL", 3: "gabriel-NAOELEG", 5: "danilo-NAOELEG"}

    for idx, tag in alvos.items():
        print(f"\n=== participante idx={idx} ({tag}) ===")
        kebabs.nth(idx).click(force=True)
        page.wait_for_timeout(1200)
        # ArrowUp: foca o ULTIMO item do menu (Iniciar reinscricao) e scrolla
        page.keyboard.press("ArrowUp")
        page.wait_for_timeout(1000)
        snap(page, f"04-{tag}-menu-fim")

        # ler o item de reinscricao: estado computado (cor/opacity/pointer) + texto
        estado = page.evaluate(
            r"""() => {
                const items = Array.from(document.querySelectorAll('[role=menu] [role=menuitem]'))
                    .filter(m => m.offsetParent !== null);
                const el = items.find(it => {
                    const di = it.querySelector('[data-icon]');
                    return (di && di.getAttribute('data-icon')==='replay') || /reinscri/i.test(it.innerText||'');
                });
                if (!el) return {achou:false};
                const cs = getComputedStyle(el);
                return {
                    achou:true,
                    texto: (el.innerText||'').replace(/\s+/g,' ').trim(),
                    ariaDisabled: el.getAttribute('aria-disabled'),
                    disabled: el.disabled === true,
                    color: cs.color, opacity: cs.opacity, pointerEvents: cs.pointerEvents,
                    cursor: cs.cursor, classe: el.className,
                };
            }""")
        print(f"   item: {estado}")

        # hover no item p/ tooltip (force, ignora pointer-events)
        try:
            item = page.locator("[role=menu] [role=menuitem]").filter(
                has=page.locator("[data-icon='replay']")).last
            item.hover(force=True, timeout=3000)
            page.wait_for_timeout(1600)
        except Exception as e:
            print(f"   hover err: {repr(e)[:80]}")
        tip = page.evaluate(
            """() => Array.from(document.querySelectorAll('[role=tooltip], .chakra-tooltip'))
                .filter(e => e.offsetParent !== null).map(e => (e.innerText||'').trim()).filter(Boolean)""")
        print(f"   tooltip: {tip}")
        snap(page, f"04-{tag}-hover-tooltip")
        page.keyboard.press("Escape"); page.wait_for_timeout(600)

    page.wait_for_timeout(1000)
    context.close(); browser.close()
