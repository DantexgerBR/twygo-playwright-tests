# -*- coding: utf-8 -*-
"""Recon telas Continuidade no 37048: descobrir URLs do submenu (Dashboard geral,
Análise individual, Ações de resposta, Parâmetros) e capturar estado/dados."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_lote_37048"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base + f"/o/{c['org_id']}/succession_actions", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        # links do submenu Continuidade
        links = pg.evaluate(r"""()=>[...document.querySelectorAll('a')].map(a=>({t:(a.innerText||'').replace(/\s+/g,' ').trim(),h:a.getAttribute('href')||''})).filter(x=>/dashboard geral|an[áa]lise individual|a[çc][õo]es de resposta|par[âa]metros|continuidade/i.test(x.t)).slice(0,12)""")
        log("[submenu Continuidade]:", [(l['t'],l['h']) for l in links])
        # visitar cada e capturar
        seen=set()
        for l in links:
            h=l['h']
            if not h or h in seen: continue
            seen.add(h)
            try:
                pg.goto(base+h if h.startswith('/') else h, wait_until="domcontentloaded", timeout=15000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
                txt=pg.evaluate("()=>document.body.innerText")
                vazio=bool(re.search(r"N[ãa]o h[áa] dados|nenhum",txt,re.I))
                nrows=pg.evaluate("()=>document.querySelectorAll('tbody tr,[class*=row]').length")
                log(f"  [{l['t'][:22]}] {h} -> vazio={vazio} rows~{nrows}")
                tw.snap(pg, PASTA, "telas-"+re.sub(r'\W+','_',l['t'].lower())[:20])
            except Exception as e: log(f"  [{l['t'][:20]}] {str(e)[:40]}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
