# -*- coding: utf-8 -*-
"""19948 — ciclo 139 Programado. Clique REAL do Playwright no kebab -> campanhas
-> aba 'Sessões de calibração'. Captura 500. Headless."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
net500, calib = [], []
def on_resp(r):
    try:
        u=r.url
        if re.search(r"calibration_session|performance_calibration", u, re.I): calib.append((r.status,u))
        if r.status>=500: net500.append((r.status,u))
    except Exception: pass
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True)
    page.on("response", on_resp)
    tw.login(page, c)
    try:
        page.goto(base + f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page); page.wait_for_timeout(3500)
        # clique REAL no kebab (único more_vert da lista = ciclo QA19948)
        kb = page.get_by_text("more_vert", exact=True).first
        kb.scroll_into_view_if_needed(); kb.click(timeout=6000)
        page.wait_for_timeout(1500)
        itens = [page.get_by_role("menuitem").nth(i).inner_text().strip() for i in range(page.get_by_role("menuitem").count())]
        log("[kebab] menuitems:", itens)
        tw.snap(page, PASTA, "ct2-01-kebab")
        # clicar Ver/Gerenciar campanhas
        mi = page.get_by_role("menuitem", name=re.compile(r"campanh", re.I)).first
        if mi.count():
            mi.click(timeout=6000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
        log("[campanhas] url:", page.url)
        tw.snap(page, PASTA, "ct2-02-campanhas", full=True)
        # abas/tabs presentes
        tabs = [page.get_by_role("tab").nth(i).inner_text().strip() for i in range(page.get_by_role("tab").count())]
        log("[campanhas] tabs:", tabs)
        # aba 'Sessões de calibração' (exato; o nome do ciclo tem 'Calibracao', cuidado)
        ab = page.get_by_role("tab", name=re.compile(r"Sess[õo]es de calibra", re.I)).first
        if not ab.count():
            ab = page.get_by_text(re.compile(r"^Sess[õo]es de calibra", re.I)).first
        log("[aba] Sessões de calibração achou:", ab.count())
        if ab.count():
            ab.click(timeout=6000); page.wait_for_timeout(7000); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "ct2-03-sessoes-calibracao", full=True)
        corpo = page.evaluate("()=>document.body.innerText")
        erro_tela = bool(re.search(r"erro interno|erro 500|Internal Server|algo deu errado|n[ãa]o foi poss[íi]vel carregar|tente novamente", corpo, re.I))
        log("[calibracao] tela de erro?", erro_tela)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-600:])
        try: tw.snap(page, PASTA, "ct2-erro", full=True)
        except Exception: pass
    finally:
        log("\n== chamadas performance_calibration_sessions =="); [log(f"  {s} {u}") for s,u in calib[-15:]]
        log("== 500s =="); [log(f"  {s} {u}") for s,u in net500[-15:]]
        c500 = any(s>=500 for s,_ in calib) or any("calibration" in u.lower() and s>=500 for s,u in net500)
        log(f"\n=> 19948: calib_calls={len(calib)} | 500_em_calibracao={c500}")
        ctx.close(); browser.close()
