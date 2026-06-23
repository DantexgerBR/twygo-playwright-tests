"""
Recon QA 1.8 — Teste discriminante: get_by_role("menuitem", name="Visualizar").
Se o Playwright lanca "intercepts pointer events" -> overlay bloqueando (automacao).
Se menu fecha e navega -> feature funciona.
Se menu fecha e nada -> bug real confirmado.
Adicionar console listener para capturar erros React.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
from playwright.sync_api import TimeoutError as PWTimeout

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


def testar_visualizar_role(page, ctx, nome_snap):
    """Testa click via get_by_role para hit-testing correto."""
    console_msgs = []
    page.on("console", lambda m: console_msgs.append(f"{m.type}: {m.text}"))
    nav_urls = []
    page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)

    snap(page, f"{nome_snap}_00_antes_kebab")

    # Ver linhas da tabela
    rows = page.locator("tbody tr")
    n = rows.count()
    print(f"   Linhas: {n}")

    if n == 0:
        print("   Sem linhas")
        return None

    # Hover e abrir kebab
    rows.first.hover()
    page.wait_for_timeout(500)
    kebab = rows.first.locator("button.chakra-menu__menu-button").first
    if kebab.count() == 0:
        kebab = page.locator("button.chakra-menu__menu-button").first
    kebab.click()
    page.wait_for_timeout(1200)
    snap(page, f"{nome_snap}_01_menu_aberto")

    # Tentar get_by_role
    vis = page.get_by_role("menuitem", name="Visualizar")
    cnt = vis.count()
    print(f"   get_by_role menuitem Visualizar count: {cnt}")

    if cnt == 0:
        print("   Nao encontrado via role. Tentando exato...")
        vis = page.get_by_role("menuitem", name="Visualizar", exact=True)
        cnt = vis.count()
        print(f"   exact count: {cnt}")

    if cnt > 0:
        print(f"   Clicando via role (sem force, sem coords)...")
        pages_antes = len(ctx.pages)

        try:
            vis.first.click(timeout=5000)
            print("   Click bem-sucedido (sem excecao)")
        except PWTimeout as e:
            print(f"   TimeoutError: {e}")
            snap(page, f"{nome_snap}_02_timeout")
            return None
        except Exception as e:
            print(f"   Excecao: {type(e).__name__}: {e}")
            snap(page, f"{nome_snap}_02_excecao")
            return None

        page.wait_for_timeout(4000)
        pages_depois = len(ctx.pages)

        print(f"   URL: {page.url}")
        print(f"   Paginas: {pages_antes} -> {pages_depois}")
        print(f"   Navegacoes: {nav_urls}")
        print(f"   Console msgs ({len(console_msgs)}):")
        for m in console_msgs[-15:]:
            print(f"   {m}")

        snap(page, f"{nome_snap}_02_pos_click", full=True)

        if pages_depois > pages_antes:
            nova = ctx.pages[-1]
            nova.wait_for_load_state("domcontentloaded", timeout=15000)
            nova.wait_for_timeout(3000)
            snap(nova, f"{nome_snap}_03_nova_aba", full=True)
            print(f"   Nova aba URL: {nova.url}")
            body = nova.inner_text("body")[:800]
            print(f"   Nova aba body: {body}")
            nova.close()
            return nova.url

        # Verificar se navegou na mesma aba
        body = page.inner_text("body")[:400]
        print(f"   Body atual: {body}")
        # Procurar por "Visualizar registro" no body
        if "Visualizar registro" in body or "Visualizar" in page.url:
            print("   ACHOU 'Visualizar registro' na tela!")
            return page.url
        return page.url
    else:
        print("   Nenhum menuitem Visualizar encontrado via role")
        return None


def main():
    with tw.sync_playwright() as p:
        # === ALUNO: Externo Pendente ===
        print("\n=== TESTE 1: Aluno — Externo Pendente (menu simples 5 itens) ===")
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

        result_aluno = testar_visualizar_role(page, ctx, "role_aluno")
        print(f"\n   RESULTADO ALUNO: {result_aluno}")
        browser.close()

        # === ADMIN: linha 2 = Richard Sebold Externo Emitido ===
        print("\n=== TESTE 2: Admin — Externo Emitido (linha 2) ===")
        browser2, ctx2, page2 = tw.nova_pagina(p)
        tw.login(page2, c_admin, admin=True)
        page2.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                   wait_until="domcontentloaded", timeout=25000)
        page2.wait_for_timeout(5000)

        # Ir para linha 2 (Richard Sebold Externo Emitido)
        rows2 = page2.locator("tbody tr")
        row2 = rows2.nth(2)
        row2.hover()
        page2.wait_for_timeout(500)
        kebab2 = row2.locator("button.chakra-menu__menu-button").first
        kebab2.click()
        page2.wait_for_timeout(1200)
        snap(page2, "role_admin_01_menu_aberto")

        console_msgs2 = []
        page2.on("console", lambda m: console_msgs2.append(f"{m.type}: {m.text}"))
        nav_urls2 = []
        page2.on("framenavigated", lambda f: nav_urls2.append(f.url) if f == page2.main_frame else None)

        vis2 = page2.get_by_role("menuitem", name="Visualizar")
        cnt2 = vis2.count()
        print(f"   get_by_role count: {cnt2}")

        if cnt2 > 0:
            print(f"   Click em Visualizar via role...")
            pages2_antes = len(ctx2.pages)

            try:
                vis2.first.click(timeout=5000)
                print("   Click OK")
            except PWTimeout as e:
                print(f"   TimeoutError: {e}")
            except Exception as e:
                print(f"   Excecao: {type(e).__name__}: {e}")

            page2.wait_for_timeout(5000)
            pages2_depois = len(ctx2.pages)
            print(f"   URL: {page2.url}")
            print(f"   Paginas: {pages2_antes} -> {pages2_depois}")
            print(f"   Navegacoes: {nav_urls2}")
            print(f"   Console ({len(console_msgs2)}):")
            for m in console_msgs2[-10:]:
                print(f"   {m}")

            snap(page2, "role_admin_02_pos_click", full=True)

            if pages2_depois > pages2_antes:
                nova2 = ctx2.pages[-1]
                nova2.wait_for_load_state("domcontentloaded", timeout=15000)
                nova2.wait_for_timeout(3000)
                snap(nova2, "role_admin_03_nova_aba", full=True)
                print(f"   Nova aba URL: {nova2.url}")
                print(f"   Body: {nova2.inner_text('body')[:600]}")

            body2 = page2.inner_text("body")[:500]
            print(f"   Body admin: {body2}")

        ctx2.close()
        browser2.close()

        # === ADMIN: linha 1 = Interno ===
        print("\n=== TESTE 3: Admin — Interno (linha 1 = Playwrite do zero) ===")
        browser3, ctx3, page3 = tw.nova_pagina(p)
        tw.login(page3, c_admin, admin=True)
        page3.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                   wait_until="domcontentloaded", timeout=25000)
        page3.wait_for_timeout(5000)

        rows3 = page3.locator("tbody tr")
        row3 = rows3.nth(1)  # qa11tc342816 / Interno
        row3.hover()
        page3.wait_for_timeout(500)
        kebab3 = row3.locator("button.chakra-menu__menu-button").first
        kebab3.click()
        page3.wait_for_timeout(1200)
        snap(page3, "role_interno_01_menu_aberto")

        nav_urls3 = []
        page3.on("framenavigated", lambda f: nav_urls3.append(f.url) if f == page3.main_frame else None)

        vis3 = page3.get_by_role("menuitem", name="Visualizar")
        cnt3 = vis3.count()
        print(f"   get_by_role count interno: {cnt3}")

        if cnt3 > 0:
            pages3_antes = len(ctx3.pages)
            try:
                vis3.first.click(timeout=5000)
                print("   Click OK interno")
            except Exception as e:
                print(f"   Excecao: {type(e).__name__}: {e}")

            page3.wait_for_timeout(5000)
            pages3_depois = len(ctx3.pages)
            print(f"   URL: {page3.url}")
            print(f"   Paginas: {pages3_antes} -> {pages3_depois}")
            print(f"   Navegacoes: {nav_urls3}")
            snap(page3, "role_interno_02_pos_click", full=True)

            if pages3_depois > pages3_antes:
                nova3 = ctx3.pages[-1]
                nova3.wait_for_load_state("domcontentloaded", timeout=15000)
                nova3.wait_for_timeout(3000)
                snap(nova3, "role_interno_03_nova_aba", full=True)
                print(f"   Nova aba URL: {nova3.url}")
                print(f"   Body nova aba: {nova3.inner_text('body')[:600]}")

        ctx3.close()
        browser3.close()
        print("\n=== FIM ROLE CLICK TEST ===")


if __name__ == "__main__":
    main()
