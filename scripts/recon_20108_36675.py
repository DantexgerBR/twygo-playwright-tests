# -*- coding: utf-8 -*-
"""Recon 20108 no 36675 (principal) — confirma Desempenho acessivel (cycles) e que
/professionals/results_for_filter NAO retorna 500 (vs 37048). Lista modelos de aval."""
import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("")  # principal = 36675
org = c["org_id"]; base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        log("org principal:", org, "| base:", base[-35:])
        # cycles acessivel?
        pg.goto(base+f"/o/{org}/cycles", wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        existe = "doesn't exist" not in pg.content()[:4000]
        rows = pg.evaluate("()=>document.querySelectorAll('tbody tr').length")
        head = pg.evaluate(r"""()=>[...document.querySelectorAll('h1,h2')].map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,2)""")
        log(f"cycles: existe={existe} rows={rows} head={head}")
        # APIs chave
        for q in ["/professionals/results_for_filter?page=1", "/professionals?page=1", "/assessments?page=1"]:
            r = pg.evaluate(r"""async (arg)=>{const[org,path]=arg;try{const res=await fetch('/api/v1/o/'+org+path,{headers:{'Accept':'application/json'}});const t=await res.text();return {s:res.status, len:t.length, head:t.slice(0,140)};}catch(e){return {err:String(e)};}}""", [org, q])
            log(f"[{q}] -> {r.get('s')} len={r.get('len')} {r.get('head','')[:80]}")
        tw.snap(pg, tw.ROOT/"evidencias"/"retrabalho_20108_desempenho", "36675-cycles", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
