"""
Recon QA 1.8 — Headed run para validar:
1. Admin /records carrega tabela headed?
2. Click em Visualizar navega para onde?
3. Capturar URL pos-click com framenavigated listener.
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


def snap(page, nome, full=False):
    fp = PASTA / f"{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")


def main():
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)  # TW_HEADED=1 ativado via env

        # --- LOGIN ADMIN ---
        tw.login(page, c_admin, admin=True)
        print(f"   Admin logado. URL: {page.url}")

        # --- PARTE 1: Admin /records carrega headed? ---
        print("\n=== PARTE 1: Admin /records tabela ===")
        page.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                  wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(5000)
        snap(page, "headed_01_admin_records", full=True)

        # Polling ate 20s
        for i in range(20):
            trs = page.evaluate("() => document.querySelectorAll('tbody tr').length")
            cards = page.evaluate("() => document.querySelectorAll('[data-testid*=record], [class*=record-card], [class*=RecordCard]').length")
            spinner = page.evaluate("() => !!document.querySelector('[class*=spinner], [class*=loading], [aria-busy=true]')")
            print(f"   [{i:02d}s] tbody tr={trs} | cards={cards} | spinner={spinner}")
            if trs > 0 or cards > 0:
                print("   Tabela/cards carregaram!")
                break
            page.wait_for_timeout(1000)
        else:
            print("   Nao carregou em 20s (mesmo headed)")
            # Capturar DOM para inspecao
            dom_excerpt = page.evaluate("() => document.body.innerHTML.slice(0, 2000)")
            print(f"   DOM[0:2000]: {dom_excerpt}")

        snap(page, "headed_02_admin_records_apos_wait", full=True)

        # Ver quantas linhas / ver texto da pagina
        body_text = page.inner_text("body")
        print(f"   Body text[0:500]: {body_text[:500]}")

        # --- PARTE 2: Via kebab do admin (se tiver linhas) ---
        print("\n=== PARTE 2: Kebab admin ===")
        trs = page.evaluate("() => document.querySelectorAll('tbody tr').length")
        if trs > 0:
            print(f"   {trs} linhas na tabela admin. Testando kebab...")
            row = page.locator("tbody tr").first
            row.hover()
            page.wait_for_timeout(800)

            kebab = row.locator("button.chakra-menu__menu-button, button:has-text('more_vert')").first
            if kebab.count() == 0:
                # fallback: qualquer botao na linha
                kebab = row.locator("button").last
            print(f"   Kebab encontrado: {kebab.count() > 0}")
            if kebab.count() > 0:
                kebab.click()
                page.wait_for_timeout(1200)
                snap(page, "headed_03_admin_kebab_aberto")

                menuitems = page.locator("[class*='menuitem']")
                count = menuitems.count()
                print(f"   Menuitems: {count}")
                for i in range(count):
                    txt = menuitems.nth(i).inner_text()
                    print(f"   [{i}] '{txt}'")

                # Encontrar Visualizar
                vis_idx = None
                for i in range(count):
                    txt = menuitems.nth(i).inner_text()
                    if "visual" in txt.lower() or "visibility" in txt.lower():
                        vis_idx = i
                        break

                if vis_idx is not None:
                    print(f"\n   Clicando Visualizar (idx={vis_idx})...")
                    nav_urls = []
                    page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)
                    pages_antes = len(ctx.pages)
                    menuitems.nth(vis_idx).click()
                    page.wait_for_timeout(4000)
                    pages_depois = len(ctx.pages)
                    print(f"   Paginas: {pages_antes} -> {pages_depois}")
                    print(f"   URL atual: {page.url}")
                    print(f"   Navegacoes capturadas: {nav_urls}")
                    snap(page, "headed_04_pos_visualizar_admin", full=True)

                    if pages_depois > pages_antes:
                        nova_aba = ctx.pages[-1]
                        nova_aba.wait_for_load_state("domcontentloaded", timeout=15000)
                        nova_aba.wait_for_timeout(2000)
                        snap(nova_aba, "headed_05_nova_aba_admin", full=True)
                        print(f"   Nova aba URL: {nova_aba.url}")
                        print(f"   Nova aba texto: {nova_aba.inner_text('body')[:500]}")
        else:
            print("   Admin ainda sem linhas mesmo headed.")

        # --- PARTE 3: Aluno — testar Visualizar com listener de navegacao ---
        print("\n=== PARTE 3: Aluno qa11tc342588 Visualizar ===")
        browser2, ctx2, page2 = tw.nova_pagina(p)
        page2.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page2.fill("#user_email", "qa11tc342588@twygotest.com")
        page2.fill("#user_password", "twygoqa2026")
        page2.click("#user_submit")
        try:
            page2.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page2.wait_for_timeout(2000)
        tw.dispensar_nps(page2)

        page2.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                   wait_until="domcontentloaded", timeout=25000)
        page2.wait_for_timeout(3000)

        # Monitorar navegacao e novas paginas
        nav_urls2 = []
        page2.on("framenavigated", lambda f: nav_urls2.append(f.url) if f == page2.main_frame else None)

        kebab2 = page2.locator("button.chakra-menu__menu-button").first
        if kebab2.count() > 0:
            kebab2.click()
            page2.wait_for_timeout(1200)
            snap(page2, "headed_06_aluno_menu")

            menuitems2 = page2.locator("[class*='menuitem']")
            count2 = menuitems2.count()
            print(f"   Menuitems aluno: {count2}")
            for i in range(count2):
                txt = menuitems2.nth(i).inner_text()
                dis = menuitems2.nth(i).evaluate("el => el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true'")
                print(f"   [{i}] '{txt}' | disabled={dis}")

            # Clicar Visualizar (idx 2)
            if count2 >= 3:
                print(f"\n   Clicando Visualizar aluno (idx=2)...")
                pages2_antes = len(ctx2.pages)
                menuitems2.nth(2).click()
                page2.wait_for_timeout(5000)
                pages2_depois = len(ctx2.pages)
                print(f"   Paginas: {pages2_antes} -> {pages2_depois}")
                print(f"   URL apos: {page2.url}")
                print(f"   Navegacoes: {nav_urls2}")
                snap(page2, "headed_07_aluno_pos_visualizar", full=True)

                if pages2_depois > pages2_antes:
                    nova2 = ctx2.pages[-1]
                    nova2.wait_for_load_state("domcontentloaded", timeout=15000)
                    nova2.wait_for_timeout(3000)
                    snap(nova2, "headed_08_aluno_nova_aba", full=True)
                    print(f"   Nova aba URL: {nova2.url}")
                    print(f"   Nova aba body: {nova2.inner_text('body')[:600]}")

        browser2.close()
        ctx.close()
        browser.close()
        print("\n=== FIM HEADED RECON ===")


if __name__ == "__main__":
    main()
