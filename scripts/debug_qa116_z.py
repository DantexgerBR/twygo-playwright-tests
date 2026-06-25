# -*- coding: utf-8 -*-
"""Debug Z — capturar screenshot imediato + tentar URL direta de alterar senha."""
import json, sys, re, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
QALIDERPURO_ID = 4299626

log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

def dispensar(pg):
    tw.dispensar_nps(pg)
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, headless=False, slow_mo=100)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # Tentar URL direta de alterar senha
    possiveis = [
        f"{BASE_URL}/o/{ORG_ID}/users/{QALIDERPURO_ID}/change_password",
        f"{BASE_URL}/o/{ORG_ID}/users/{QALIDERPURO_ID}/password",
        f"{BASE_URL}/o/{ORG_ID}/professionals/{QALIDERPURO_ID}/change_password",
    ]
    for url in possiveis:
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=10000)
            pg.wait_for_timeout(1000)
            log(f"  URL {url} → {pg.url} status~={pg.url}")
            snap(pg, f"z_url_{url.split('/')[-1]}")
        except Exception as e:
            log(f"  URL {url} → erro: {e}")

    # Tentar via a pagina de lista
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    linha = pg.locator("tr").filter(has_text="qaliderpuro@teste.com").first
    kebab = linha.locator("button").last
    kebab_box = kebab.bounding_box()
    pg.mouse.click(kebab_box['x'] + kebab_box['width']/2, kebab_box['y'] + kebab_box['height']/2)
    pg.wait_for_timeout(800)

    # Capturar coordenadas de Alterar senha
    alterar_box = pg.evaluate("""() => {
        const items = [...document.querySelectorAll('[role="menuitem"]')];
        const item = items.find(el => el.innerText && el.innerText.includes('Alterar senha'));
        return item ? item.getBoundingClientRect() : null;
    }""")
    log(f"  Alterar senha box: {alterar_box}")

    if alterar_box:
        cx = alterar_box['x'] + alterar_box['width']/2
        cy = alterar_box['y'] + alterar_box['height']/2
        log(f"  Clicando em ({cx:.0f}, {cy:.0f})")

        # Escutar navegação
        pg.on("load", lambda: log(f"  [EVENT] load: {pg.url}"))
        pg.on("framenavigated", lambda frame: log(f"  [EVENT] nav: {frame.url}"))

        pg.mouse.click(cx, cy)

        # Screenshots imediatos a cada 200ms
        for i in range(15):
            pg.wait_for_timeout(200)
            url = pg.url
            # Verificar todos os elementos
            count_modals = pg.evaluate("() => document.querySelectorAll('.chakra-modal__overlay, .chakra-modal__content-container').length")
            count_dialogs = pg.evaluate("() => document.querySelectorAll('[role=dialog], [role=alertdialog]').length")
            count_fixed = pg.evaluate("() => [...document.querySelectorAll('*')].filter(el => window.getComputedStyle(el).position==='fixed' && el.getBoundingClientRect().height>100).length")
            log(f"  [{i*200}ms] url={url[:60]} modals={count_modals} dialogs={count_dialogs} fixed={count_fixed}")
            if count_modals > 0 or count_dialogs > 1:  # >1 pq o popover ja e 1
                log("  ENCONTROU algo!")
                snap(pg, f"z_modal_{i*200}ms")
                break

    snap(pg, "z_estado_final")
    pg.wait_for_timeout(3000)
    ca.close(); ba.close()
