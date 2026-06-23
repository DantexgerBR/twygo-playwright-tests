"""
Teste final QA 1.8:
1. Navegar diretamente para /records/ID para ver se existe pagina de visualizacao
2. Usar keyboard Enter no elemento focalizado para comparar com click
3. Inspecionar outerHTML completo do button Visualizar vs Editar
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
RECORD_ID = "44279951"  # aluno qa11tc342588

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

        # === TESTE 1: Navegar direto para /records/ID/view ou /records/ID ===
        print("\n=== TESTE 1: Navegar direto para URL de visualizacao ===")
        for route in [f"/o/{ORG_ID}/records/{RECORD_ID}", f"/o/{ORG_ID}/records/{RECORD_ID}/view", f"/o/{ORG_ID}/records/{RECORD_ID}/show"]:
            page.goto(f"{BASE_URL}{route}", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)
            url = page.url
            title = page.title()
            body_short = page.inner_text("body")[:200].replace("\n", " ")
            print(f"   Route {route}: url={url} body='{body_short}'")

        snap(page, "final_01_direct_nav", full=True)

        # === TESTE 2: Abrir menu e usar Tab/Enter para focar e ativar Visualizar ===
        print("\n=== TESTE 2: Tab/Enter no item Visualizar ===")
        page.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                  wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)

        row = page.locator("tbody tr").first
        kebab = row.locator("button.chakra-menu__menu-button").first
        kebab.click()
        page.wait_for_timeout(1200)
        snap(page, "final_02_menu_aberto")

        # HTML completo do button Visualizar vs Editar
        html_info = page.evaluate("""() => {
            const list = document.querySelector('ul[class*="menu__menu-list"]');
            if (!list) return {error: 'no list'};
            const r = list.getBoundingClientRect();
            if (r.left < 100) return {error: 'list not visible', left: r.left};

            const btns = Array.from(list.querySelectorAll('button[role="menuitem"]'));
            return btns.map(btn => ({
                id: btn.id,
                text: btn.innerText.trim(),
                outerHTML: btn.outerHTML.slice(0, 500),
                hasReactFiber: Object.keys(btn).some(k => k.startsWith('__reactFiber') || k.startsWith('__reactProps')),
                reactPropsKeys: Object.keys(btn).filter(k => k.startsWith('__react')).slice(0,3),
                hasClickHandler: !!btn.onclick
            }));
        }""")

        print(f"   Buttons no menu ativo:")
        for item in html_info if isinstance(html_info, list) else []:
            print(f"\n   === {item['text']} ===")
            print(f"   id: {item['id']}")
            print(f"   hasReactFiber: {item['hasReactFiber']}")
            print(f"   reactPropsKeys: {item['reactPropsKeys']}")
            print(f"   hasClickHandler: {item['hasClickHandler']}")
            print(f"   outerHTML: {item['outerHTML'][:400]}")

        # Usar Tab para navegar ate Visualizar e Enter para ativar
        print("\n   Usando Tab/Enter para ativar Visualizar...")
        # O menu ja esta aberto — Tab move entre menuitems
        page.keyboard.press("ArrowDown")  # Editar
        page.keyboard.press("ArrowDown")  # Excluir
        page.keyboard.press("ArrowDown")  # Visualizar
        page.wait_for_timeout(500)
        snap(page, "final_03_tab_visualizar")

        nav_urls = []
        page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)
        pages_antes = len(ctx.pages)

        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)
        pages_depois = len(ctx.pages)

        print(f"   URL apos Enter: {page.url}")
        print(f"   Paginas: {pages_antes} -> {pages_depois}")
        print(f"   Navegacoes: {nav_urls}")
        snap(page, "final_04_pos_enter", full=True)

        if pages_depois > pages_antes:
            nova = ctx.pages[-1]
            nova.wait_for_load_state("domcontentloaded", timeout=15000)
            nova.wait_for_timeout(3000)
            snap(nova, "final_05_nova_aba", full=True)
            print(f"   Nova aba URL: {nova.url}")
            print(f"   Body: {nova.inner_text('body')[:400]}")
        else:
            body = page.inner_text("body")
            if "Visualizar registro" in body:
                print("   ACHOU 'Visualizar registro' na mesma aba!")
            else:
                print("   Sem mudanca detectada")

        browser.close()
        print("\n=== FIM FINAL ===")


if __name__ == "__main__":
    main()
