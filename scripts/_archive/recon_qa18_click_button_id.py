"""
Click direto no button[role="menuitem"] do Visualizar usando locator preciso.
Compara com Editar e verifica se React handler esta conectado.
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

        # === TESTE 1: Clicar no button de Visualizar via data-test-id interno ===
        print("\n=== Clicando via data-test-id='records-list-view-action' ===")
        row = page.locator("tbody tr").first
        kebab = row.locator("button.chakra-menu__menu-button").first
        kebab.click()
        page.wait_for_timeout(1200)
        snap(page, "click_btn_01_menu_aberto")

        # Localizar o button pai do div com data-test-id
        vis_btn = page.locator("[data-test-id='records-list-view-action']")
        cnt = vis_btn.count()
        print(f"   data-test-id view-action count: {cnt}")

        if cnt > 0:
            info = vis_btn.first.evaluate("""el => {
                const btn = el.closest('button[role="menuitem"]');
                return {
                    divFound: !!el,
                    btnFound: !!btn,
                    btnId: btn ? btn.id : null,
                    btnTabindex: btn ? btn.tabIndex : null,
                    btnDisabled: btn ? btn.disabled : null,
                    divId: el.id
                };
            }""")
            print(f"   info: {info}")

            # Clicar no button pai
            vis_button = page.locator("[data-test-id='records-list-view-action']").locator("xpath=ancestor::button[@role='menuitem']")
            cnt_btn = vis_button.count()
            print(f"   button ancestor count: {cnt_btn}")

            # Click direto no button
            nav_urls = []
            page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)
            pages_antes = len(ctx.pages)

            if cnt_btn > 0:
                vis_button.first.click(timeout=5000)
            else:
                # Fallback: clicar no div internamente
                vis_btn.first.click(timeout=5000)

            page.wait_for_timeout(4000)
            print(f"   URL: {page.url}")
            print(f"   Paginas: {pages_antes} -> {len(ctx.pages)}")
            print(f"   Navegacoes: {nav_urls}")
            snap(page, "click_btn_02_pos_click", full=True)

            if len(ctx.pages) > pages_antes:
                nova = ctx.pages[-1]
                nova.wait_for_load_state("domcontentloaded", timeout=15000)
                nova.wait_for_timeout(2000)
                snap(nova, "click_btn_03_nova_aba", full=True)
                print(f"   Nova aba URL: {nova.url}")

        browser.close()

        # === ADMIN: mesma busca por data-test-id ===
        print("\n=== ADMIN: via data-test-id ===")
        c_admin = {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": "dante.tavares@twygo.com", "senha": "123456"}
        browser2, ctx2, page2 = tw.nova_pagina(p)
        tw.login(page2, c_admin, admin=True)
        page2.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                   wait_until="domcontentloaded", timeout=25000)
        page2.wait_for_timeout(5000)

        rows2 = page2.locator("tbody tr")
        n2 = rows2.count()
        print(f"   Linhas: {n2}")

        if n2 >= 3:
            row2 = rows2.nth(2)
            row2.hover()
            page2.wait_for_timeout(300)
            kebab2 = row2.locator("button.chakra-menu__menu-button").first
            kebab2.click()
            page2.wait_for_timeout(1200)
            snap(page2, "click_btn_admin_01_menu_aberto")

            vis2 = page2.locator("[data-test-id='records-list-view-action']")
            cnt2 = vis2.count()
            print(f"   Admin view-action count: {cnt2}")

            # Filtrar por posicao (left > 500)
            if cnt2 > 1:
                # Pode ter multiplos (um por linha) — pegar o que esta na viewport
                vis_visible = page2.locator("[data-test-id='records-list-view-action']").filter(has=page2.locator(":visible"))
                cnt_vis = vis_visible.count()
                print(f"   Admin view-action :visible count: {cnt_vis}")

            nav2 = []
            page2.on("framenavigated", lambda f: nav2.append(f.url) if f == page2.main_frame else None)
            p2_antes = len(ctx2.pages)

            # Usar o botao ancestor
            vis2_btn = page2.locator("[data-test-id='records-list-view-action']").locator("xpath=ancestor::button[@role='menuitem']")
            cnt2_btn = vis2_btn.count()
            print(f"   Admin button ancestor count: {cnt2_btn}")

            if cnt2_btn > 0:
                # Achar o que esta visivelmente em posicao valida
                for i in range(cnt2_btn):
                    btn = vis2_btn.nth(i)
                    r = btn.evaluate("el => { const r = el.getBoundingClientRect(); return {left: Math.round(r.left), top: Math.round(r.top), width: Math.round(r.width), height: Math.round(r.height)}; }")
                    print(f"   Btn {i}: {r}")
                    if r['left'] > 500 and r['width'] > 0:
                        print(f"   Clicando btn {i} ({r['left']}, {r['top']})...")
                        btn.click(timeout=5000)
                        break

            page2.wait_for_timeout(5000)
            print(f"   URL: {page2.url}")
            print(f"   Paginas: {p2_antes} -> {len(ctx2.pages)}")
            print(f"   Navegacoes: {nav2}")
            snap(page2, "click_btn_admin_02_pos_click", full=True)

            if len(ctx2.pages) > p2_antes:
                nova2 = ctx2.pages[-1]
                nova2.wait_for_load_state("domcontentloaded", timeout=15000)
                nova2.wait_for_timeout(2000)
                snap(nova2, "click_btn_admin_03_nova_aba", full=True)
                print(f"   Nova aba URL: {nova2.url}")
                print(f"   Body: {nova2.inner_text('body')[:500]}")
            else:
                body2 = page2.inner_text("body")
                if "Visualizar registro" in body2:
                    print("   ACHOU 'Visualizar registro' na mesma aba!")
                else:
                    print("   Sem mudanca de tela apos click")

        ctx2.close()
        browser2.close()
        print("\n=== FIM ===")


if __name__ == "__main__":
    main()
