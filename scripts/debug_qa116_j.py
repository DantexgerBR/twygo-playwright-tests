# -*- coding: utf-8 -*-
"""Debug J — encontrar e clicar no campo Pessoas corretamente."""
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

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # Mapear todos os elementos clicáveis próximos ao label Pessoas
    dom = pg.evaluate("""() => {
        const results = [];
        // Buscar label Pessoas
        const labels = [...document.querySelectorAll('label, span, p, div')];
        for (const lbl of labels) {
            if ((lbl.innerText||'').trim() === 'Pessoas' || (lbl.innerText||'').startsWith('Pessoas')) {
                const container = lbl.closest('.chakra-form-control, .css-') || lbl.parentElement?.parentElement;
                // Mapear todos os elementos interativos no container
                const interativos = [...(container || document.body).querySelectorAll(
                    'button, [role="button"], [tabindex], .chakra-input, div[class*="input"], span[class*="input"], [data-focus], [aria-haspopup]'
                )].slice(0, 20);
                results.push({
                    label_tag: lbl.tagName,
                    label_text: (lbl.innerText||'').slice(0,30),
                    container_tag: container?.tagName,
                    container_class: (container?.className||'').slice(0,80),
                    interativos: interativos.map(el => ({
                        tag: el.tagName,
                        role: el.getAttribute('role'),
                        tabindex: el.getAttribute('tabindex'),
                        class: (el.className||'').slice(0,60),
                        text: (el.innerText||'').slice(0,30),
                        visible: el.offsetParent !== null,
                        rect: el.getBoundingClientRect(),
                    })),
                });
                break;
            }
        }
        return results;
    }""")
    log(f"  DOM Pessoas mapeamento: {json.dumps(dom, ensure_ascii=False, indent=2)[:2000]}")

    # Tentar clicar nas coordenadas do ícone de pessoa visível no screenshot
    # No screenshot (1280px), o ícone está aproximadamente em x=509, y=421
    pg.mouse.click(509, 421)
    pg.wait_for_timeout(2000)
    snap(pg, "j_click_coord_pessoas")
    modal = pg.locator("[role='dialog']").filter(visible=True).first
    log(f"  Modal via coord: {modal.count() > 0}")

    if modal.count():
        log(f"  Modal text: {modal.inner_text()[:300]}")
    else:
        # Tentar click em outros pontos próximos
        for x, y in [(340, 421), (480, 421), (500, 421), (510, 421)]:
            pg.mouse.click(x, y)
            pg.wait_for_timeout(1000)
            if pg.locator("[role='dialog']").filter(visible=True).count():
                log(f"  Modal aberto em ({x},{y})")
                snap(pg, f"j_modal_{x}_{y}")
                break

    ca.close(); ba.close()
