# -*- coding: utf-8 -*-
"""19948 — 'Gerenciar campanhas' tem SUBMENU. Abre kebab -> pai -> item do submenu
-> campanhas -> aba Sessões de calibração. Captura 500. Headless."""
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
        page.get_by_text("more_vert", exact=True).first.click(timeout=6000); page.wait_for_timeout(1200)
        # hover + click no pai "Gerenciar campanhas" pra abrir submenu
        pai = page.get_by_role("menuitem", name=re.compile(r"Gerenciar campanh", re.I)).first
        pai.hover(); page.wait_for_timeout(800)
        pai.click(timeout=5000); page.wait_for_timeout(1500)
        # enumerar TODOS os menuitems agora (pai + submenu)
        mis = page.get_by_role("menuitem")
        itens = [mis.nth(i).inner_text().replace("\n"," ").strip() for i in range(mis.count())]
        log("[menu] itens (pai+submenu):", itens)
        tw.snap(page, PASTA, "ct3-01-submenu")
        # clicar o item de submenu que navega (último 'Gerenciar campanhas' ou outro do submenu)
        alvos = [mis.nth(i) for i in range(mis.count()) if re.search(r"campanh|calibra|sess", mis.nth(i).inner_text(), re.I)]
        clicou = None
        # preferir o ÚLTIMO 'Gerenciar campanhas' (submenu)
        for loc in reversed(alvos):
            try:
                if loc.is_visible():
                    txt = loc.inner_text().replace("\n"," ").strip()
                    loc.click(timeout=4000); clicou = txt; break
            except Exception: pass
        log("[menu] cliquei submenu:", clicou)
        page.wait_for_timeout(4500); tw.dispensar_nps(page)
        log("[campanhas] url:", page.url)
        tw.snap(page, PASTA, "ct3-02-campanhas", full=True)
        # tabs na tela de campanhas
        tabs = [page.get_by_role("tab").nth(i).inner_text().replace("\n"," ").strip() for i in range(page.get_by_role("tab").count())]
        log("[campanhas] tabs:", tabs)
        # achar a aba/sub-aba 'Sessões de calibração'
        ab = page.get_by_role("tab", name=re.compile(r"Sess[õo]es de calibra", re.I)).first
        if not ab.count(): ab = page.get_by_text(re.compile(r"Sess[õo]es de calibra", re.I))
        cnt = ab.count()
        log("[aba] Sessões de calibração matches:", cnt)
        if cnt:
            for i in range(cnt):
                try:
                    el = ab.nth(i) if cnt>1 else ab.first
                    if el.is_visible(): el.click(timeout=5000); break
                except Exception: pass
            page.wait_for_timeout(7000); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "ct3-03-sessoes-calibracao", full=True)
        corpo = page.evaluate("()=>document.body.innerText")
        erro = bool(re.search(r"erro interno|erro 500|Internal Server|algo deu errado|n[ãa]o foi poss[íi]vel|tente novamente", corpo, re.I))
        log("[calibracao] tela de erro?", erro)
        log("[calibracao] corpo[:160]:", corpo[:160].replace("\n"," | "))
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-600:])
        try: tw.snap(page, PASTA, "ct3-erro", full=True)
        except Exception: pass
    finally:
        log("\n== perf_calibration_sessions =="); [log(f"  {s} {u}") for s,u in calib[-15:]]
        log("== 500s =="); [log(f"  {s} {u}") for s,u in net500[-15:]]
        c500 = any(s>=500 for s,_ in calib) or any("calibration" in u.lower() and s>=500 for s,u in net500)
        log(f"\n=> 19948: calib_calls={len(calib)} | 500_calibracao={c500}")
        ctx.close(); browser.close()
