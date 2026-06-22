"""tc3_focus_enter.py — Foca o menuitem e pressiona Enter (sem click)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
TC3_EMAIL = "qa11tc342588@twygotest.com"
TC3_NOVA_SENHA = "twygoqa2026"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def main():
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            # Login admin
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.fill("#user_email", "dante.tavares@twygo.com")
            page.fill("#user_password", "123456")
            page.click("#user_submit")
            page.wait_for_timeout(3000)
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            # Navega para usuarios
            page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            # Pesquisa usuario
            busca = page.locator("input[placeholder='Pesquise aqui']").first
            if busca.is_visible(timeout=2000):
                busca.fill("qa11tc342588")
                page.wait_for_timeout(1500)

            # Abre kebab
            row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
            kebab = row.locator("button").last
            kebab.click(force=True)
            page.wait_for_timeout(1200)

            itens = tw.menu_visivel(page)
            log(f"Menu: {itens}")

            # Obtem ID do menuitem Alterar senha
            id_alterar = page.evaluate("""() => {
                const ms = Array.from(document.querySelectorAll('[role=menu]')).filter(m => {
                    const c = getComputedStyle(m);
                    return c.visibility === 'visible' && parseFloat(c.opacity) > 0.5;
                });
                const m = ms[ms.length - 1];
                if (!m) return '';
                const it = Array.from(m.querySelectorAll('[role=menuitem]')).find(
                    e => /alterar senha/i.test(e.innerText || '')
                );
                return it ? it.id : '';
            }""")
            log(f"ID do menuitem: {id_alterar!r}")

            if not id_alterar:
                log("BLOQUEADO: menuitem nao encontrado")
                return

            # Metodo 1: focus() no menuitem + Enter
            item = page.locator(f'[id="{id_alterar}"]')
            item.focus()
            page.wait_for_timeout(500)

            focused = page.evaluate("document.activeElement?.id")
            log(f"Elemento focado: {focused!r}")

            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)

            campos = page.locator("input[type='password']").count()
            menus = page.evaluate(
                "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
            )
            log(f"M1 focus+Enter: campos={campos} menus={menus}")
            tw.snap(page, EVID, "tc3_fe_m1")

            if campos > 0:
                log("MODAL ABRIU via focus+Enter!")
                page.locator("input[type='password']").first.fill(TC3_NOVA_SENHA)
                page.wait_for_timeout(500)
                import re
                page.locator("button").filter(has_text=re.compile(r"Salvar|Confirmar|Alterar|OK", re.I)).last.click()
                page.wait_for_timeout(2000)
                tw.snap(page, EVID, "fechamento_tc3_senha_definida")
                log("SENHA DEFINIDA")
                return

            # Metodo 2: hover + click (para mouseenter trigger)
            log("M2: hover + click...")
            if menus > 0:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)

            kebab.click(force=True)
            page.wait_for_timeout(1200)

            id_alterar2 = page.evaluate("""() => {
                const ms = Array.from(document.querySelectorAll('[role=menu]')).filter(m => {
                    const c = getComputedStyle(m);
                    return c.visibility === 'visible' && parseFloat(c.opacity) > 0.5;
                });
                const m = ms[ms.length - 1];
                if (!m) return '';
                const it = Array.from(m.querySelectorAll('[role=menuitem]')).find(
                    e => /alterar senha/i.test(e.innerText || '')
                );
                return it ? it.id : '';
            }""")

            item2 = page.locator(f'[id="{id_alterar2}"]')
            item2.hover()
            page.wait_for_timeout(300)
            item2.click(force=True)
            page.wait_for_timeout(2000)

            campos2 = page.locator("input[type='password']").count()
            log(f"M2 hover+click(force): campos={campos2}")
            tw.snap(page, EVID, "tc3_fe_m2")

            if campos2 > 0:
                log("MODAL ABRIU via hover+click!")
                page.locator("input[type='password']").first.fill(TC3_NOVA_SENHA)
                page.wait_for_timeout(500)
                import re
                page.locator("button").filter(has_text=re.compile(r"Salvar|Confirmar|Alterar|OK", re.I)).last.click()
                page.wait_for_timeout(2000)
                tw.snap(page, EVID, "fechamento_tc3_senha_definida")
                log("SENHA DEFINIDA")
                return

            # Metodo 3: mouse.move() + mouse.down() + mouse.up() raw
            log("M3: raw mouse events...")
            menus2 = page.evaluate(
                "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
            )
            if menus2 > 0:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)

            kebab.click(force=True)
            page.wait_for_timeout(1200)

            bbox = page.locator(f'[id="{id_alterar}"]').bounding_box()
            if bbox:
                cx = bbox["x"] + bbox["width"] / 2
                cy = bbox["y"] + bbox["height"] / 2
                log(f"BBox: {bbox} -> centro ({cx:.0f}, {cy:.0f})")
                page.mouse.move(cx, cy)
                page.wait_for_timeout(200)
                page.mouse.down(button="left")
                page.wait_for_timeout(100)
                page.mouse.up(button="left")
                page.wait_for_timeout(2000)

                campos3 = page.locator("input[type='password']").count()
                log(f"M3 raw mouse: campos={campos3}")
                tw.snap(page, EVID, "tc3_fe_m3")

                if campos3 > 0:
                    log("MODAL ABRIU via raw mouse!")
                    page.locator("input[type='password']").first.fill(TC3_NOVA_SENHA)
                    page.wait_for_timeout(500)
                    import re
                    page.locator("button").filter(has_text=re.compile(r"Salvar|Confirmar|Alterar|OK", re.I)).last.click()
                    page.wait_for_timeout(2000)
                    tw.snap(page, EVID, "fechamento_tc3_senha_definida")
                    log("SENHA DEFINIDA")
                    return
            else:
                log("M3: bbox nulo")

            log("TODOS OS METODOS FALHARAM - Modal nao abre")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
