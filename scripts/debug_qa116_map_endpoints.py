# -*- coding: utf-8 -*-
"""Mapear endpoints de aprovacao de registro interceptando network como admin."""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
# Registro do liderado1 (QA116-Liderado-Externo, id=44280186, situacao=Aprovado)
# Registro do devtestes (QA116-ForaEquipe-Externo, id=44280185)
FORA_REC_ID    = 44280185

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # Capturar requests enquanto admin interage com kebab de aprovacao
    captured = []
    def on_request(req):
        if req.method in ("POST","PATCH","PUT") and "/records/" in req.url:
            captured.append({"method": req.method, "url": req.url, "post_data": req.post_data})
            log(f"  [REQ] {req.method} {req.url}")
    pg.on("request", on_request)

    # Navegar para registros e tentar encontrar o kebab de aprovacao no registro QA116-ForaEquipe
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)

    # Buscar pelo registro ForaEquipe
    search = pg.locator("input[placeholder*='Pesquise por pessoa' i]").first
    if search.count():
        search.fill("QA116-ForaEquipe")
        pg.wait_for_timeout(2000)

    snap(pg, "map_busca_foraequipe")

    # Clicar no kebab da primeira linha
    first_row = pg.locator("tbody tr").first
    if first_row.count():
        kebab = first_row.locator("button").last
        box = kebab.bounding_box()
        if box:
            pg.mouse.move(box['x']+box['width']/2, box['y']+box['height']/2)
            pg.wait_for_timeout(300)
            pg.mouse.click(box['x']+box['width']/2, box['y']+box['height']/2)
            pg.wait_for_timeout(1000)
            snap(pg, "map_kebab_aberto")

            items = pg.evaluate("""() => {
                return [...document.querySelectorAll('[role="menuitem"]')].map(el => ({
                    text: (el.innerText||'').trim().slice(0,50),
                    disabled: el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true'
                }));
            }""")
            log(f"  menu items: {json.dumps(items, ensure_ascii=False)}")

            # Clicar em Aprovar ou Avaliar
            aprovar = pg.locator("[role='menuitem']").filter(has_text=re.compile("Aprova|Avalia|Emitir", re.I)).first
            if aprovar.count():
                box_ap = aprovar.bounding_box()
                if box_ap:
                    pg.mouse.move(box_ap['x']+box_ap['width']/2, box_ap['y']+box_ap['height']/2)
                    pg.wait_for_timeout(300)
                    pg.mouse.click(box_ap['x']+box_ap['width']/2, box_ap['y']+box_ap['height']/2)
                    pg.wait_for_timeout(2000)
                    snap(pg, "map_apos_aprovar")
                    log(f"  url apos aprovar: {pg.url}")
            else:
                pg.keyboard.press("Escape")

    pg.wait_for_timeout(1000)
    log(f"\n  Requests capturados: {json.dumps(captured, ensure_ascii=False, indent=2)}")

    # Verificar via API direta o endpoint
    endpoints_tentativa = [
        f"/api/v1/o/{ORG_ID}/records/{FORA_REC_ID}/approve",
        f"/api/v1/o/{ORG_ID}/records/{FORA_REC_ID}/emit",
        f"/api/v1/o/{ORG_ID}/records/{FORA_REC_ID}",
    ]
    for ep in endpoints_tentativa:
        r = pg.request.get(f"{BASE_URL}{ep}", headers={"Accept":"application/json"})
        log(f"  GET {ep}: {r.status}")

    ca.close(); ba.close()
