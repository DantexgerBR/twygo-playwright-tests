# -*- coding: utf-8 -*-
"""Debug W — clicar Alterar senha e esperar modal aparecer + inspecionar."""
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
    ba, ca, pg = tw.nova_pagina(p, headless=False, slow_mo=300)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    # Filtrar por nome para garantir linha certa
    # Usar o campo de busca da tabela
    busca = pg.locator("input[placeholder*='Pesquisa'], input[placeholder*='Busca'], input[placeholder*='pesquisa'], [data-test*='search'] input").first
    if not busca.count():
        busca = pg.locator("input[placeholder*='search'], input[placeholder*='nome']").first
    log(f"  Campo busca count={busca.count()}")
    if busca.count():
        busca.fill("qaliderpuro")
        pg.wait_for_timeout(2000)
        snap(pg, "w_busca_qaliderpuro")
        log("  Buscou por qaliderpuro")

    # Encontrar linha
    linha = pg.locator("tr").filter(has_text="qaliderpuro@teste.com").first
    log(f"  linha count={linha.count()}")
    if not linha.count():
        linha = pg.locator("tr").filter(has_text="QALider Puro116").first
        log(f"  linha (by nome) count={linha.count()}")

    if linha.count():
        # Clicar kebab da linha
        kebab_btn = linha.locator("button.chakra-menu__menu-button").first
        if not kebab_btn.count():
            kebab_btn = linha.locator("button").last
        log(f"  kebab btn count={kebab_btn.count()}")
        kebab_btn.click()
        pg.wait_for_timeout(1500)
        snap(pg, "w_kebab_aberto")

        # Esperar menu ficar visivel
        try:
            pg.wait_for_selector("[role='menu']:visible", timeout=5000)
        except:
            log("  menu nao ficou visivel via wait_for_selector")

        # Ver menuitems visiveis
        menu = pg.locator("[role='menu']:visible").first
        if menu.count():
            itens = menu.locator("[role='menuitem']").all()
            log(f"  menu items: {len(itens)}")
            for item in itens:
                log(f"    '{item.inner_text()}'")
            # Clicar Alterar senha
            for item in itens:
                if "Alterar senha" in item.inner_text():
                    item.click()
                    log("  -> clicou Alterar senha")
                    pg.wait_for_timeout(1000)
                    break

        snap(pg, "w_apos_alterar_senha")

        # Esperar modal de senha aparecer
        try:
            modal_sel = "dialog, [role='dialog']:not(.chakra-popover__content), .chakra-modal__content-container"
            pg.wait_for_selector(modal_sel, timeout=8000)
            log("  modal apareceu!")
            snap(pg, "w_modal_senha")
        except Exception as e:
            log(f"  modal nao apareceu: {e}")

        # Inspecionar DOM completo depois do click
        todos = pg.evaluate("""() => {
            return [...document.querySelectorAll('dialog, [role="dialog"], .chakra-modal__content, [class*="modal"], [class*="dialog"]')]
            .filter(el => {
                const s = window.getComputedStyle(el);
                return s.display !== 'none' && s.visibility !== 'hidden' && el.offsetParent !== null;
            })
            .map(el => ({
                tag: el.tagName,
                role: el.getAttribute('role'),
                class: el.className.slice(0,80),
                text: (el.innerText||'').slice(0,200),
                inputs: [...el.querySelectorAll('input,textarea')].map(i => ({type:i.type,id:i.id,placeholder:i.placeholder}))
            }));
        }""")
        log(f"  DOM dialogs: {json.dumps(todos, ensure_ascii=False)[:3000]}")

        # Estado da pagina
        snap(pg, "w_estado_final")

    pg.wait_for_timeout(5000)
    ca.close(); ba.close()
