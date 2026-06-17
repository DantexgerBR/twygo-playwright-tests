# -*- coding: utf-8 -*-
"""Recon 20108 — abre o wizard 'Novo ciclo' no 37048 e mapeia os passos/campos pra
montar ciclo->campanha->avaliacao. Tambem tenta abrir o ciclo existente pelo nome."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

def dump(pg, tag):
    info = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>250};
      const inputs=[...document.querySelectorAll('input,textarea,select')].filter(vis).map(e=>({ph:e.placeholder||'',name:e.name||'',type:e.type||e.tagName,req:e.required}));
      const labels=[...document.querySelectorAll('label,h1,h2,h3,legend')].filter(vis).map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<45);
      const btns=[...document.querySelectorAll('button,[role=button]')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean);
      return {inputs:inputs.slice(0,15), labels:[...new Set(labels)].slice(0,20), btns:[...new Set(btns)].slice(0,15)};}""")
    log(f"\n[{tag}] url={pg.url[-40:]}")
    log("  inputs:", info["inputs"]); log("  labels:", info["labels"]); log("  btns:", info["btns"])

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        # 1) abrir ciclo existente pela ROW (nao pelo texto solto)
        row = pg.locator("tbody tr").first
        if row.count():
            try:
                row.click(timeout=4000); pg.wait_for_timeout(3000); dump(pg, "ciclo-existente")
                tw.snap(pg, PASTA, "wiz-00-ciclo-existente", full=True)
            except Exception as ex: log("row click:", str(ex)[:50])
        # 2) voltar e abrir Novo ciclo
        pg.goto(base+f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000); pg.wait_for_timeout(2500); tw.dispensar_nps(pg)
        nc = pg.get_by_role("button", name=re.compile("Novo ciclo", re.I))
        if nc.count():
            nc.first.click(timeout=4000); pg.wait_for_timeout(2500); dump(pg, "novo-ciclo-wizard")
            tw.snap(pg, PASTA, "wiz-01-novo-ciclo", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "wiz-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
