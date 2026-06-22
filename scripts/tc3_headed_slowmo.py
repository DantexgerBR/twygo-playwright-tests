"""tc3_headed_slowmo.py — Tenta abrir modal Alterar Senha em modo headed com slow_mo alto.

Objetivo: confirmar se o modal abre em tempo real (slow_mo=2000) e capturar
o screenshot do modal aberto para entender por que nao aparece em headless.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
from playwright.sync_api import sync_playwright

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def main():
    log("=" * 60)
    log("tc3_headed_slowmo.py — Modal Alterar Senha headed+slowmo")
    log("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1500)
        ctx = browser.new_context(viewport={"width": 1500, "height": 950}, locale="pt-BR")
        page = ctx.new_page()

        # Intercepta requests do Twygo apos o clique em Alterar Senha
        req_after_click = []

        def on_request(req):
            if "registrosf2" in req.url:
                req_after_click.append(f"{req.method} {req.url[:120]}")

        page.on("request", on_request)

        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.fill("#user_email", "dante.tavares@twygo.com")
            page.fill("#user_password", "123456")
            page.click("#user_submit")
            page.wait_for_timeout(3000)
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
                wait_until="domcontentloaded"
            )
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            busca = page.locator("input[placeholder='Pesquise aqui']").first
            if busca.is_visible(timeout=2000):
                busca.fill("qa11tc342588")
                page.wait_for_timeout(1500)

            row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
            kebab = row.locator("button").last
            kebab.click(force=True)
            page.wait_for_timeout(1500)
            tw.snap(page, EVID, "tc3_slowmo_kebab_aberto")

            # Limpa requests antes do clique critico
            req_after_click.clear()

            # Clica em Alterar Senha usando click_menuitem
            ok = tw.click_menuitem(page, "Alterar senha")
            log(f"click_menuitem: {ok}")

            # Aguarda bem mais que o normal
            page.wait_for_timeout(5000)
            tw.snap(page, EVID, "tc3_slowmo_apos_alterar_senha_5s")

            # Verifica requests e DOM
            log(f"Requests Twygo apos clique: {req_after_click}")

            modal_check = page.evaluate("""() => {
                // Qualquer elemento novo com input visivel
                const inputs = Array.from(document.querySelectorAll('input')).filter(i => {
                    const s = getComputedStyle(i);
                    return s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity) > 0.5;
                });
                const modals = Array.from(document.querySelectorAll('[class*="chakra-modal"], [aria-modal]')).filter(el => {
                    const s = getComputedStyle(el);
                    return s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity) > 0.5;
                });
                return {
                    inputs_visiveis: inputs.map(i => ({type: i.type, id: i.id, ph: i.placeholder})),
                    modals_visiveis: modals.map(m => ({tag: m.tagName, id: m.id, cls: m.className.slice(0,60)}))
                };
            }""")
            log(f"DOM apos 5s: inputs={modal_check['inputs_visiveis']}")
            log(f"  modals={modal_check['modals_visiveis']}")

            # Se ainda sem modal, tenta inspecionar visualmente apos mais tempo
            if not modal_check["modals_visiveis"]:
                log("Nenhum modal visivel apos 5s. Tentando aguardar 10s mais...")
                page.wait_for_timeout(10000)
                tw.snap(page, EVID, "tc3_slowmo_apos_15s")

        finally:
            ctx.close()
            browser.close()

    log("=" * 60)
    log("FIM")
    log("=" * 60)


if __name__ == "__main__":
    main()
