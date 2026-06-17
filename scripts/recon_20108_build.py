# -*- coding: utf-8 -*-
"""Recon 20108 build — abre o ciclo existente (QA19948 Ciclo Calibracao) no 37048 e
mapeia como criar/abrir campanha + avaliacao e como responder. Dumpa abas, botoes e
acoes do detalhe do ciclo."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        # clicar no ciclo (texto) pra abrir detalhe
        ciclo = pg.get_by_text(re.compile("Ciclo Calibracao", re.I)).first
        if ciclo.count():
            ciclo.click(timeout=4000); pg.wait_for_timeout(3000)
        log("url detalhe:", pg.url[-50:])
        info = pg.evaluate(r"""()=>{const tabs=[...document.querySelectorAll('[role=tab],button,a')].map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<30&&!/^\d+$/.test(t)).slice(0,25);
          const btns=[...document.querySelectorAll('button')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/campanha|avalia|adicionar|novo|nova|iniciar|ativar|responder|publicar|gerar|atribuir|\+/i.test(t));
          const heads=[...document.querySelectorAll('h1,h2,h3')].map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,6);
          return {tabs:[...new Set(tabs)], btns:[...new Set(btns)], heads};}""")
        log("heads:", info["heads"])
        log("tabs:", info["tabs"])
        log("btns relevantes:", info["btns"])
        tw.snap(pg, PASTA, "build-01-ciclo-detalhe", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "build-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
