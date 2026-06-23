"""
Teste definitivo: navegar com ArrowDown ate Visualizar e pressionar Enter.
Conta posicao exata do item no menu para garantir foco correto.
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
        page.wait_for_timeout(3000)

        # Abrir kebab
        row = page.locator("tbody tr").first
        kebab = row.locator("button.chakra-menu__menu-button").first
        kebab.click()
        page.wait_for_timeout(1500)

        # Descubrir o indice real de "Visualizar" no menu
        menu_order = page.evaluate("""() => {
            const list = document.querySelector('ul[class*="menu__menu-list"]');
            if (!list) return [];
            const r = list.getBoundingClientRect();
            if (r.left < 100) return [];
            const btns = Array.from(list.querySelectorAll('button[role="menuitem"]'));
            return btns.map((btn, i) => ({ index: i, text: btn.innerText.trim().replace(/\\n/g,' ') }));
        }""")
        print(f"   Ordem do menu: {menu_order}")

        vis_index = next((item['index'] for item in menu_order if 'isual' in item['text']), None)
        print(f"   Visualizar index: {vis_index}")

        if vis_index is not None:
            # ArrowDown vis_index vezes (o menu inicia sem foco, 1o ArrowDown = item 0)
            for i in range(vis_index + 1):
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(200)

            snap(page, "key_01_visualizar_focado")

            # Verificar qual item esta focado
            focused_text = page.evaluate("""() => {
                const el = document.activeElement;
                return { tag: el.tagName, role: el.getAttribute('role'), text: el.innerText ? el.innerText.trim() : '' };
            }""")
            print(f"   Elemento focado: {focused_text}")

            nav_urls = []
            page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)
            pages_antes = len(ctx.pages)

            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)
            pages_depois = len(ctx.pages)

            print(f"   URL apos Enter em Visualizar: {page.url}")
            print(f"   Paginas: {pages_antes} -> {pages_depois}")
            print(f"   Navegacoes: {nav_urls}")
            snap(page, "key_02_pos_enter", full=True)

            if pages_depois > pages_antes:
                nova = ctx.pages[-1]
                nova.wait_for_load_state("domcontentloaded", timeout=15000)
                nova.wait_for_timeout(3000)
                snap(nova, "key_03_nova_aba", full=True)
                print(f"   Nova aba URL: {nova.url}")
                print(f"   Body nova aba: {nova.inner_text('body')[:500]}")
                nova.close()
            else:
                body = page.inner_text("body")
                if "Visualizar registro" in body:
                    print("   ACHOU 'Visualizar registro' - BUG AUSENTE, FEATURE FUNCIONA!")
                else:
                    print(f"   BUG CONFIRMADO: nenhum efeito ao pressionar Enter em 'Visualizar'")
                    print(f"   Body: {body[:300]}")

        browser.close()
        print("\n=== FIM KEYBOARD TEST ===")


if __name__ == "__main__":
    main()
