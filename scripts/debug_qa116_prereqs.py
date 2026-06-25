# -*- coding: utf-8 -*-
"""Debug rápido dos bloqueios do QA 1.16 v2."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"

ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
LIDER_PURO_EMAIL = "qaliderpuro@teste.com"

log = lambda *a: print(*a, flush=True)

def api_get(page, path):
    resp = page.request.get(f"{BASE_URL}{path}", headers={"Accept":"application/json"})
    try: data = resp.json()
    except: data = {}
    return resp.status, data

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # 1. Buscar professionals
    log("\n--- 1. API professionals search ---")
    for email in ["qaliderpuro@teste.com", "liderado1@teste.com", "devtestes@teste.com"]:
        st, data = api_get(pg, f"/api/v1/o/{ORG_ID}/professionals?search={email}&per_page=10")
        profs = data.get("data",{}).get("professionals",[])
        log(f"  {email}: status={st} count={len(profs)} ids={[p['id'] for p in profs]}")

    # 2. Verificar meta.total_count do endpoint /records
    log("\n--- 2. Records meta ---")
    for params in [
        "order_type=desc&per_page=1&page=1",
        "per_page=1&page=1",
        "per_page=25&page=1",
    ]:
        st, data = api_get(pg, f"/api/v1/o/{ORG_ID}/records?{params}")
        meta = data.get("data",{}).get("meta",{})
        records_count = len(data.get("data",{}).get("records",[]))
        log(f"  params={params[:40]}: status={st} meta={meta} records_in_page={records_count}")

    # 3. Verificar payload correto de POST /records
    log("\n--- 3. POST records — inspecionar campos necessários ---")
    # Tentar GET de um registro existente para ver estrutura
    st, data = api_get(pg, f"/api/v1/o/{ORG_ID}/records?per_page=1&page=1")
    recs = data.get("data",{}).get("records",[])
    if recs:
        rec = recs[0]
        log(f"  Exemplo de registro existente: {json.dumps({k:v for k,v in rec.items() if k != 'certificate_token'}, ensure_ascii=False)[:600]}")

    # Tentar POST com payload alternativo (com event_id)
    log("\n--- 4. Tentar POST /records com event_id=nil ---")
    for email in ["liderado1@teste.com"]:
        # Payload sem event_id
        p1 = {"record":{"origin":"external","content":"DEBUG-TEST-001","workload_hours":1,"workload_minutes":0},"person_email":email}
        r1 = pg.request.post(f"{BASE_URL}/api/v1/o/{ORG_ID}/records",
                             headers={"Accept":"application/json","Content-Type":"application/json"},
                             data=json.dumps(p1))
        log(f"  POST sem event_id: status={r1.status} body={r1.text()[:200]}")

        # Payload com person_id se disponível
        st_prof, data_prof = api_get(pg, f"/api/v1/o/{ORG_ID}/professionals?search={email}&per_page=5")
        profs = data_prof.get("data",{}).get("professionals",[])
        if profs:
            pid = profs[0]["id"]
            p2 = {"record":{"origin":"external","content":"DEBUG-TEST-002","workload_hours":1,"workload_minutes":0,"person_id":pid},"person_email":email}
            r2 = pg.request.post(f"{BASE_URL}/api/v1/o/{ORG_ID}/records",
                                 headers={"Accept":"application/json","Content-Type":"application/json"},
                                 data=json.dumps(p2))
            log(f"  POST com person_id={pid}: status={r2.status} body={r2.text()[:200]}")

    # 5. Verificar se qaliderpuro existe e tem que perfis
    log("\n--- 5. Verificar qaliderpuro@teste.com ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users?search=qaliderpuro", wait_until="domcontentloaded", timeout=15000)
    pg.wait_for_timeout(2000)
    body = pg.locator("body").inner_text()
    log(f"  body snippet: {body[:300]}")

    # Tentar clicar no usuário para ver detalhes
    link = pg.locator("a:has-text('QALider')").first
    if link.count():
        link.click()
        pg.wait_for_timeout(2000)
        log(f"  url: {pg.url}")
        log(f"  body: {pg.locator('body').inner_text()[:400]}")

    # 6. Verificar login do líder puro
    log("\n--- 6. Verificar se qaliderpuro consegue logar ---")
    bd, cd, pg_lider = tw.nova_pagina(p)
    pg_lider.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
    pg_lider.fill("#user_email", LIDER_PURO_EMAIL)
    pg_lider.fill("#user_password", "123456")
    pg_lider.click("#user_submit")
    try: pg_lider.wait_for_load_state("networkidle", timeout=15000)
    except: pass
    pg_lider.wait_for_timeout(2000)
    log(f"  URL após login: {pg_lider.url}")
    body_l = pg_lider.locator("body").inner_text()
    log(f"  body[:200]: {body_l[:200]}")

    ca.close(); ba.close()
    cd.close(); bd.close()
