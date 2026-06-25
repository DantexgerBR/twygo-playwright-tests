# -*- coding: utf-8 -*-
"""Debug AC — alterar senha via API com token de auth da sessao + hover antes de click."""
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
    ba, ca, pg = tw.nova_pagina(p, headless=False, slow_mo=300)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    # Tentar obter o token Bearer da API
    api_token_info = pg.evaluate("""() => {
        // Procurar em localStorage, sessionStorage, cookies, Redux store, etc.
        const ls_keys = Object.keys(localStorage);
        const ss_keys = Object.keys(sessionStorage);
        const token_from_ls = ls_keys.filter(k => k.toLowerCase().includes('token') || k.toLowerCase().includes('auth'));
        const meta_csrf = document.querySelector('meta[name=csrf-token]')?.content;
        return {
            ls_token_keys: token_from_ls.map(k => ({k, v: localStorage.getItem(k)?.slice(0,50)})),
            ss_count: ss_keys.length,
            meta_csrf: meta_csrf?.slice(0,30),
        };
    }""")
    log(f"  API token info: {json.dumps(api_token_info, ensure_ascii=False)}")

    # Tentar fazer o click com hover antes
    linha = pg.locator("tr").filter(has_text="qaliderpuro@teste.com").first
    kebab = linha.locator("button").last
    kebab_box = kebab.bounding_box()

    # Hover no kebab antes de clicar
    pg.mouse.move(kebab_box['x'] + kebab_box['width']/2, kebab_box['y'] + kebab_box['height']/2)
    pg.wait_for_timeout(300)
    pg.mouse.click(kebab_box['x'] + kebab_box['width']/2, kebab_box['y'] + kebab_box['height']/2)
    pg.wait_for_timeout(1000)

    # Obter posicao de Alterar senha
    alterar_box = pg.evaluate("""() => {
        const items = [...document.querySelectorAll('[role="menuitem"]')];
        const item = items.find(el => el.innerText && el.innerText.includes('Alterar senha'));
        return item ? item.getBoundingClientRect() : null;
    }""")
    log(f"  Alterar senha box: {alterar_box}")

    if alterar_box:
        cx = alterar_box['x'] + alterar_box['width']/2
        cy = alterar_box['y'] + alterar_box['height']/2

        # Hover sobre o item antes de clicar
        pg.mouse.move(cx, cy)
        pg.wait_for_timeout(300)
        snap(pg, "ac_hover_alterar_senha")

        # Clicar
        pg.mouse.click(cx, cy)
        pg.wait_for_timeout(500)
        snap(pg, "ac_apos_click")

        # Esperar 5 segundos com snapshots
        for i in range(5):
            pg.wait_for_timeout(1000)
            # Verificar modais chakra (nao popover)
            modais = pg.evaluate("""() => {
                return [...document.querySelectorAll('.chakra-modal__content, .chakra-modal__overlay, .chakra-modal__content-container')].filter(el => {
                    const s = window.getComputedStyle(el);
                    return s.display !== 'none';
                }).map(el => ({
                    class: el.className.slice(0,60),
                    text: (el.innerText||'').slice(0,100),
                    inputs: [...el.querySelectorAll('input')].map(i => ({type:i.type,id:i.id}))
                }));
            }""")
            log(f"  [{i+1}s] modais: {modais}")
            if modais:
                snap(pg, f"ac_modal_{i+1}s")
                break

    # Tentar API de alterar senha com Authorization header
    # Primeiro obter o JWT/token do admin
    token_resp = pg.request.post(
        f"{BASE_URL}/api/v1/auth/sign_in",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        data=json.dumps({"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    )
    log(f"  Token API sign_in: {token_resp.status}")
    if token_resp.status == 200:
        token_data = token_resp.json()
        token = token_data.get("data", {}).get("token", "") or token_data.get("token", "")
        log(f"  Token: {token[:30]}...")

        # Tentar alterar senha com token
        change_resp = pg.request.fetch(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/users/{QALIDERPURO_ID}",
            method="PATCH",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
            data=json.dumps({"user": {"password": "123456", "password_confirmation": "123456"}})
        )
        log(f"  PATCH com Bearer: {change_resp.status}")
        body = change_resp.body().decode('utf-8', errors='replace')[:200]
        log(f"  body: {body}")
    else:
        body = token_resp.body().decode('utf-8', errors='replace')[:200]
        log(f"  Sign_in body: {body}")

    snap(pg, "ac_estado_final")
    pg.wait_for_timeout(3000)
    ca.close(); ba.close()
