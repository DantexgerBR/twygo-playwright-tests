# -*- coding: utf-8 -*-
"""Debug B — payload correto POST /records e como buscar user IDs."""
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

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # A. Inspecionar fields disponíveis capturando network ao criar registro pela UI
    #    Navegar para /records/new e capturar o que o form manda
    network_reqs = []
    pg.on("request", lambda r: network_reqs.append({
        "method": r.method,
        "url": r.url.split("twygoead.com")[-1][:80],
        "post": r.post_data[:400] if r.post_data else None,
    }) if r.method in ("POST","PUT","PATCH") and "/api/" in r.url else None)

    log("\n--- A. Tentar /records/new para capturar payload ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=20000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "debug_records_new")
    log(f"  URL: {pg.url}")
    log(f"  body[:300]: {pg.locator('body').inner_text()[:300]}")

    # B. Buscar usuários pela página admin (não via API)
    log("\n--- B. Buscar user IDs via página admin ---")
    for email in ["liderado1@teste.com", "qaliderpuro@teste.com", "devtestes@teste.com"]:
        pg.goto(f"{BASE_URL}/o/{ORG_ID}/users?search={email.split('@')[0]}", wait_until="domcontentloaded", timeout=15000)
        pg.wait_for_timeout(2000)
        hrefs = [a.get_attribute("href") for a in pg.locator("a[href*='/users/']").all()[:5]]
        ids = [re.search(r"/users/(\d+)", h).group(1) for h in hrefs if h and re.search(r"/users/(\d+)", h)]
        log(f"  {email}: hrefs={hrefs[:3]} ids={ids}")

    # C. Total de registros — formato correto
    log("\n--- C. Inspecionar response completo de /records ---")
    resp = pg.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1", headers={"Accept":"application/json"})
    try:
        rdata = resp.json()
        log(f"  status={resp.status}")
        log(f"  keys top-level: {list(rdata.keys())}")
        log(f"  keys data: {list(rdata.get('data',{}).keys())}")
        meta = rdata.get("data",{}).get("meta",{})
        log(f"  meta: {meta}")
        # Tentar campos alternativos
        for k in ["total", "total_count", "count", "total_records", "pagination"]:
            v = rdata.get("data",{}).get(k)
            if v is not None:
                log(f"  data.{k}: {v}")
        # headers de paginação
        log(f"  response headers Total: {resp.headers.get('x-total','n/a')} x-total-count: {resp.headers.get('x-total-count','n/a')}")
    except Exception as e:
        log(f"  erro: {e}")

    # D. Verificar registro existente — campos completos
    log("\n--- D. GET /records/{id} — campos completos ---")
    resp2 = pg.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/records/44280004", headers={"Accept":"application/json"})
    if resp2.status == 200:
        rec = resp2.json().get("data",{}).get("record",{})
        log(f"  campos: {list(rec.keys())}")
        log(f"  event_id: {rec.get('event_id','N/A')}")
        log(f"  event: {rec.get('event','N/A')}")

    # E. Tentar POST com todos os campos do registro existente (sem conteúdo fixo)
    log("\n--- E. POST /records com payload replicado ---")
    # Usar o payload exato do registro 44280004 como modelo
    if resp2.status == 200:
        rec_model = resp2.json().get("data",{}).get("record",{})
        payload_test = {
            "record": {
                "origin": "external",
                "content": "DEBUG-TEST-003",
                "workload_hours": 1,
                "workload_minutes": 0,
                "situation": "pending",
                "certificate_situation": "pending",
            },
            "person_email": "liderado1@teste.com",
        }
        if "event_id" in rec_model and rec_model["event_id"]:
            payload_test["record"]["event_id"] = rec_model["event_id"]
        r_test = pg.request.post(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/records",
            headers={"Accept":"application/json","Content-Type":"application/json"},
            data=json.dumps(payload_test),
        )
        log(f"  POST status={r_test.status} body={r_test.text()[:300]}")

    # F. Verificar qaliderpuro — tentar definir senha via admin UI
    log("\n--- F. Verificar/corrigir senha qaliderpuro ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users?search=qaliderpuro", wait_until="domcontentloaded", timeout=15000)
    pg.wait_for_timeout(2000)
    body_u = pg.locator("body").inner_text()
    log(f"  users page body: {body_u[:400]}")
    snap(pg, "debug_qaliderpuro_users")

    # Pegar href do usuário
    hrefs = [a.get_attribute("href") for a in pg.locator("a[href*='/users/']").all()[:5]]
    ids = [re.search(r"/users/(\d+)", h).group(1) for h in hrefs if h and re.search(r"/users/(\d+)", h)]
    log(f"  qaliderpuro ids encontrados: {ids}")

    if ids:
        uid = ids[0]
        pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{uid}/edit", wait_until="domcontentloaded", timeout=15000)
        pg.wait_for_timeout(2000)
        snap(pg, "debug_qaliderpuro_edit")
        body_edit = pg.locator("body").inner_text()
        log(f"  edit body[:200]: {body_edit[:200]}")
        # Definir senha
        pwd_inp = pg.locator("input[name='professional[password]']")
        if pwd_inp.count():
            pwd_inp.first.fill("123456")
            pwd_conf = pg.locator("input[name='professional[password_confirmation]']")
            if pwd_conf.count():
                pwd_conf.first.fill("123456")
            pg.get_by_role("button", name=__import__('re').compile(r"^Salvar$", __import__('re').I)).first.click(timeout=5000)
            pg.wait_for_timeout(2000)
            log(f"  Senha definida. URL: {pg.url}")
            snap(pg, "debug_qaliderpuro_senha_salva")

    ca.close(); ba.close()
