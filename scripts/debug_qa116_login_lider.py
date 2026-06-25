# -*- coding: utf-8 -*-
"""Testar login do lider e resetar senha se necessario."""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
LIDER_EMAIL    = "qaliderpuro@teste.com"
LIDER_ID       = 4299626

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log  = lambda *a: print(*a, flush=True)

def snap(pg, nome):
    pg.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True)
    log(f"  [snap] {nome}.png")

# Testar senhas candidatas para o lider
senhas_candidatas = ["twygoqa2026", "123456", "Twygo@2024", "twygo123", "qaliderpuro", "Twygo2024"]

login_ok = False
senha_correta = None
for senha in senhas_candidatas:
    with tw.sync_playwright() as p:
        ba, ca, pg = tw.nova_pagina(p, slow_mo=200)
        pg.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
        pg.fill("#user_email", LIDER_EMAIL)
        pg.fill("#user_password", senha)
        pg.click("#user_submit")
        try:
            pg.wait_for_load_state("networkidle", timeout=15000)
        except:
            pass
        pg.wait_for_timeout(2000)
        if "/users/login" not in pg.url and "/login" not in pg.url:
            login_ok = True
            senha_correta = senha
            log(f"  [lider] Login OK com senha: {senha}")
            snap(pg, "lider_login_ok")
            ca.close(); ba.close()
            break
        else:
            log(f"  [lider] Senha '{senha}' FALHOU (url: {pg.url})")
            ca.close(); ba.close()

if not login_ok:
    log("\n  Nenhuma senha funcionou. Resetando via admin (alterar senha)...")
    with tw.sync_playwright() as p:
        ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
        tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                       "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
        log("[admin] logado para reset")

        # Navegar para alterar senha via URL direta de edit
        pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDER_ID}/edit",
                wait_until="domcontentloaded", timeout=30000)
        try: pg.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        pg.wait_for_timeout(2000)

        # Scrollar para encontrar campos de senha
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pg.wait_for_timeout(1000)
        snap(pg, "lider_edit_bottom")

        # Ver todos os campos
        todos_inputs = pg.evaluate("""() => {
            return [...document.querySelectorAll('input')].map(i => ({
                type: i.type, id: i.id, name: i.name,
                placeholder: i.placeholder, visible: i.getBoundingClientRect().height > 0
            }));
        }""")
        log(f"  Todos inputs: {json.dumps(todos_inputs, ensure_ascii=False)}")

        # Tentar via API de reset de senha
        csrf = pg.evaluate("() => document.querySelector('meta[name=csrf-token]')?.content || ''")

        # Tentar alterar senha via PATCH/PUT na API
        endpoints_senha = [
            f"/api/v1/o/{ORG_ID}/users/{LIDER_ID}",
            f"/o/{ORG_ID}/users/{LIDER_ID}",
        ]
        for ep in endpoints_senha:
            r = pg.request.patch(
                f"{BASE_URL}{ep}",
                headers={"Accept": "application/json", "Content-Type": "application/json",
                          "X-CSRF-Token": csrf},
                data=json.dumps({"user": {"password": "123456", "password_confirmation": "123456"}})
            )
            log(f"  PATCH {ep}: {r.status}")
            if r.status in (200, 204):
                log("  Senha alterada via API!")
                senha_correta = "123456"
                break

        # Se nenhuma API funcionou, tentar via formulario HTML
        if not senha_correta:
            # Procurar campo senha scrollando
            pg.evaluate("window.scrollTo(0, 0)")
            pg.wait_for_timeout(500)
            # Procurar o botao de alterar senha no formulario
            snap(pg, "lider_edit_form")

        ca.close(); ba.close()

log(f"\nSenha correta do lider: {senha_correta}")
