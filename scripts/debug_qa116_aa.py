# -*- coding: utf-8 -*-
"""Debug AA — inspecionar os 2 dialogs que aparecem imediatamente apos clicar Alterar senha."""
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
QALIDERPURO_ID = 4299626

log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

def dispensar(pg):
    tw.dispensar_nps(pg)
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, headless=False, slow_mo=50)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

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

    alterar_box = pg.evaluate("""() => {
        const items = [...document.querySelectorAll('[role="menuitem"]')];
        const item = items.find(el => el.innerText && el.innerText.includes('Alterar senha'));
        return item ? item.getBoundingClientRect() : null;
    }""")

    if alterar_box:
        cx = alterar_box['x'] + alterar_box['width']/2
        cy = alterar_box['y'] + alterar_box['height']/2
        pg.mouse.click(cx, cy)

        # Inspecionar imediatamente — sem timeout
        dialogs_info = pg.evaluate("""() => {
            return [...document.querySelectorAll('[role="dialog"], [role="alertdialog"]')].map(d => ({
                tag: d.tagName,
                role: d.getAttribute('role'),
                class: d.className.slice(0,100),
                id: d.id,
                aria_label: d.getAttribute('aria-label'),
                text: (d.innerText||'').slice(0,300),
                visible: d.offsetParent !== null,
                display: window.getComputedStyle(d).display,
                inputs: [...d.querySelectorAll('input,textarea')].map(i => ({type:i.type,id:i.id,name:i.name,placeholder:i.placeholder}))
            }));
        }""")
        log(f"  Dialogs: {json.dumps(dialogs_info, ensure_ascii=False)[:3000]}")

        snap(pg, "aa_dialogs_imediato")

        # Esperar um pouco e checar novamente
        pg.wait_for_timeout(1000)
        dialogs_info2 = pg.evaluate("""() => {
            return [...document.querySelectorAll('[role="dialog"], [role="alertdialog"]')].map(d => ({
                role: d.getAttribute('role'),
                class: d.className.slice(0,100),
                text: (d.innerText||'').slice(0,300),
                visible: d.offsetParent !== null,
                display: window.getComputedStyle(d).display,
                inputs: [...d.querySelectorAll('input,textarea')].map(i => ({type:i.type,id:i.id,name:i.name,placeholder:i.placeholder}))
            }));
        }""")
        log(f"  Dialogs (1s depois): {json.dumps(dialogs_info2, ensure_ascii=False)[:3000]}")

        snap(pg, "aa_dialogs_1s")

        # Esperar 3s e checar novamente
        pg.wait_for_timeout(2000)
        dialogs_info3 = pg.evaluate("""() => {
            return [...document.querySelectorAll('[role="dialog"], [role="alertdialog"]')].map(d => ({
                role: d.getAttribute('role'),
                class: d.className.slice(0,100),
                text: (d.innerText||'').slice(0,300),
                visible: d.offsetParent !== null,
                display: window.getComputedStyle(d).display,
                inputs: [...d.querySelectorAll('input,textarea')].map(i => ({type:i.type,id:i.id,name:i.name,placeholder:i.placeholder}))
            }));
        }""")
        log(f"  Dialogs (3s depois): {json.dumps(dialogs_info3, ensure_ascii=False)[:3000]}")

        snap(pg, "aa_dialogs_3s")

    pg.wait_for_timeout(5000)
    ca.close(); ba.close()
