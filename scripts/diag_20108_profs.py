# -*- coding: utf-8 -*-
"""Consulta a API de profissionais do 37048 (autenticado via browser) pra ver a
contagem — confirma se a lista de participantes esta vazia."""
import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=25000); pg.wait_for_timeout(2000)
        for q in ["/professionals/results_for_filter?search_field=&search_value=&page=1",
                  "/professionals?page=1", "/professionals/results_for_filter"]:
            r = pg.evaluate(r"""async (path)=>{try{const res=await fetch('/api/v1/o/'+%s+path,{headers:{'Accept':'application/json'}});const t=await res.text();return {status:res.status, len:t.length, head:t.slice(0,300)};}catch(e){return {err:String(e)};}}""" % repr(c['org_id']), q)
            log(f"[{q[:45]}] -> {r}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
