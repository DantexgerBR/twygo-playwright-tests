# -*- coding: utf-8 -*-
"""Recon 20108 — fluxo de responder avaliacao de Desempenho no 37048. Mapeia ciclos,
avaliacoes disponiveis (Avaliacoes a preencher) e tenta abrir o responder p/ ver se
a avaliacao prossegue ate o fim (botao concluir/proximo)."""
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
        # listagem de avaliacoes (Desenvolvimento)
        for path in (f"/o/{c['org_id']}/cycles", f"/o/{c['org_id']}/performance_assessments",
                     f"/o/{c['org_id']}/team_development", f"/o/{c['org_id']}/development"):
            pg.goto(base+path, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
            url = pg.url
            txt = pg.evaluate(r"""()=>{const tabs=[...document.querySelectorAll('[role=tab],button,a')].map(e=>(e.innerText||'').trim()).filter(t=>/avalia|preench|responder|situa|9-box|times/i.test(t)).slice(0,12);
              const rows=document.querySelectorAll('tbody tr').length;
              const responder=[...document.querySelectorAll('button,a')].filter(e=>/responder/i.test(e.innerText||'')).length;
              return {tabs:[...new Set(tabs)], rows, responder};}""")
            log(f"[{path}] -> {url[-40:]} | tabs={txt['tabs']} rows={txt['rows']} responder_btns={txt['responder']}")
            tw.snap(pg, PASTA, "recon-"+re.sub(r'\W+','_',path)[-18:])
            if txt["responder"] or txt["rows"]:
                break
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "recon-erro")
        except: pass
    finally:
        ctx.close(); b.close()
