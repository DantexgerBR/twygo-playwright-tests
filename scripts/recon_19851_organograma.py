# -*- coding: utf-8 -*-
"""19851 — recon Skills>Organograma no 19653: ve se da pra estruturar lider->liderado
+ funcao por la (bypass do save de pessoa bloqueado pelo 422-telefone)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        # organograma de skills
        for path in ("/organization_chart", "/organization_charts", "/skills/organization_chart"):
            pg.goto(base+f"/o/{c['org_id']}{path}", wait_until="domcontentloaded", timeout=20000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
            ok = "doesn't exist" not in pg.content()[:4000]
            head = pg.evaluate(r"""()=>[...document.querySelectorAll('h1,h2')].map(e=>(e.innerText||'').trim()).filter(t=>/organo|estrutura|hierarq/i.test(t)).slice(0,3)""")
            log(f"[{path}] ok={ok} url={pg.url[-30:]} head={head}")
            if ok and (head or "organization_chart" in pg.url):
                btns = pg.evaluate(r"""()=>[...document.querySelectorAll('button,a')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/adicionar|nova|novo|vincular|atribuir|gerenciar|estrutura|\+/i.test(t)&&t.length<30).slice(0,10)""")
                log("   btns:", [*dict.fromkeys(btns)])
                tw.snap(pg, PASTA, "organograma", full=True)
                break
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "organograma-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
