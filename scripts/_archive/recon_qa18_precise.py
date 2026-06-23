"""
Recon QA 1.8 — Click preciso em Visualizar usando posicao do menu aberto.
Abre kebab da linha 2 (Richard Sebold / Externo Emitido),
verifica quais menuitems ficam VISIVEIS COM POSICAO VALIDA,
e clica no que tem "Visualizar" usando click pela posicao central do elemento.
Registra tudo que acontece na network.
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

        page.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                  wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(5000)

        trs = page.evaluate("() => document.querySelectorAll('tbody tr').length")
        print(f"   Linhas: {trs}")

        # Linha 2 = Richard Sebold / Externo Emitido
        row2 = page.locator("tbody tr").nth(2)
        row_text = row2.inner_text()
        print(f"   Linha 2: {row_text[:80]}")

        # Hover e abrir kebab da linha 2
        row2.hover()
        page.wait_for_timeout(500)
        kebab2 = row2.locator("button.chakra-menu__menu-button").first
        if kebab2.count() == 0:
            kebab2 = row2.locator("button").last
        print(f"   Kebab found: {kebab2.count() > 0}")

        kebab2.click()
        page.wait_for_timeout(1500)
        snap(page, "prec_01_menu_aberto_row2")

        # Inspecionar TODOS os menuitems no DOM com posicao
        all_items = page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('[class*="menuitem"]'));
            return items.map(el => {
                const r = el.getBoundingClientRect();
                const visible = r.width > 0 && r.height > 0 && r.top >= 0 && r.top < window.innerHeight;
                const style = window.getComputedStyle(el);
                return {
                    text: el.innerText.trim().slice(0, 40),
                    top: Math.round(r.top),
                    left: Math.round(r.left),
                    width: Math.round(r.width),
                    height: Math.round(r.height),
                    visible: visible,
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity
                };
            });
        }""")

        print(f"\n   Total menuitems no DOM: {len(all_items)}")
        print("   Items VISIVEIS (top >= 0 e dentro da viewport):")
        visible_items = [i for i in all_items if i["visible"] and i["opacity"] != "0"]
        for item in visible_items:
            print(f"   text='{item['text']}' | top={item['top']} left={item['left']} w={item['width']} h={item['height']}")

        # Encontrar o Visualizar pelo texto e clicar pela posicao
        vis_item_info = next((i for i in visible_items if "visual" in i["text"].lower() or "visibility" in i["text"].lower()), None)
        print(f"\n   Item Visualizar info: {vis_item_info}")

        if vis_item_info:
            cx = vis_item_info["left"] + vis_item_info["width"] // 2
            cy = vis_item_info["top"] + vis_item_info["height"] // 2
            print(f"   Clicando em ({cx}, {cy})...")

            # Registrar requests antes e apos
            requests_apos = []
            responses_apos = []
            nav_urls = []

            def on_req(req):
                if req.resource_type in ["fetch", "xhr", "document"]:
                    requests_apos.append(f"{req.method} {req.url}")

            def on_resp(resp):
                if resp.request.resource_type in ["fetch", "xhr", "document"]:
                    responses_apos.append(f"{resp.status} {resp.url}")

            page.on("request", on_req)
            page.on("response", on_resp)
            page.on("framenavigated", lambda f: nav_urls.append(f.url) if f == page.main_frame else None)

            pages_antes = len(ctx.pages)
            page.mouse.click(cx, cy)
            page.wait_for_timeout(5000)
            pages_depois = len(ctx.pages)

            print(f"   URL apos: {page.url}")
            print(f"   Paginas: {pages_antes} -> {pages_depois}")
            print(f"   Navegacoes: {nav_urls}")
            print(f"\n   Requests ({len(requests_apos)}):")
            for r in requests_apos[:15]:
                # Filtrar apenas requests Twygo (nao analytics)
                if "twygoead" in r or "twygo" in r:
                    print(f"   TWYGO: {r[:120]}")
                else:
                    print(f"   ext: {r[:80]}")

            snap(page, "prec_02_pos_click", full=True)

            if pages_depois > pages_antes:
                nova = ctx.pages[-1]
                nova.wait_for_load_state("domcontentloaded", timeout=15000)
                nova.wait_for_timeout(3000)
                snap(nova, "prec_03_nova_aba", full=True)
                print(f"   Nova aba URL: {nova.url}")
                print(f"   Nova aba body: {nova.inner_text('body')[:600]}")
            else:
                # Verificar o que esta na tela agora
                body_excerpt = page.inner_text("body")[:400]
                print(f"\n   Body: {body_excerpt}")

        ctx.close()
        browser.close()
        print("\n=== FIM PRECISE RECON ===")


if __name__ == "__main__":
    main()
