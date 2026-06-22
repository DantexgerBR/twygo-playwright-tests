"""tc3_slowmo_headless.py — Testa com slow_mo=500 em headless para ver se modal abre."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
from playwright.sync_api import sync_playwright

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
TC3_EMAIL = "qa11tc342588@twygotest.com"
TC3_NOVA_SENHA = "twygoqa2026"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)

BLOQUEIO = None
PASSOU = []
FALHOU = []


def log(msg):
    print(msg, flush=True)


def check(cond, label):
    if cond:
        PASSOU.append(label)
        log(f"  OK  {label}")
    else:
        FALHOU.append(label)
        log(f"  FAIL {label}")
    return cond


def run(slow_mo_val=500, headless_val=True):
    global BLOQUEIO

    log(f"\nheadless={headless_val} slow_mo={slow_mo_val}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless_val, slow_mo=slow_mo_val)
        ctx = browser.new_context(viewport={"width": 1500, "height": 950}, locale="pt-BR")
        page = ctx.new_page()
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.fill("#user_email", "dante.tavares@twygo.com")
            page.fill("#user_password", "123456")
            page.click("#user_submit")
            page.wait_for_timeout(3000)
            page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            busca = page.locator("input[placeholder='Pesquise aqui']").first
            if busca.is_visible(timeout=2000):
                busca.fill("qa11tc342588")
                page.wait_for_timeout(1500)

            row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
            kebab = row.locator("button").last
            kebab.click(force=True)
            page.wait_for_timeout(1500)

            # Clica no menuitem Alterar senha
            ok = tw.click_menuitem(page, "Alterar senha")
            log(f"  click_menuitem: {ok}")
            page.wait_for_timeout(3000)

            campos = page.locator("input[type='password']").count()
            menus = page.evaluate(
                "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
            )
            log(f"  Campos password: {campos}, menus: {menus}")
            tw.snap(page, EVID, f"tc3_sm{slow_mo_val}_{'hl' if headless_val else 'vis'}")
            return campos > 0
        finally:
            ctx.close()
            browser.close()


def main():
    log("=" * 60)
    log("tc3_slowmo_headless.py")
    log("=" * 60)

    # Testa combinacoes
    for hl, sm in [(True, 500), (True, 0), (False, 0)]:
        opened = run(slow_mo_val=sm, headless_val=hl)
        log(f"headless={hl} slow_mo={sm}: modal_abriu={opened}")
        if opened:
            log("SUCESSO! Modal abriu")
            break


if __name__ == "__main__":
    main()
