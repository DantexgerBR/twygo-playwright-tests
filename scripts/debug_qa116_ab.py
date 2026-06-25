# -*- coding: utf-8 -*-
"""Debug AB — tentar alterar senha via API Rails Devise + investigar CSRF token."""
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
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # Obter CSRF token da sessao
    csrf = pg.evaluate("() => document.querySelector('meta[name=csrf-token]')?.content || ''")
    log(f"  CSRF token: {csrf[:20]}...")

    # Tentar diferentes endpoints de alteracao de senha
    endpoints = [
        f"/o/{ORG_ID}/users/{QALIDERPURO_ID}/password",
        f"/o/{ORG_ID}/users/{QALIDERPURO_ID}/change_password",
        f"/o/{ORG_ID}/professionals/{QALIDERPURO_ID}/change_password",
        f"/api/v1/o/{ORG_ID}/users/{QALIDERPURO_ID}/change_password",
        f"/api/v1/o/{ORG_ID}/professionals/{QALIDERPURO_ID}/password",
        f"/users/password",
    ]

    headers_json = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-CSRF-Token": csrf,
    }
    headers_form = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "X-CSRF-Token": csrf,
    }

    for ep in endpoints:
        # Tentar PATCH e PUT
        for method in ["PATCH", "PUT"]:
            try:
                resp = pg.request.fetch(
                    f"{BASE_URL}{ep}",
                    method=method,
                    headers=headers_json,
                    data=json.dumps({"password": "123456", "password_confirmation": "123456"}),
                )
                log(f"  {method} {ep} -> {resp.status}")
                if resp.status not in [404, 405, 500]:
                    body = resp.body().decode('utf-8', errors='replace')[:200]
                    log(f"    body: {body}")
            except Exception as e:
                log(f"  {method} {ep} -> erro: {e}")

    # Tentar endpoint de admin alterar senha especifico do Twygo
    # Formato: PUT /o/{org}/users/{id} com password
    resp = pg.request.fetch(
        f"{BASE_URL}/o/{ORG_ID}/users/{QALIDERPURO_ID}",
        method="PATCH",
        headers=headers_form,
        form={
            "_method": "patch",
            "authenticity_token": csrf,
            "user[password]": "123456",
            "user[password_confirmation]": "123456",
        }
    )
    log(f"  PATCH /users/{QALIDERPURO_ID} (form) -> {resp.status}")
    body = resp.body().decode('utf-8', errors='replace')[:200]
    log(f"    body: {body}")

    # Tentar via pagina de edit do user inspecionando o formulario
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{QALIDERPURO_ID}/edit", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)

    # Inspecionar todos os campos do form
    form_info = pg.evaluate("""() => {
        const form = document.querySelector('form');
        if (!form) return {error: 'no form'};
        return {
            action: form.action,
            method: form.method,
            fields: [...form.querySelectorAll('input, textarea, select')].map(el => ({
                tag: el.tagName,
                type: el.type,
                name: el.name,
                id: el.id,
                value: (el.value||'').slice(0,50),
                placeholder: el.placeholder,
            }))
        };
    }""")
    log(f"  Form edit: {json.dumps(form_info, ensure_ascii=False)[:3000]}")

    ca.close(); ba.close()
