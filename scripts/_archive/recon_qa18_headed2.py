"""
Recon QA 1.8 — Headed run 2: Clicar Visualizar SOMENTE em menuitem visivel.
Usa :visible selector para garantir o item certo.
Testa: Interno Emitido (admin), Externo Emitido (admin), Externo Pendente (aluno).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa18"
PASTA.mkdir(parents=True, exist_ok=True)

c_admin = {
    "base_url": BASE_URL, "org_id": ORG_ID,
    "email": "dante.tavares@twygo.com", "senha": "123456"
}

# IDs conhecidos via recon anterior
# Interno Emitido: #44279298 (julia@sophia.tech.com.br | PDI...)
# Externo Emitido: #44279907 (richard.sebold@twygo.com | QA11-F2-FGV-Financas)
# Externo Recusado: #44279851 (qa11tc342816@twygotest.com)


def snap(page, nome, full=False):
    fp = PASTA / f"{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")


def abrir_kebab_e_clicar_visualizar(page, ctx, nome_snap):
    """Abre kebab da linha hoverable e clica em Visualizar visivel. Retorna URL/nova_aba."""
    # Hover na primeira linha para revelar o kebab
    rows = page.locator("tbody tr")
    rows.first.hover()
    page.wait_for_timeout(800)

    # Clicar no kebab da linha (deve estar visivel apos hover)
    kebab = rows.first.locator("button.chakra-menu__menu-button").first
    if kebab.count() == 0:
        kebab = rows.first.locator("button:has-text('more_vert')").first
    if kebab.count() == 0:
        print("   Kebab nao encontrado na linha")
        return None

    kebab.click()
    page.wait_for_timeout(1200)
    snap(page, f"{nome_snap}_01_menu_aberto")

    # Clicar SOMENTE no menuitem visivel com texto Visualizar
    # Usar locator com :visible para garantir
    vis = page.locator("[class*='menuitem']:visible").filter(has_text="Visualizar").first
    if vis.count() == 0:
        # fallback: icon material
        vis = page.locator("[class*='menuitem']:visible").filter(has_text="visibility").first
    if vis.count() == 0:
        print("   Item Visualizar visivel nao encontrado")
        snap(page, f"{nome_snap}_01b_sem_vis")
        return None

    print(f"   Item Visualizar visivel: '{vis.inner_text()}'")
    # Checar se disabled
    is_dis = vis.evaluate("el => el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true' || !!el.getAttribute('data-disabled')")
    print(f"   Disabled: {is_dis}")

    nav_urls = []
    page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)
    pages_antes = len(ctx.pages)

    # Forcar click com force=True para bypassar possiveis sobreposicoes
    vis.click(force=True)
    page.wait_for_timeout(4000)

    pages_depois = len(ctx.pages)
    print(f"   Paginas: {pages_antes} -> {pages_depois}")
    print(f"   URL: {page.url}")
    print(f"   Navegacoes: {nav_urls}")
    snap(page, f"{nome_snap}_02_pos_click", full=True)

    if pages_depois > pages_antes:
        nova_aba = ctx.pages[-1]
        nova_aba.wait_for_load_state("domcontentloaded", timeout=15000)
        nova_aba.wait_for_timeout(3000)
        snap(nova_aba, f"{nome_snap}_03_nova_aba", full=True)
        print(f"   Nova aba URL: {nova_aba.url}")
        body = nova_aba.inner_text("body")[:800]
        print(f"   Nova aba body: {body}")
        return nova_aba.url

    return page.url


def main():
    with tw.sync_playwright() as p:
        # === ADMIN: Interno Emitido ===
        print("\n=== TESTE 1: Admin — filtrar Interno Emitido + Visualizar ===")
        browser, ctx, page = tw.nova_pagina(p)
        tw.login(page, c_admin, admin=True)

        # Filtrar por Interno + Emitido
        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/records?origin=internal&certificate_situation=emitted",
            wait_until="domcontentloaded", timeout=25000
        )
        page.wait_for_timeout(5000)
        snap(page, "tc2_01_admin_interno_emitido", full=True)

        trs = page.evaluate("() => document.querySelectorAll('tbody tr').length")
        print(f"   Linhas Interno Emitido: {trs}")

        if trs > 0:
            url_result = abrir_kebab_e_clicar_visualizar(page, ctx, "tc2")
            print(f"   Resultado TC2 (Interno Emitido): {url_result}")
        else:
            print("   Sem linhas para Interno Emitido no admin")

        ctx.close()
        browser.close()

        # === ADMIN: Externo Emitido ===
        print("\n=== TESTE 2: Admin — filtrar Externo Emitido + Visualizar ===")
        browser2, ctx2, page2 = tw.nova_pagina(p)
        tw.login(page2, c_admin, admin=True)

        page2.goto(
            f"{BASE_URL}/o/{ORG_ID}/records?origin=external&certificate_situation=emitted",
            wait_until="domcontentloaded", timeout=25000
        )
        page2.wait_for_timeout(5000)
        snap(page2, "tc5_01_admin_externo_emitido", full=True)

        trs2 = page2.evaluate("() => document.querySelectorAll('tbody tr').length")
        print(f"   Linhas Externo Emitido: {trs2}")

        if trs2 > 0:
            url_result2 = abrir_kebab_e_clicar_visualizar(page2, ctx2, "tc5")
            print(f"   Resultado TC5 (Externo Emitido): {url_result2}")
        else:
            print("   Sem linhas para Externo Emitido no admin")

        ctx2.close()
        browser2.close()

        # === ADMIN: Externo Recusado ===
        print("\n=== TESTE 3: Admin — filtrar Externo Recusado + Visualizar (banner?) ===")
        browser3, ctx3, page3 = tw.nova_pagina(p)
        tw.login(page3, c_admin, admin=True)

        page3.goto(
            f"{BASE_URL}/o/{ORG_ID}/records?origin=external&certificate_situation=rejected",
            wait_until="domcontentloaded", timeout=25000
        )
        page3.wait_for_timeout(5000)
        snap(page3, "tc6_01_admin_externo_recusado", full=True)

        trs3 = page3.evaluate("() => document.querySelectorAll('tbody tr').length")
        print(f"   Linhas Externo Recusado: {trs3}")

        if trs3 > 0:
            url_result3 = abrir_kebab_e_clicar_visualizar(page3, ctx3, "tc6")
            print(f"   Resultado TC6 (Externo Recusado): {url_result3}")
        else:
            print("   Sem linhas para Externo Recusado no admin")

        ctx3.close()
        browser3.close()

        # === ALUNO: Externo Pendente (unico registro disponivel) ===
        print("\n=== TESTE 4: Aluno qa11tc342588 — Externo Pendente + Visualizar ===")
        browser4, ctx4, page4 = tw.nova_pagina(p)
        page4.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page4.fill("#user_email", "qa11tc342588@twygotest.com")
        page4.fill("#user_password", "twygoqa2026")
        page4.click("#user_submit")
        try:
            page4.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page4.wait_for_timeout(2000)
        tw.dispensar_nps(page4)

        page4.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                   wait_until="domcontentloaded", timeout=25000)
        page4.wait_for_timeout(3000)
        snap(page4, "tc1_aluno_historico", full=True)

        rows4 = page4.locator("tbody tr")
        n4 = rows4.count()
        print(f"   Linhas aluno: {n4}")

        if n4 > 0:
            rows4.first.hover()
            page4.wait_for_timeout(800)
            kebab4 = rows4.first.locator("button.chakra-menu__menu-button").first
            if kebab4.count() == 0:
                kebab4 = page4.locator("button.chakra-menu__menu-button").first
            kebab4.click()
            page4.wait_for_timeout(1200)
            snap(page4, "tc1_aluno_menu_aberto")

            # Ver todos os menuitems visiveis
            vis_items = page4.locator("[class*='menuitem']:visible")
            cnt = vis_items.count()
            print(f"   Menuitems visiveis: {cnt}")
            for i in range(cnt):
                item = vis_items.nth(i)
                txt = item.inner_text()
                dis = item.evaluate("el => el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true' || !!el.getAttribute('data-disabled')")
                print(f"   [{i}] '{txt}' | disabled={dis}")

            # Fechar menu e registrar resultado TC1 (todos enabled para Externo Pendente?)
            page4.keyboard.press("Escape")
            page4.wait_for_timeout(500)

        ctx4.close()
        browser4.close()

        print("\n=== FIM HEADED RECON 2 ===")


if __name__ == "__main__":
    main()
