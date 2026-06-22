# -*- coding: utf-8 -*-
"""Recon do lote no 19653 (MIGR/evertongambeta admin): Continuidade (Dashboard geral,
Ações de resposta com dados?), e disponibilidade de módulos. Headless."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_lote_19653"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        # módulos no menu
        pg.goto(base + f"/o/{c['org_id']}/events?tab=events&profile=admin", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        mods = pg.evaluate(r"""()=>[...document.querySelectorAll('a')].map(a=>({t:(a.innerText||'').replace(/\s+/g,' ').trim(),h:a.getAttribute('href')||''})).filter(x=>/continuidade|desenvolv|desempenh|sucess|a[çc][õo]es|dashboard.geral|feedback|skills|fun[çc]/i.test(x.t+x.h)).slice(0,15)""")
        log("[menu] módulos:", [(m['t'][:25],m['h']) for m in mods])
        # Continuidade: Dashboard geral
        for path,nome in [(f"/o/{c['org_id']}/succession_dashboard","dashboard_geral"),(f"/o/{c['org_id']}/succession_actions","acoes"),(f"/o/{c['org_id']}/succession_individual_analysis","analise")]:
            try:
                pg.goto(base+path, wait_until="domcontentloaded", timeout=15000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
                txt=pg.evaluate("()=>document.body.innerText")
                bad=bool(re.search(r"não existe|doesn't exist",txt[:120],re.I))
                vazio=bool(re.search(r"N[ãa]o h[áa] dados|nenhum",txt,re.I))
                log(f"  [{nome}] {path} -> bad={bad} vazio={vazio} url={pg.url[-30:]}")
                tw.snap(pg, PASTA, f"recon-{nome}")
            except Exception as e: log(f"  [{nome}] {str(e)[:40]}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
