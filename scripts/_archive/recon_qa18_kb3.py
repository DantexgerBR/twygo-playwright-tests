"""
Keyboard test v3: click kebab, use ArrowDown from the document body.
O Chakra vai focar o primeiro item no ArrowDown.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa18"
PASTA.mkdir(parents=True, exist_ok=True)


def snap(page, nome, full=False):
    fp = PASTA / f"{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")


def main():
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page.fill("#user_email", "qa11tc342588@twygotest.com")
        page.fill("#user_password", "twygoqa2026")
        page.click("#user_submit")
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        tw.dispensar_nps(page)
        page.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                  wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(4000)

        row = page.locator("tbody tr").first
        kebab = row.locator("button.chakra-menu__menu-button").first

        # Click no kebab
        kebab.click()
        page.wait_for_timeout(1500)
        snap(page, "kb3_01_menu_aberto")

        # Verificar o que esta focado agora
        focused = page.evaluate(
            "() => { const el = document.activeElement; const r = el.getBoundingClientRect();"
            " return { tag: el.tagName, id: el.id, left: Math.round(r.left), text: (el.textContent||'').trim().slice(0,40) }; }"
        )
        print(f"   Focado apos click kebab: {focused}")

        # ArrowDown 3x para chegar em Visualizar (Editar=1, Excluir=2, Visualizar=3)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(300)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(300)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(300)

        focused2 = page.evaluate(
            "() => { const el = document.activeElement; const r = el.getBoundingClientRect();"
            " return { tag: el.tagName, id: el.id, left: Math.round(r.left), text: (el.textContent||'').trim().slice(0,40) }; }"
        )
        print(f"   Focado apos 3x ArrowDown: {focused2}")
        snap(page, "kb3_02_focado_visualizar")

        nav_urls = []
        page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)
        pages_antes = len(ctx.pages)

        page.keyboard.press("Enter")
        page.wait_for_timeout(6000)
        pages_depois = len(ctx.pages)

        print(f"   URL: {page.url}")
        print(f"   Paginas: {pages_antes} -> {pages_depois}")
        print(f"   Navegacoes: {nav_urls}")
        snap(page, "kb3_03_pos_enter", full=True)

        if pages_depois > pages_antes:
            nova = ctx.pages[-1]
            nova.wait_for_load_state("domcontentloaded", timeout=15000)
            nova.wait_for_timeout(3000)
            snap(nova, "kb3_04_nova_aba", full=True)
            print(f"   Nova aba URL: {nova.url}")
            print(f"   Body: {nova.inner_text('body')[:400]}")
        else:
            body = page.inner_text("body")
            if "Visualizar registro" in body:
                print("   ACHOU: feature funciona!")
            else:
                print(f"   BUG CONFIRMADO: Enter em Visualizar nao tem efeito. Body: {body[:200]}")

        browser.close()


if __name__ == "__main__":
    main()
