"""
Recon QA 1.8 — Click CORRETO em Visualizar do menu dropdown.
O menu real esta em left~=1188 (nao na sidebar left~=23).
Filtra por posicao X > 500 para garantir o dropdown.
Testa admin (Externo Emitido, linha 2) e aluno (Externo Pendente).
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


def clicar_visualizar_dropdown(page, ctx, nome_snap, row_locator=None, aluno=False):
    """
    Abre kebab de uma linha e clica em Visualizar no dropdown real (left > 500).
    Retorna URL resultante ou None se sem navegacao.
    """
    if row_locator is None:
        row_locator = page.locator("tbody tr").nth(2)

    txt = row_locator.inner_text()
    print(f"   Linha: {txt[:80]}")

    # Hover e abrir kebab
    if not aluno:
        row_locator.hover()
        page.wait_for_timeout(500)
    kebab = row_locator.locator("button.chakra-menu__menu-button").first
    if kebab.count() == 0:
        kebab = page.locator("button.chakra-menu__menu-button").first
    if kebab.count() == 0:
        print("   Kebab nao encontrado")
        return None

    kebab.click()
    page.wait_for_timeout(1500)
    snap(page, f"{nome_snap}_01_menu_aberto")

    # Encontrar todos menuitems com posicao no dropdown (left > 500)
    dropdown_items = page.evaluate("""() => {
        const items = Array.from(document.querySelectorAll('[class*="menuitem"]'));
        return items
            .map(el => {
                const r = el.getBoundingClientRect();
                return {
                    text: el.innerText.trim(),
                    left: Math.round(r.left),
                    top: Math.round(r.top),
                    width: Math.round(r.width),
                    height: Math.round(r.height),
                    centerX: Math.round(r.left + r.width / 2),
                    centerY: Math.round(r.top + r.height / 2),
                    disabled: el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true',
                    dataDisabled: el.getAttribute('data-disabled')
                };
            })
            .filter(i => i.left > 500 && i.width > 0 && i.height > 0);
    }""")

    print(f"   Items do dropdown (left > 500): {len(dropdown_items)}")
    for item in dropdown_items:
        print(f"   '{item['text']}' | left={item['left']} top={item['top']} | disabled={item['disabled']}")

    # Encontrar Visualizar no dropdown
    vis_item = next((i for i in dropdown_items if "visual" in i["text"].lower() or "visibility" in i["text"].lower()), None)
    print(f"\n   Item Visualizar: {vis_item}")

    if vis_item is None:
        print("   Visualizar nao encontrado no dropdown")
        snap(page, f"{nome_snap}_02_sem_visualizar", full=True)
        return None

    # Registrar requests
    requests_twygo = []
    nav_urls = []
    page.on("request", lambda req: requests_twygo.append(f"{req.method} {req.url}") if "twygoead" in req.url and req.resource_type in ["fetch", "xhr", "document"] else None)
    page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)

    # Clicar no Visualizar pelo centro do elemento no dropdown
    cx = vis_item["centerX"]
    cy = vis_item["centerY"]
    print(f"\n   Clicando em Visualizar ({cx}, {cy})...")
    pages_antes = len(ctx.pages)
    page.mouse.click(cx, cy)
    page.wait_for_timeout(5000)
    pages_depois = len(ctx.pages)

    print(f"   URL: {page.url}")
    print(f"   Paginas: {pages_antes} -> {pages_depois}")
    print(f"   Navegacoes: {nav_urls}")
    print(f"   Requests Twygo ({len(requests_twygo)}):")
    for r in requests_twygo[:10]:
        print(f"   {r[:120]}")

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
    else:
        body = page.inner_text("body")[:300]
        print(f"\n   Tela atual body: {body}")
        return page.url


def main():
    with tw.sync_playwright() as p:
        # === ADMIN: Externo Emitido (Richard Sebold FGV, linha 2) ===
        print("\n=== TC5/TC7: Admin Externo Emitido ===")
        browser, ctx, page = tw.nova_pagina(p)
        tw.login(page, c_admin, admin=True)
        page.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                  wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(5000)
        trs = page.evaluate("() => document.querySelectorAll('tbody tr').length")
        print(f"   Linhas na tabela: {trs}")

        if trs >= 3:
            result_tc7 = clicar_visualizar_dropdown(page, ctx, "tc7")
            print(f"\n   RESULTADO TC7 (Admin Externo Emitido): {result_tc7}")
        ctx.close()
        browser.close()

        # === ADMIN: Interno (linha 1 = qa11tc342816 / Interno) ===
        print("\n=== TC2: Admin Interno ===")
        browser2, ctx2, page2 = tw.nova_pagina(p)
        tw.login(page2, c_admin, admin=True)
        page2.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                   wait_until="domcontentloaded", timeout=25000)
        page2.wait_for_timeout(5000)

        trs2 = page2.evaluate("() => document.querySelectorAll('tbody tr').length")
        if trs2 >= 2:
            row1 = page2.locator("tbody tr").nth(1)
            txt1 = row1.inner_text()
            print(f"   Linha 1: {txt1[:80]}")
            result_tc2 = clicar_visualizar_dropdown(page2, ctx2, "tc2", row_locator=row1)
            print(f"\n   RESULTADO TC2 (Admin Interno): {result_tc2}")
        ctx2.close()
        browser2.close()

        # === ALUNO: Externo Pendente (unico registro) ===
        print("\n=== TC1/TC5 aluno: Externo Pendente ===")
        browser3, ctx3, page3 = tw.nova_pagina(p)
        page3.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page3.fill("#user_email", "qa11tc342588@twygotest.com")
        page3.fill("#user_password", "twygoqa2026")
        page3.click("#user_submit")
        try:
            page3.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page3.wait_for_timeout(2000)
        tw.dispensar_nps(page3)
        page3.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                   wait_until="domcontentloaded", timeout=25000)
        page3.wait_for_timeout(3000)

        n3 = page3.locator("tbody tr").count()
        print(f"   Linhas aluno: {n3}")
        if n3 > 0:
            row_a = page3.locator("tbody tr").first
            result_tc5_aluno = clicar_visualizar_dropdown(page3, ctx3, "tc5_aluno", row_locator=row_a, aluno=True)
            print(f"\n   RESULTADO TC5/aluno (Externo Pendente): {result_tc5_aluno}")

        browser3.close()
        print("\n=== FIM CLICK CORRETO ===")


if __name__ == "__main__":
    main()
