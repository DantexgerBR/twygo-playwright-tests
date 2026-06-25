# -*- coding: utf-8 -*-
"""Debug X — alterar senha com abordagem mais simples: wait_for_selector + click direto."""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)

log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

def dispensar(pg):
    tw.dispensar_nps(pg)
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, headless=False, slow_mo=200)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    # Verificar numero de usuarios na lista
    rows = pg.locator("tbody tr").all()
    log(f"  Linhas na tabela: {len(rows)}")
    for i, row in enumerate(rows[:10]):
        txt = row.inner_text()[:80].replace('\n',' ')
        log(f"    row[{i}]: {txt}")

    # Encontrar qaliderpuro
    linha = pg.locator("tr").filter(has_text="qaliderpuro@teste.com").first
    log(f"  linha qaliderpuro: count={linha.count()}")

    if linha.count():
        # Verificar coordenadas da linha
        box = linha.bounding_box()
        log(f"  linha bounding box: {box}")

        # Clicar no kebab (botao na extremidade direita da linha)
        kebab = linha.locator("button").last
        log(f"  kebab: {kebab.bounding_box()}")
        kebab.click()
        pg.wait_for_timeout(1000)

        # Esperar o menu estar visivel
        pg.wait_for_selector("[role='menu']:visible", timeout=5000)
        snap(pg, "x_menu_aberto")

        # Clicar em Alterar senha usando locator mais especifico
        # O item do menu tem data-index="2"
        alterar = pg.locator("[role='menu']:visible [role='menuitem']").filter(has_text="Alterar senha").first
        log(f"  Alterar senha locator: {alterar.count()}")
        if alterar.count():
            alterar.click()
            pg.wait_for_timeout(500)
            snap(pg, "x_apos_alterar_click")
            log("  Clicou Alterar senha")

            # Monitorar mudancas na pagina por 10 segundos
            for i in range(10):
                pg.wait_for_timeout(1000)
                url = pg.url
                # Verificar modais
                modal_count = pg.evaluate("""() => {
                    return [...document.querySelectorAll('.chakra-modal__content-container, .chakra-modal__overlay')].filter(el => {
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none';
                    }).length;
                }""")
                log(f"  [{i+1}s] url={url} modal_containers={modal_count}")
                if modal_count > 0:
                    log("  MODAL APARECEU!")
                    snap(pg, "x_modal_senha")
                    break

        snap(pg, "x_estado_final")

    # Inspeção total do DOM
    dom_estado = pg.evaluate("""() => {
        return {
            url: window.location.href,
            modals: [...document.querySelectorAll('.chakra-modal__content-container, .chakra-modal__overlay')].map(el => ({
                class: el.className.slice(0,60),
                display: window.getComputedStyle(el).display,
                children_count: el.children.length
            })),
            fixed_overlays: [...document.querySelectorAll('*')].filter(el => {
                return window.getComputedStyle(el).position === 'fixed' && el.getBoundingClientRect().height > 50 && el.offsetParent !== null;
            }).map(el => ({tag: el.tagName, class: el.className.slice(0,50), text: (el.innerText||'').slice(0,50)})).slice(0,5)
        };
    }""")
    log(f"  DOM final: {json.dumps(dom_estado, ensure_ascii=False)[:2000]}")

    pg.wait_for_timeout(3000)
    ca.close(); ba.close()
