# -*- coding: utf-8 -*-
"""Debug I — inspecionar DOM do campo Pessoas e criar registro corretamente."""
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

LIDER_PURO_ID  = 4299626
LIDERADO_ID    = 4298605
FORA_ID        = 4298501

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

    # Inspecionar DOM do campo Pessoas
    log("\n--- Inspecionar DOM do campo Pessoas ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # Inspecionar a área do campo Pessoas
    dom_info = pg.evaluate("""() => {
        // Encontrar o label "Pessoas*"
        const all = [...document.querySelectorAll('label, .chakra-form-control')];
        for (const el of all) {
            if ((el.innerText||'').includes('Pessoas')) {
                const container = el.closest('.chakra-form-control') || el.parentElement;
                const buttons = [...container.querySelectorAll('button')];
                const inputs = [...container.querySelectorAll('input')];
                return {
                    container_class: container?.className?.slice(0,100),
                    buttons: buttons.map(b => ({
                        text: b.innerText.slice(0,50),
                        type: b.type,
                        aria: b.getAttribute('aria-label'),
                        class: b.className.slice(0,60),
                        visible: b.offsetParent !== null,
                        rect: b.getBoundingClientRect(),
                    })),
                    inputs: inputs.map(i => ({
                        type: i.type,
                        placeholder: i.placeholder,
                        name: i.name,
                        visible: i.offsetParent !== null,
                    })),
                };
            }
        }
        return 'label Pessoas não encontrado';
    }""")
    log(f"  DOM Pessoas: {json.dumps(dom_info, ensure_ascii=False)}")

    # Tentar clicar pelo ícone de pessoa (o SVG com ícone person)
    # No screenshot vemos um ícone roxo de pessoa à direita do input
    pessoas_area = pg.evaluate("""() => {
        // Procurar por qualquer botão visível próximo ao texto "Adicionar pessoas"
        const inp = [...document.querySelectorAll('input')].find(i => i.placeholder === 'Adicionar pessoas');
        if (!inp) return 'input não encontrado';
        const container = inp.parentElement;
        const rect = container.getBoundingClientRect();
        return {
            x: rect.right - 20,  // clique no ícone à direita
            y: rect.top + rect.height/2,
            container_text: container.innerText.slice(0,50),
        };
    }""")
    log(f"  Pessoas area: {pessoas_area}")

    if isinstance(pessoas_area, dict) and "x" in pessoas_area:
        pg.mouse.click(pessoas_area["x"], pessoas_area["y"])
        pg.wait_for_timeout(2000)
        snap(pg, "i_modal_pessoas")
        modal = pg.locator("[role='dialog']").filter(visible=True).first
        log(f"  Modal aberto via coords: {modal.count() > 0}")
        if modal.count():
            modal_text = modal.inner_text()
            log(f"  Modal text: {modal_text[:400]}")

    ca.close(); ba.close()
