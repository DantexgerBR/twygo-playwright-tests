"""
Keyboard test v4: click kebab (Chakra foca Editar automaticamente),
ArrowDown 2x = Visualizar, Enter.
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
        kebab.click()
        page.wait_for_timeout(1500)

        # Verificar item focado inicial
        focused0 = page.evaluate(
            "() => { const el = document.activeElement; return { tag: el.tagName, id: el.id, text: (el.textContent||'').trim().slice(0,30) }; }"
        )
        print(f"   Focado apos click kebab: {focused0}")

        # 2 ArrowDown = Visualizar (ja que Chakra foca Editar=index0 ao abrir)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(200)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(300)

        focused2 = page.evaluate(
            "() => { const el = document.activeElement; const r = el.getBoundingClientRect(); return { tag: el.tagName, id: el.id, left: Math.round(r.left), text: (el.textContent||'').trim().slice(0,40) }; }"
        )
        print(f"   Focado apos 2x ArrowDown: {focused2}")
        snap(page, "kb4_01_focado")

        nav_urls = []
        page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)
        pages_antes = len(ctx.pages)

        page.keyboard.press("Enter")
        page.wait_for_timeout(6000)
        pages_depois = len(ctx.pages)

        print(f"   URL: {page.url}")
        print(f"   Paginas: {pages_antes} -> {pages_depois}")
        print(f"   Navegacoes: {nav_urls}")
        snap(page, "kb4_02_pos_enter", full=True)

        if pages_depois > pages_antes:
            nova = ctx.pages[-1]
            nova.wait_for_load_state("domcontentloaded", timeout=15000)
            nova.wait_for_timeout(3000)
            snap(nova, "kb4_03_nova_aba", full=True)
            print(f"   Nova aba URL: {nova.url}")
            print(f"   Body: {nova.inner_text('body')[:500]}")
        else:
            body = page.inner_text("body")
            if "Visualizar registro" in body:
                print("   ACHOU: feature funciona na mesma aba!")
                snap(page, "kb4_04_visualizar_form", full=True)
            elif "Meu Hist" in body and page.locator("button.chakra-menu__menu-button").count() > 0:
                print("   Menu fechou mas voltou para lista - nenhum efeito de visualizacao")
            else:
                print(f"   Resultado incerto. Body[:200]: {body[:200]}")

        browser.close()
        print("\n=== FIM KB4 ===")


if __name__ == "__main__":
    main()
