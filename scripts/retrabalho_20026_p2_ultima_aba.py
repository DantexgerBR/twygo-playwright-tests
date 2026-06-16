# -*- coding: utf-8 -*-
"""20026 P2 — "Editar" reabre na ÚLTIMA aba acessada (PR #10694).
Dois ciclos: fixa uma aba por clique, reabre o editor SEM ?tab e confere que
volta nela (prova que segue a última acessada, não um valor fixo)."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20026_kebab_editar"
CURSO = "807533"
c = tw.cfg("NOVOEST")
EDIT = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit"
LISTAGEM = f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin"

JS_TABS = ("()=>Array.from(document.querySelectorAll('[role=tab]')).map(t=>({"
           "txt:(t.innerText||'').replace(/\\s+/g,' ').trim(),sel:t.getAttribute('aria-selected')}))")

def esperar_abas(page):
    for _ in range(25):
        if page.locator("[role=tab]").count() > 0:
            page.wait_for_timeout(1200); return True
        page.wait_for_timeout(1000)
    return False

def aba_ativa(page):
    return next((t["txt"] for t in page.evaluate(JS_TABS) if t["sel"] == "true"), None)

def fixar_aba(page, nome_texto):
    # clica via JS na aba [role=tab] cujo innerText bate (evita scroll/overlay)
    clicou = page.evaluate(
        "(alvo)=>{const ts=Array.from(document.querySelectorAll('[role=tab]'));"
        "const t=ts.find(e=>(e.innerText||'').replace(/\\s+/g,' ').trim().toLowerCase()===alvo.toLowerCase());"
        "if(t){t.scrollIntoView({block:'center'});t.click();return true;}return false;}",
        nome_texto,
    )
    page.wait_for_timeout(4500)  # tempo pra persistir last_tab
    print(f"   (clicou '{nome_texto}'? {clicou})")
    return aba_ativa(page)

def reabrir(page):
    page.goto(LISTAGEM, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
    page.wait_for_timeout(2500)
    page.goto(EDIT, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
    esperar_abas(page)
    return aba_ativa(page)

res = {}
with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1500, height=900)
    tw.login(page, c)
    try:
        # abre editor uma vez
        page.goto(EDIT, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        esperar_abas(page)
        print(f"[inicio] aba ativa = {aba_ativa(page)}")

        # ---- ciclo 1: fixar "Atividades" (Estúdio) ----
        fix1 = fixar_aba(page, "Atividades")
        tw.snap(page, PASTA, "p2-01-fixou-atividades")
        reab1 = reabrir(page)
        tw.snap(page, PASTA, "p2-02-reabriu-deve-atividades")
        ok1 = bool(reab1 and re.search(r"Atividades", reab1, re.I))
        print(f"[ciclo1] fixei={fix1} -> reabriu={reab1} | {'OK' if ok1 else 'FALHOU'}")
        res["ciclo1_atividades"] = (ok1, f"fixei=Atividades reabriu={reab1}")

        # ---- ciclo 2: fixar "Acesso" ----
        page.goto(EDIT, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page); esperar_abas(page)
        fix2 = fixar_aba(page, "Acesso")
        tw.snap(page, PASTA, "p2-03-fixou-acesso")
        reab2 = reabrir(page)
        tw.snap(page, PASTA, "p2-04-reabriu-deve-acesso")
        ok2 = bool(reab2 and re.search(r"Acesso", reab2, re.I))
        print(f"[ciclo2] fixei={fix2} -> reabriu={reab2} | {'OK' if ok2 else 'FALHOU'}")
        res["ciclo2_acesso"] = (ok2, f"fixei=Acesso reabriu={reab2}")
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "p2-99-erro")
    finally:
        print("\n=== RESUMO 20026-P2 ===")
        for k,(ok,det) in res.items(): print(f"  {k}: {'PASSOU' if ok else 'FALHOU'} | {det}")
        ctx.close(); browser.close()
