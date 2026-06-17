# -*- coding: utf-8 -*-
"""Caracteriza o 500 de /professionals/results_for_filter no 37048 (varios params)."""
import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("RECERT"); org = c["org_id"]; base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

QS = [
    "/professionals/results_for_filter",
    "/professionals/results_for_filter?search_field=&search_value=&page=1",
    "/professionals/results_for_filter?search_field=name&search_value=a&page=1",
    "/professionals/results_for_filter?page=1&per_page=10",
    "/professionals/results_for_filter?cycle_id=166",
]

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{org}/cycles", wait_until="domcontentloaded", timeout=25000); pg.wait_for_timeout(1500)
        for q in QS:
            r = pg.evaluate(r"""async (arg)=>{const[org,path]=arg;try{const res=await fetch('/api/v1/o/'+org+path,{headers:{'Accept':'application/json'}});const t=await res.text();return {status:res.status, head:t.slice(0,160)};}catch(e){return {err:String(e)};}}""", [org, q])
            log(f"[{q[-50:]}] -> {r.get('status')} | {r.get('head','')[:90]}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
