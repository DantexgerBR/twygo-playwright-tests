"""tc3_intercept_network.py — Intercepta a request real de Alterar Senha.

Abre o browser headed, admin vai para /users, abre kebab e captura a request
que e feita quando o form de Alterar Senha e submetido.

Executa em modo headed para ver o que acontece.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
USER_ID = "4298402"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)

requests_log = []


def log(msg):
    print(msg, flush=True)


def main():
    log("=" * 60)
    log("tc3_intercept_network.py")
    log("=" * 60)

    with tw.sync_playwright() as p:
        # Modo headed + slow_mo para ver o que acontece
        browser = p.chromium.launch(headless=False, slow_mo=800)
        ctx = browser.new_context(viewport={"width": 1500, "height": 950}, locale="pt-BR")
        page = ctx.new_page()

        # Intercepta TODAS as requests (nao so POST) do dominio Twygo
        def on_request(request):
            url = request.url
            if "registrosf2" in url or "twygoead" in url:
                requests_log.append({
                    "method": request.method,
                    "url": url[:150],
                    "post_data": (request.post_data or "")[:200]
                })

        def on_response(response):
            url = response.url
            if ("registrosf2" in url or "twygoead" in url) and response.status not in (200, 304):
                log(f"  RESP {response.status}: {url[:100]}")

        page.on("request", on_request)
        page.on("response", on_response)

        try:
            # Login admin
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.fill("#user_email", "dante.tavares@twygo.com")
            page.fill("#user_password", "123456")
            page.click("#user_submit")
            page.wait_for_timeout(3000)
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
                wait_until="domcontentloaded"
            )
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            # Lista de usuarios
            page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # Pesquisa usuario
            busca = page.locator("input[placeholder='Pesquise aqui']").first
            if busca.is_visible(timeout=2000):
                busca.fill("qa11tc342588")
                page.wait_for_timeout(1500)

            # Localiza linha e abre kebab
            row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
            kebab = row.locator("button").last
            kebab.click(force=True)
            page.wait_for_timeout(1500)

            # Log do menu visivel
            itens = tw.menu_visivel(page)
            log(f"Menu visivel: {itens}")

            # CRIA UM PONTO DE PAUSA para inspecao manual
            log("\n*** PAUSA: Com o menu aberto, vou clicar em 'Alterar senha' via locator...")
            log("    Capture o Network tab do DevTools se possivel")

            # Limpa o log de requests antes do clique
            requests_log.clear()

            # Clica em Alterar senha usando o locator direto (sem click_menuitem)
            # O elemento topmost e o div interno, vou tentar clicar no proprio li
            id_alterar = page.evaluate(
                "(pal)=>{const ms=Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
                "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;});"
                "const m=ms[ms.length-1];if(!m)return '';"
                "const it=Array.from(m.querySelectorAll('[role=menuitem]'))"
                ".find(e=>new RegExp(pal,'i').test(e.innerText||''));return it?it.id:'';}",
                "Alterar senha"
            )
            log(f"ID menuitem: {id_alterar!r}")

            if id_alterar:
                item = page.locator(f"#{id_alterar}")

                # Tenta clicar diretamente no elemento sem mover o mouse
                log("  Tentativa 1: item.click()")
                item.click(timeout=3000)
                page.wait_for_timeout(2000)

                menus_depois = page.evaluate(
                    "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
                    "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
                )
                log(f"  Menus apos item.click(): {menus_depois}")
                tw.snap(page, EVID, "tc3_intercept_apos_click")

                if menus_depois > 0:
                    log("  Menu ainda aberto. Tentando clicar com dispatch em todos os filhos...")
                    # Captura bounding boxes de todos os filhos do item
                    filhos_info = page.evaluate(f"""(rid) => {{
                        const item = document.getElementById(rid);
                        if (!item) return [];
                        const filhos = [item, ...item.querySelectorAll('*')];
                        return filhos.slice(0, 10).map(el => ({{
                            tag: el.tagName,
                            id: el.id || '',
                            class: el.className.slice(0, 50)
                        }}));
                    }}""", id_alterar)
                    log(f"  Filhos do menuitem: {filhos_info}")

            # Log das requests capturadas
            log(f"\nRequests do Twygo capturadas: {len(requests_log)}")
            for r in requests_log:
                log(f"  {r['method']} {r['url']}")
                if r["post_data"]:
                    log(f"    data: {r['post_data'][:100]}")

            # Aguarda para inspecao visual
            page.wait_for_timeout(3000)
            tw.snap(page, EVID, "tc3_intercept_final")

        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("FIM")
    log("=" * 60)


if __name__ == "__main__":
    main()
