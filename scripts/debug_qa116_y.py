# -*- coding: utf-8 -*-
"""Debug Y — alterar senha via page.mouse.click em coordenadas exatas + investigar tela."""
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
    ba, ca, pg = tw.nova_pagina(p, headless=False, slow_mo=500)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    # Encontrar a linha qaliderpuro e o botao kebab
    linha = pg.locator("tr").filter(has_text="qaliderpuro@teste.com").first
    kebab = linha.locator("button").last
    kebab_box = kebab.bounding_box()
    log(f"  kebab box: {kebab_box}")

    # Clicar no kebab usando page.mouse (coordenadas absolutas)
    pg.mouse.click(kebab_box['x'] + kebab_box['width']/2, kebab_box['y'] + kebab_box['height']/2)
    pg.wait_for_timeout(1500)
    snap(pg, "y_menu_aberto")

    # Ver menuitems e suas posicoes
    menuitems_info = pg.evaluate("""() => {
        const items = [...document.querySelectorAll('[role="menuitem"]')];
        return items.filter(el => {
            const s = window.getComputedStyle(el);
            return s.display !== 'none' && s.visibility !== 'hidden' && el.offsetParent !== null;
        }).map(el => ({
            text: (el.innerText||'').replace(/\\n/g,' ').slice(0,40),
            box: el.getBoundingClientRect(),
            disabled: el.disabled,
        }));
    }""")
    log(f"  menuitems: {json.dumps(menuitems_info, ensure_ascii=False)}")

    # Encontrar "Alterar senha" e clicar nas coordenadas
    alterar = next((x for x in menuitems_info if "Alterar senha" in x.get("text","")), None)
    if alterar:
        box = alterar['box']
        cx = box['x'] + box['width']/2
        cy = box['y'] + box['height']/2
        log(f"  'Alterar senha' em ({cx:.0f}, {cy:.0f})")
        pg.mouse.click(cx, cy)
        pg.wait_for_timeout(3000)
        snap(pg, "y_apos_alterar_senha")

        # Verificar o que apareceu
        tudo = pg.evaluate("""() => {
            return [...document.querySelectorAll('*')].filter(el => {
                const s = window.getComputedStyle(el);
                return s.position === 'fixed' && el.getBoundingClientRect().height > 50
                    && s.display !== 'none' && el.offsetParent !== null;
            }).map(el => ({
                tag: el.tagName,
                role: el.getAttribute('role'),
                class: el.className.slice(0,80),
                text: (el.innerText||'').slice(0,200),
                inputs: [...el.querySelectorAll('input')].map(i => ({type:i.type,id:i.id}))
            })).slice(0,10);
        }""")
        log(f"  Fixed elements: {json.dumps(tudo, ensure_ascii=False)[:3000]}")
    else:
        log("  'Alterar senha' nao encontrado nos menuitems!")

    snap(pg, "y_estado_final")
    pg.wait_for_timeout(3000)
    ca.close(); ba.close()
