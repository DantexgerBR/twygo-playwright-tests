"""recon_qa11_kebab_usuario.py — Abre o kebab do usuario QA11TC3 para ver opcoes.

Objetivo: verificar se existe "Redefinir senha" ou "Acessar como usuario"
no menu do usuario recentemente criado.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ADMIN_EMAIL = "dante.tavares@twygo.com"
ADMIN_SENHA = "123456"
ORG_ID = "37079"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def main():
    log("=" * 60)
    log("recon_qa11_kebab_usuario.py")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            # Login admin
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("#user_email", timeout=15000)
            page.fill("#user_email", ADMIN_EMAIL)
            page.fill("#user_password", ADMIN_SENHA)
            page.click("#user_submit")
            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            # Switch admin
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
                wait_until="domcontentloaded", timeout=60000
            )
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            log(f"Admin: {page.url[:60]}")

            # Lista de usuarios
            page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            tw.snap(page, EVID, "recon_kebab_lista_antes")
            log("Lista de usuarios carregada")

            # Busca usuario QA11TC3
            try:
                busca = page.locator("input[placeholder='Pesquise aqui']").first
                if busca.count() > 0 and busca.is_visible(timeout=2000):
                    busca.fill("QA11TC3")
                    page.wait_for_timeout(1500)
                    log("Buscando QA11TC3")
                    tw.snap(page, EVID, "recon_kebab_busca")
            except Exception as e:
                log(f"Busca erro: {e}")

            # Localiza linha do usuario QA11TC3
            row = page.locator("tr, [role='row']").filter(has_text="QA11TC3").first
            if row.count() == 0:
                # Tenta pelo email parcial
                row = page.locator("tr, [role='row']").filter(has_text="mailtest").first
            log(f"Linha encontrada: {row.count() > 0}")

            if row.count() > 0:
                # Dump do HTML da linha
                row_html = row.evaluate("el => el.outerHTML.slice(0, 1000)")
                log(f"\nHTML da linha:\n{row_html}")

                # Lista botoes na linha
                botoes = row.locator("button").all()
                log(f"\nBotoes na linha: {len(botoes)}")
                for b in botoes:
                    try:
                        txt = b.inner_text().strip()
                        cls = b.get_attribute("class") or ""
                        log(f"  text={txt!r} class={cls[:60]!r}")
                    except Exception:
                        pass

                # Clica no ultimo botao da linha (kebab/3 pontos)
                if botoes:
                    # Kebab geralmente e o ultimo botao
                    kebab = botoes[-1]
                    log(f"\nClicando no ultimo botao...")
                    kebab.scroll_into_view_if_needed()
                    kebab.click(timeout=5000)
                    page.wait_for_timeout(1500)
                    tw.snap(page, EVID, "recon_kebab_menu_aberto")
                    log("Kebab clicado, screenshot capturado")

                    # Lista itens do menu
                    menu_items = page.locator(
                        "[role='menuitem'], [class*='dropdown-item'], "
                        "[class*='menu-item'], li[class*='item']"
                    ).all()
                    log(f"\nItens de menu: {len(menu_items)}")
                    for item in menu_items:
                        try:
                            if item.is_visible(timeout=500):
                                txt = item.inner_text().strip()
                                log(f"  menuitem: {txt!r}")
                        except Exception:
                            pass

                    # Dump do popup/dropdown visivel
                    popup_html = page.evaluate("""() => {
                        const selectors = [
                            '[role="menu"]',
                            '[class*="dropdown-menu"]',
                            '[class*="popover"]',
                            '[class*="chakra-menu__menu-list"]',
                            '[data-popper-placement]'
                        ];
                        for (const sel of selectors) {
                            const el = document.querySelector(sel);
                            if (el && el.offsetParent !== null) {
                                return el.outerHTML.slice(0, 2000);
                            }
                        }
                        return 'nenhum popup encontrado';
                    }""")
                    log(f"\nHTML do popup:\n{popup_html}")
            else:
                log("USUARIO QA11TC3 NAO ENCONTRADO — usuario pode ter sido criado com email diferente")
                log("Tentando listar todos os usuarios recentes...")
                # Lista todos os usuarios sem filtro
                page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                page.wait_for_timeout(2000)
                tw.snap(page, EVID, "recon_kebab_lista_completa")

                rows = page.locator("table tbody tr").all()
                log(f"\nTotal usuarios: {len(rows)}")
                for r in rows[:5]:
                    try:
                        log(f"  {r.inner_text()[:100].strip()}")
                    except Exception:
                        pass

        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("RECON KEBAB CONCLUIDO")
    log("=" * 60)


if __name__ == "__main__":
    main()
