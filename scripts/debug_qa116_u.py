# -*- coding: utf-8 -*-
"""Debug U — alterar senha via JS focado na linha de qaliderpuro + ver modal."""
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
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    # Encontrar o tr que contém qaliderpuro e clicar no seu kebab
    linha = pg.locator("tr").filter(has_text="qaliderpuro@teste.com").first
    log(f"  linha count={linha.count()}")
    if linha.count():
        # Clicar no ULTIMO botao da linha (kebab)
        botoes = linha.locator("button").all()
        log(f"  botoes na linha: {len(botoes)}")
        if botoes:
            botoes[-1].click(force=True)
            pg.wait_for_timeout(1500)
            snap(pg, "u_kebab_aberto")

            # Ver menuitems visiveis
            menuitems = pg.locator("[role='menuitem']:visible").all()
            log(f"  menuitems visiveis: {len(menuitems)}")
            for mi in menuitems:
                txt = mi.inner_text()
                log(f"    '{txt}'")

            # Clicar em Alterar senha
            for mi in menuitems:
                if "Alterar senha" in mi.inner_text():
                    mi.click()
                    log("  [alterar_senha] clicou!")
                    break
            pg.wait_for_timeout(2000)
            snap(pg, "u_apos_alterar_senha_click")

    # Ver o que apareceu
    # Inspecionar estrutura do modal/dialog
    modal_info = pg.evaluate("""() => {
        const dialogs = [...document.querySelectorAll('[role="dialog"], [role="alertdialog"], .chakra-modal__content')];
        return dialogs.filter(d => d.offsetParent !== null).map(d => ({
            tag: d.tagName,
            role: d.getAttribute('role'),
            class: d.className.slice(0, 80),
            text: (d.innerText || '').slice(0, 200),
            inputs: [...d.querySelectorAll('input')].map(i => ({type: i.type, placeholder: i.placeholder, name: i.name, id: i.id}))
        }));
    }""")
    log(f"  Modais/dialogs visiveis: {json.dumps(modal_info, ensure_ascii=False)[:3000]}")

    # Também verificar qualquer overlay
    overlays = pg.evaluate("""() => {
        return [...document.querySelectorAll('*')].filter(el => {
            const style = window.getComputedStyle(el);
            return style.position === 'fixed' && el.offsetParent !== null && el.getBoundingClientRect().height > 100;
        }).map(el => ({
            tag: el.tagName,
            class: el.className.slice(0,60),
            text: (el.innerText||'').slice(0,100),
        })).slice(0, 10);
    }""")
    log(f"  Overlays fixed: {json.dumps(overlays, ensure_ascii=False)[:2000]}")

    ca.close(); ba.close()
