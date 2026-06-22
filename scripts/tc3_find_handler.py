"""tc3_find_handler.py — Encontra e aciona o handler de 'Alterar senha' via React.

Abordagem: intercepta a network request que o modal de Alterar Senha faz quando
o form e submetido, capturando o endpoint real via page.route.

ALTERNATIVA: tenta via 'Acoes em massa > Redefinir senha' que pode ter um
endpoint diferente.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
USER_ID = "4298402"
TC3_EMAIL = "qa11tc342588@twygotest.com"
TC3_NOVA_SENHA = "twygoqa2026"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def main():
    log("=" * 60)
    log("tc3_find_handler.py — Acoes em massa > Redefinir senha")
    log("=" * 60)

    # Intercepta requests do dominio Twygo
    requests_intercept = []

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)

        def on_request(req):
            if "registrosf2" in req.url and req.method in ("POST", "PUT", "PATCH"):
                post_data = ""
                try:
                    post_data = req.post_data or ""
                except Exception:
                    pass
                requests_intercept.append({
                    "method": req.method,
                    "url": req.url[:200],
                    "data": post_data[:300]
                })

        page.on("request", on_request)

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
            page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            # Pesquisa usuario
            busca = page.locator("input[placeholder='Pesquise aqui']").first
            if busca.is_visible(timeout=2000):
                busca.fill("qa11tc342588")
                page.wait_for_timeout(1500)
            tw.snap(page, EVID, "tc3_find_lista")

            # Seleciona o checkbox da linha do usuario
            row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
            if row.count() == 0:
                log("ERRO: linha do usuario nao encontrada")
                return

            checkbox = row.locator("input[type='checkbox']").first
            if checkbox.count() > 0:
                checkbox.check(force=True)
                page.wait_for_timeout(500)
                log("Checkbox selecionado")
            else:
                log("Checkbox nao encontrado, tentando selecionar a linha")

            tw.snap(page, EVID, "tc3_find_checkbox")

            # Clica em "Acoes em massa"
            btn_acoes = page.locator("button, a").filter(has_text="Ações em massa").first
            if btn_acoes.count() == 0:
                btn_acoes = page.locator("button, a").filter(has_text="Acoes em massa").first
            if btn_acoes.count() > 0:
                btn_acoes.click()
                page.wait_for_timeout(1000)
                tw.snap(page, EVID, "tc3_find_acoes_menu")
                log("Menu Acoes em massa aberto")

                # Busca item "Redefinir senha"
                items = page.locator("[role='menuitem'], li, button").filter(
                    has_text="senha"
                ).all()
                log(f"Itens de menu com 'senha': {[i.inner_text().strip()[:30] for i in items[:5]]}")

                # Tenta clicar em "Redefinir senha"
                for item in items[:3]:
                    try:
                        txt = item.inner_text().strip()
                        if "senha" in txt.lower():
                            log(f"Clicando em: {txt!r}")
                            item.click(timeout=3000)
                            page.wait_for_timeout(2000)
                            tw.snap(page, EVID, "tc3_find_pos_redefinir")
                            break
                    except Exception as e:
                        log(f"  Erro: {e}")

            else:
                log("Botao 'Acoes em massa' nao encontrado")
                # Lista todos os botoes
                botoes = page.locator("button").all()
                log(f"Botoes na pagina: {[b.inner_text()[:20] for b in botoes[:10]]}")

            # Log das requests capturadas
            log(f"\nRequests Twygo capturadas: {len(requests_intercept)}")
            for r in requests_intercept:
                log(f"  {r['method']} {r['url']}")
                if r["data"]:
                    log(f"    data: {r['data'][:100]}")

            tw.snap(page, EVID, "tc3_find_final")

        finally:
            ctx.close()
            browser.close()


if __name__ == "__main__":
    main()
