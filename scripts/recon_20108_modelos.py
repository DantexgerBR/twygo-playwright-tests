# -*- coding: utf-8 -*-
"""Recon 20108 — acha onde criar um MODELO de Avaliacao de Desempenho no 37048.
Testa rotas de Avaliacoes/assessments e dumpa botoes de criar."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

ROTAS = ["/assessments", "/performance_assessment_models", "/assessment_models",
         "/evaluations", "/performance_evaluations", "/assessment_templates"]

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        for path in ROTAS:
            url = base+f"/o/{c['org_id']}{path}"
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=20000); pg.wait_for_timeout(2000)
            except Exception as ex:
                log(f"[{path}] goto erro {str(ex)[:30]}"); continue
            existe = "doesn't exist" not in pg.content()[:4000] and "404" not in pg.title()
            heads = pg.evaluate(r"""()=>[...document.querySelectorAll('h1,h2,h3')].map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<50).slice(0,3)""")
            btns = pg.evaluate(r"""()=>[...document.querySelectorAll('button,a')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/criar|adicionar|nova|novo|modelo|\+/i.test(t)&&t.length<30).slice(0,6)""")
            log(f"[{path}] existe={existe} url={pg.url[-30:]} heads={heads} btns={[*dict.fromkeys(btns)]}")
            if existe and heads and "doesn't" not in str(heads):
                tw.snap(pg, PASTA, "modelos-"+re.sub(r'\W+','_',path)[-14:])
        # tambem: menu Questionarios (submenu Avaliacoes)
        log("\n--- via menu Questionarios > Avaliacoes ---")
        pg.goto(base+f"/o/{c['org_id']}/events?profile=admin", wait_until="domcontentloaded", timeout=20000); pg.wait_for_timeout(2000)
        av = pg.get_by_role("link", name=re.compile("^Avalia", re.I))
        log("link Avaliacoes no menu:", av.count())
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
