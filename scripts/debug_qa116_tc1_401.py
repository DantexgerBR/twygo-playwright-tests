# -*- coding: utf-8 -*-
"""Capturar a URL do 401 no TC1 (form e provedores)."""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
LIDER_EMAIL = "qaliderpuro@teste.com"
LIDER_SENHA = "123456"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
INATIVO_ID  = 4299629  # qainativo_tc4_28129

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log = lambda *a: print(*a, flush=True)


def snap(pg, nome):
    pg.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True)
    log(f"  [snap] {nome}.png")


# ==============================================================================
log("="*60)
log("Capturar 401s na sessao do lider (TC1.3 e TC1.4)")
log("="*60)

erros_form = []
erros_prov = []

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)

    # Login lider
    pg.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    pg.fill("#user_email", LIDER_EMAIL)
    pg.fill("#user_password", LIDER_SENHA)
    pg.click("#user_submit")
    try: pg.wait_for_load_state("networkidle", timeout=20000)
    except: pass
    pg.wait_for_timeout(2000)
    tw.dispensar_nps(pg)

    # Capturar TODOS os erros (4xx, 5xx) do form de adicionar
    def captura_form(resp):
        if resp.status >= 400:
            erros_form.append({
                "status": resp.status,
                "url": resp.url,
                "method": resp.request.method
            })
            log(f"  [FORM {resp.status}] {resp.request.method} {resp.url}")

    pg.on("response", captura_form)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)

    # Clicar no campo Pessoas para abrir o modal
    pessoas = pg.locator("text=Adicionar pessoas").first
    if pessoas.count():
        pessoas.click()
        pg.wait_for_timeout(2000)

    snap(pg, "tc1_401_form")
    pg.remove_listener("response", captura_form)

    log(f"\n  Erros no form: {json.dumps(erros_form, ensure_ascii=False)}")

    # Agora capturar 401s na aba Provedores
    def captura_prov(resp):
        if resp.status >= 400:
            erros_prov.append({
                "status": resp.status,
                "url": resp.url,
                "method": resp.request.method
            })
            log(f"  [PROV {resp.status}] {resp.request.method} {resp.url}")

    pg.on("response", captura_prov)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)

    # Clicar na aba Provedores
    tab = pg.locator("[role='tab'], a").filter(has_text=re.compile("Provedores?", re.I)).first
    if tab.count():
        tab.click()
        pg.wait_for_timeout(2000)
    snap(pg, "tc1_401_provedores")
    pg.remove_listener("response", captura_prov)

    log(f"\n  Erros na aba Provedores: {json.dumps(erros_prov, ensure_ascii=False)}")

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("Verificar status de qainativo_tc4_28129")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{INATIVO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "qainativo_edit")

    # Ver o status ativo/inativo
    ativo_info = pg.evaluate("""() => {
        // Verificar toggle ativo
        const toggle = document.querySelector('.chakra-switch input[type=checkbox]');
        if (toggle) return {type: 'chakra-switch', checked: toggle.checked};
        // Ver na URL ou titulo
        return {url: document.URL, title: document.title};
    }""")
    log(f"  Status qainativo: {ativo_info}")

    # Ver na lista de usuarios
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)

    busca = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca.count():
        busca.fill("qainativo")
        pg.wait_for_timeout(2000)
        snap(pg, "qainativo_lista")

        row_info = pg.evaluate("""() => {
            const rows = [...document.querySelectorAll('tbody tr')];
            return rows.map(tr => ({
                texto: tr.innerText.replace(/\\n/g,' ').slice(0, 100),
                toggle: (() => {
                    const t = tr.querySelector('.chakra-switch input');
                    return t ? t.checked : null;
                })()
            }));
        }""")
        log(f"  Rows qainativo: {json.dumps(row_info, ensure_ascii=False)}")

    ca.close(); ba.close()


# SUMARIO TC1 401
log("\n" + "="*60)
log("ANALISE TC1 401s")
log("="*60)
log(f"  401s no form (/records/new): {len(erros_form)}")
for e in erros_form:
    log(f"    {e['method']} {e['url']} -> {e['status']}")

log(f"\n  Erros na aba Provedores: {len(erros_prov)}")
for e in erros_prov:
    log(f"    {e['method']} {e['url']} -> {e['status']}")

# Analisar
form_401 = [e for e in erros_form if e['status'] == 401]
prov_erros = [e for e in erros_prov if e['status'] >= 400]

if form_401:
    log(f"\n  URL do 401 no form: {form_401[0]['url']}")
    if prov_erros:
        # Verificar se e a mesma URL ou diferente
        urls_prov = [e['url'] for e in prov_erros]
        if any(form_401[0]['url'] in u or u in form_401[0]['url'] for u in urls_prov):
            log("  MESMO endpoint: TC1.3 e TC1.4 sao o mesmo bug de autorizacao")
        else:
            log("  ENDPOINTS DIFERENTES: podem ser bugs distintos")
    else:
        log("  Provedores sem 401: TC1.4 e bug de escopo diferente (nao autorizacao)")
else:
    log("  Sem 401 no form - TC1.3 pode ser outro problema")
    if prov_erros:
        log(f"  Provedores tem erros: {prov_erros}")
    else:
        log("  Provedores sem erros 4xx tambem")
