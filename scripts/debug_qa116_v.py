# -*- coding: utf-8 -*-
"""Debug V — Investigar o que acontece ao clicar Alterar senha (modal vs navegacao)."""
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

    log(f"  URL atual: {pg.url}")

    # Encontrar linha qaliderpuro
    linha = pg.locator("tr").filter(has_text="qaliderpuro@teste.com").first
    log(f"  linha qaliderpuro count={linha.count()}")
    if linha.count():
        txt = linha.inner_text()
        log(f"  texto linha: {txt[:100]}")
        botoes = linha.locator("button").all()
        log(f"  botoes: {len(botoes)}")
        for i, b in enumerate(botoes):
            log(f"    btn[{i}]: {b.inner_text()[:30]} aria={b.get_attribute('aria-label')} class={b.get_attribute('class')[:50] if b.get_attribute('class') else ''}")

        # Clicar no botao kebab
        botoes[-1].click(force=True)
        pg.wait_for_timeout(2000)
        snap(pg, "v_kebab_aberto")

        # Ver menuitems visiveis
        menuitems = pg.locator("[role='menuitem']:visible").all()
        log(f"  menuitems visiveis: {len(menuitems)}")
        for mi in menuitems:
            log(f"    '{mi.inner_text()}'")

        # Clicar "Alterar senha"
        for mi in menuitems:
            if "Alterar senha" in mi.inner_text():
                log("  -> clicando Alterar senha")
                mi.click()
                pg.wait_for_timeout(3000)  # esperar mais
                snap(pg, "v_apos_alterar_senha")
                log(f"  URL apos click: {pg.url}")
                break

    # Inspecionar o estado atual
    log(f"  URL final: {pg.url}")

    # Ver se algum modal/dialog foi aberto
    dialogs = pg.evaluate("""() => {
        return [...document.querySelectorAll('[role="dialog"], [role="alertdialog"], .chakra-modal__content, [data-testid*="modal"]')]
        .filter(d => d.offsetParent !== null || getComputedStyle(d).visibility !== 'hidden')
        .map(d => ({
            tag: d.tagName,
            role: d.getAttribute('role'),
            class: d.className.slice(0,80),
            text: (d.innerText||'').slice(0,300),
            inputs: [...d.querySelectorAll('input')].map(i => ({type:i.type, id:i.id, name:i.name, placeholder:i.placeholder}))
        }));
    }""")
    log(f"  Dialogs: {json.dumps(dialogs, ensure_ascii=False)[:3000]}")

    # Verificar se algum toast/notificacao apareceu
    toasts = pg.locator("[data-status], [role='alert'], [class*='toast'], [class*='alert']").all_text_contents()
    log(f"  Toasts/alerts: {toasts[:5]}")

    snap(pg, "v_estado_final")
    pg.wait_for_timeout(3000)
    ca.close(); ba.close()
