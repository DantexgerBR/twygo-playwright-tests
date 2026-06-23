"""
Teste keyboard simples: abrir menu, ArrowDown x3 = Visualizar, Enter.
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
        snap(page, "key2_00_lista")

        # Usar click no kebab via JS para garantir que o foco permanece no menu
        row = page.locator("tbody tr").first
        kebab = row.locator("button.chakra-menu__menu-button").first
        kebab.focus()
        kebab.press("Enter")  # Abrir o menu com Enter (mais confiavel que click)
        page.wait_for_timeout(2000)
        snap(page, "key2_01_menu_aberto")

        # Verificar se menu esta aberto
        menu_info = page.evaluate(
            "() => {"
            "  const uls = Array.from(document.querySelectorAll('ul'));"
            "  const openUl = uls.find(ul => { const r = ul.getBoundingClientRect(); return r.width > 0 && r.left > 100 && r.height > 0; });"
            "  if (!openUl) return { found: false };"
            "  const btns = Array.from(openUl.querySelectorAll('button[role=\"menuitem\"]'));"
            "  return { found: true, ulLeft: Math.round(openUl.getBoundingClientRect().left), items: btns.map((b, i) => ({ i: i, text: (b.textContent || '').trim().slice(0, 40) })) };"
            "}"
        )
        print(f"   Menu info: {menu_info}")

        if menu_info.get('found') and menu_info.get('items'):
            items = menu_info['items']
            vis_idx = next((item['i'] for item in items if 'isual' in item['text']), None)
            print(f"   Items: {items}")
            print(f"   Visualizar index: {vis_idx}")

            if vis_idx is not None:
                # Navegar ate Visualizar com ArrowDown
                for i in range(vis_idx + 1):
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(300)

                # Confirmar foco
                focused = page.evaluate("() => ({ tag: document.activeElement.tagName, text: document.activeElement.innerText ? document.activeElement.innerText.trim() : '', id: document.activeElement.id })")
                print(f"   Elemento focado: {focused}")
                snap(page, "key2_02_focado")

                nav_urls = []
                page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)
                pages_antes = len(ctx.pages)

                page.keyboard.press("Enter")
                page.wait_for_timeout(5000)
                pages_depois = len(ctx.pages)

                print(f"   URL: {page.url}")
                print(f"   Paginas: {pages_antes} -> {pages_depois}")
                print(f"   Navegacoes: {nav_urls}")
                snap(page, "key2_03_pos_enter", full=True)

                if pages_depois > pages_antes:
                    nova = ctx.pages[-1]
                    nova.wait_for_load_state("domcontentloaded", timeout=15000)
                    nova.wait_for_timeout(3000)
                    snap(nova, "key2_04_nova_aba", full=True)
                    print(f"   Nova aba URL: {nova.url}")
                    print(f"   Body: {nova.inner_text('body')[:400]}")
                    nova.close()
                else:
                    body = page.inner_text("body")
                    if "Visualizar registro" in body:
                        print("   ACHOU: feature funciona!")
                    else:
                        print("   BUG CONFIRMADO: Enter em Visualizar nao tem efeito")

        browser.close()
        print("\n=== FIM ===")


if __name__ == "__main__":
    main()
