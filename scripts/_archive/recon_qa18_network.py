"""
Recon QA 1.8 — Network listener ao clicar Visualizar.
Obrigatorio checar Network antes de concluir "nao funciona".
Testa admin Externo Emitido (25 linhas confirmadas).
Registra todos os requests/responses durante/apos o click.
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
        browser, ctx, page = tw.nova_pagina(p)
        tw.login(page, c_admin, admin=True)

        # Carregar lista sem filtro (25 linhas confirmadas)
        page.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                  wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(5000)
        trs = page.evaluate("() => document.querySelectorAll('tbody tr').length")
        print(f"   Linhas: {trs}")

        # Registrar requests/respostas
        requests_log = []
        responses_log = []

        def on_req(req):
            if req.resource_type in ["fetch", "xhr", "document"]:
                requests_log.append({
                    "method": req.method,
                    "url": req.url,
                })

        def on_resp(resp):
            if resp.request.resource_type in ["fetch", "xhr", "document"]:
                responses_log.append({
                    "status": resp.status,
                    "url": resp.url
                })

        page.on("request", on_req)
        page.on("response", on_resp)

        # Abrir kebab da linha 3 (Richard Sebold FGV - provavelmente Externo Emitido)
        print("\n   Verificando dados das primeiras 5 linhas...")
        rows_data = page.evaluate("""() => {
            const rows = Array.from(document.querySelectorAll('tbody tr')).slice(0, 5);
            return rows.map((r, i) => ({
                idx: i,
                text: r.innerText.trim().slice(0, 100)
            }));
        }""")
        for rd in rows_data:
            print(f"   Linha {rd['idx']}: {rd['text']}")

        # Hover e abrir kebab da TERCEIRA linha (idx=2 = Richard Sebold FGV 10h)
        row = page.locator("tbody tr").nth(2)
        row.hover()
        page.wait_for_timeout(600)

        # Limpar logs antes do click
        requests_log.clear()
        responses_log.clear()

        kebab = row.locator("button.chakra-menu__menu-button").first
        if kebab.count() == 0:
            kebab = row.locator("button").last
        kebab.click()
        page.wait_for_timeout(1200)
        snap(page, "net_01_menu_aberto_row2")

        # Ver menuitems visiveis
        vis_items = page.locator("[class*='menuitem']:visible")
        cnt = vis_items.count()
        print(f"\n   Menuitems visiveis: {cnt}")
        for i in range(cnt):
            txt = vis_items.nth(i).inner_text()
            dis = vis_items.nth(i).evaluate("el => el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true'")
            print(f"   [{i}] '{txt}' | disabled={dis}")

        # Clicar Visualizar (idx 3 = visibility/Visualizar no admin)
        vis_idx = None
        for i in range(cnt):
            txt = vis_items.nth(i).inner_text()
            if "visibility" in txt.lower() or "visual" in txt.lower():
                vis_idx = i
                break

        print(f"\n   Visualizar idx: {vis_idx}")
        if vis_idx is not None:
            vis_item = vis_items.nth(vis_idx)

            # Capturar rect do elemento
            rect = vis_item.evaluate("""el => {
                const r = el.getBoundingClientRect();
                return {left: r.left, top: r.top, width: r.width, height: r.height, centerX: r.left + r.width/2, centerY: r.top + r.height/2};
            }""")
            print(f"   Rect do Visualizar: {rect}")

            # Click normal
            print("\n   Clicando Visualizar...")
            requests_log.clear()
            responses_log.clear()
            nav_urls = []
            page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)

            pages_antes = len(ctx.pages)
            vis_item.click()
            page.wait_for_timeout(4000)
            pages_depois = len(ctx.pages)

            print(f"   URL: {page.url}")
            print(f"   Paginas: {pages_antes} -> {pages_depois}")
            print(f"   Navegacoes: {nav_urls}")
            print(f"\n   Requests apos click ({len(requests_log)}):")
            for req in requests_log[:15]:
                print(f"   {req['method']} {req['url'][:100]}")
            print(f"\n   Responses apos click ({len(responses_log)}):")
            for resp in responses_log[:15]:
                print(f"   {resp['status']} {resp['url'][:100]}")

            snap(page, "net_02_pos_click_visualizar", full=True)

            if pages_depois > pages_antes:
                nova = ctx.pages[-1]
                nova.wait_for_load_state("domcontentloaded", timeout=15000)
                nova.wait_for_timeout(3000)
                snap(nova, "net_03_nova_aba", full=True)
                print(f"   Nova aba URL: {nova.url}")

        ctx.close()
        browser.close()
        print("\n=== FIM NETWORK RECON ===")


if __name__ == "__main__":
    main()
