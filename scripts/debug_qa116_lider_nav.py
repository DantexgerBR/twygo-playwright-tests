# -*- coding: utf-8 -*-
"""Descobrir como o lider acessa Registros e testar TC1/TC5."""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
LIDER_EMAIL    = "qaliderpuro@teste.com"
LIDER_SENHA    = "123456"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log  = lambda *a: print(*a, flush=True)

def snap(pg, nome):
    pg.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True)
    log(f"  [snap] {nome}.png")

def extrair_kpis(pg):
    return pg.evaluate("""() => {
        const labels = ['Emitidos', 'Expirados', 'Pendentes', 'Recusados'];
        const result = {};
        labels.forEach(lbl => {
            const labelEl = [...document.querySelectorAll('p, span, div')].find(e =>
                e.children.length === 0 && e.innerText.trim() === lbl
            );
            if (labelEl) {
                let card = labelEl.parentElement;
                for (let i = 0; i < 5; i++) {
                    if (!card) break;
                    const nums = [...card.querySelectorAll('p, span, h2, h3, h4')].filter(n =>
                        n !== labelEl && /^\\d+$/.test(n.innerText.trim())
                    );
                    if (nums.length) { result[lbl] = parseInt(nums[0].innerText.trim()); break; }
                    card = card.parentElement;
                }
                if (result[lbl] === undefined) result[lbl] = -1;
            } else {
                result[lbl] = -1;
            }
        });
        return result;
    }""")

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)

    # Login do lider (sem forcar admin)
    pg.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    pg.fill("#user_email", LIDER_EMAIL)
    pg.fill("#user_password", LIDER_SENHA)
    pg.click("#user_submit")
    try: pg.wait_for_load_state("networkidle", timeout=20000)
    except: pass
    pg.wait_for_timeout(2000)
    tw.dispensar_nps(pg)
    log(f"[lider] URL apos login: {pg.url}")
    snap(pg, "lider_nav_dashboard")

    # Tentar ir para /o/{ORG_ID}/events com profile=admin (gestor de turma acessa assim)
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "lider_nav_eventos_admin")
    log(f"[lider] URL apos goto admin: {pg.url}")

    # Ver a sidebar disponivel
    sidebar = pg.evaluate("""() => {
        const items = [...document.querySelectorAll('nav a, [role="navigation"] a, aside a')];
        return items.map(a => ({text: (a.innerText||'').trim().slice(0,40), href: a.href.slice(-60)})).filter(i => i.text);
    }""")
    log(f"[lider] Sidebar: {json.dumps(sidebar, ensure_ascii=False)}")

    # Tentar navegar para Registros
    urls_tentativas = [
        f"{BASE_URL}/o/{ORG_ID}/records",
        f"{BASE_URL}/o/{ORG_ID}/records?as_team_manager=true",
        f"{BASE_URL}/o/{ORG_ID}/records?profile=team_manager",
        f"{BASE_URL}/o/{ORG_ID}/records?view=team_manager",
    ]
    for url in urls_tentativas:
        pg.goto(url, wait_until="domcontentloaded", timeout=30000)
        try: pg.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        pg.wait_for_timeout(3000)
        log(f"  URL: {pg.url}")
        if "/login" not in pg.url:
            snap(pg, f"lider_records_{url.split('?')[1] if '?' in url else 'base'}")
            log(f"  Acessou! Conteudo: {pg.evaluate('() => document.body.innerText.slice(0, 200).replace(/\\n/g, \" \")')}")
            break

    ca.close(); ba.close()

# Tambem verificar como o admin ve os Registros carregados corretamente
log("\n=== Admin - KPIs carregados ===")
with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=15000)
    except: pass
    pg.wait_for_timeout(8000)  # aguardar MUITO para o JS carregar
    snap(pg, "admin_records_carregado_8s")

    kpis = extrair_kpis(pg)
    linhas = pg.locator("tbody tr").count()
    log(f"  KPIs admin (8s wait): {json.dumps(kpis, ensure_ascii=False)}")
    log(f"  Linhas: {linhas}")

    # Verificar se tem spinner ainda
    spinner = pg.evaluate("() => !!document.querySelector('[class*=\"spinner\"], svg[class*=\"spin\"]')")
    log(f"  Spinner ainda ativo: {spinner}")

    # Extrair texto completo dos KPIs
    kpi_text = pg.evaluate("""() => {
        const statEls = [...document.querySelectorAll('[class*="stat"]')];
        return statEls.map(e => e.innerText.replace(/\\n/g, ' ').trim()).filter(t => t).slice(0, 8);
    }""")
    log(f"  Stat elements: {json.dumps(kpi_text, ensure_ascii=False)}")

    ca.close(); ba.close()
