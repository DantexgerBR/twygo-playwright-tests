# -*- coding: utf-8 -*-
"""Recon 20026 — entender abas do editor e persistência de última aba."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20026_kebab_editar"
CURSO = "807533"
c = tw.cfg("NOVOEST")
EDIT = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit"
LISTAGEM = f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin"

JS_TABS = (
    "()=>Array.from(document.querySelectorAll('[role=tab]')).map(t=>({"
    "txt:(t.innerText||'').replace(/\\s+/g,' ').trim(),"
    "sel:t.getAttribute('aria-selected')}))"
)

def estado(page, rotulo):
    page.wait_for_timeout(1500)
    tabs = page.evaluate(JS_TABS)
    ativa = next((t["txt"] for t in tabs if t["sel"] == "true"), None)
    print(f"[{rotulo}] url={page.url}")
    print(f"   abas={[t['txt'] for t in tabs]}")
    print(f"   ATIVA={ativa}")
    return ativa

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1500, height=900)
    tw.login(page, c)

    # 1) abrir ?tab=studio e esperar carregar de verdade
    page.goto(f"{EDIT}?tab=studio", wait_until="domcontentloaded", timeout=45000)
    tw.dispensar_nps(page)
    # espera o editor renderizar abas
    for _ in range(20):
        if page.locator("[role=tab]").count() > 0:
            break
        page.wait_for_timeout(1000)
    ativa_studio = estado(page, "abriu ?tab=studio")
    tw.snap(page, PASTA, "r-01-tab-studio")

    # também procurar especificamente texto Estúdio / Atividades em qualquer lugar
    tem_estudio = page.get_by_text(re.compile(r"Est.dio", re.I)).count()
    print(f"   ocorrencias texto 'Estúdio' na página: {tem_estudio}")

    # 2) clicar numa aba diferente pra fixar last_tab (ex.: Acesso), depois reabrir
    try:
        page.get_by_role("tab", name=re.compile(r"^Acesso$", re.I)).first.click(timeout=5000)
        page.wait_for_timeout(3500)
        estado(page, "cliquei aba Acesso")
        tw.snap(page, PASTA, "r-02-tab-acesso")
    except Exception as e:
        print(f"[clique Acesso] {e}")

    # 3) sair e reabrir SEM tab -> deve cair na última (Acesso)
    page.goto(LISTAGEM, wait_until="domcontentloaded", timeout=45000); page.wait_for_timeout(2500)
    page.goto(EDIT, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
    for _ in range(20):
        if page.locator("[role=tab]").count() > 0: break
        page.wait_for_timeout(1000)
    ativa_reabre = estado(page, "reabri SEM ?tab (espera ultima=Acesso)")
    tw.snap(page, PASTA, "r-03-reabertura")

    print(f"\n=> studio_ativa={ativa_studio} | reabertura={ativa_reabre}")
    ctx.close(); browser.close()
