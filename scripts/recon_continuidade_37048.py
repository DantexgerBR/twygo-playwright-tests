# -*- coding: utf-8 -*-
"""Recon Continuidade e Sucessão no 37048: achar o módulo + Ações de resposta +
drawer Adicionar. Mede cor do select Estratégia (19983) e estado dos selects (19851)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_continuidade_sucessao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        # sidebar: itens ligados a sucessão/continuidade/risco/ações
        pg.goto(base + f"/o/{c['org_id']}/events?tab=events&profile=admin", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        menu = pg.evaluate(r"""()=>[...document.querySelectorAll('a')].map(a=>({t:(a.innerText||'').replace(/\s+/g,' ').trim(),h:a.getAttribute('href')||''})).filter(x=>x.h && /sucess|continuidade|risco|a[çc][õo]es|sucession|talent/i.test(x.t+x.h))""")
        log("[sidebar] candidatos:", menu)
        # tentar URLs prováveis do módulo
        for path in (f"/o/{c['org_id']}/succession", f"/o/{c['org_id']}/continuity", f"/o/{c['org_id']}/risk_actions", f"/o/{c['org_id']}/response_actions", f"/o/{c['org_id']}/sucessao"):
            try:
                pg.goto(base+path, wait_until="domcontentloaded", timeout=12000); pg.wait_for_timeout(1500)
                txt = pg.evaluate("()=>document.body.innerText.slice(0,80)")
                bad = "não existe" in txt.lower() or "doesn't exist" in txt.lower()
                log(f"  [{path}] -> {pg.url[-40:]} bad={bad} | {txt[:50].strip()!r}")
            except Exception as e: log(f"  [{path}] {str(e)[:40]}")
        tw.snap(pg, PASTA, "recon-sidebar")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
    finally:
        ctx.close(); b.close()
