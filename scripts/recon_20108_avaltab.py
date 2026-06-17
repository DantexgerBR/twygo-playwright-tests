# -*- coding: utf-8 -*-
"""Recon 20108 — clica a aba Avaliacoes via role=tab e dumpa o conteudo (ha modelo
de avaliacao configurado no ciclo 139?)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
CID = "139"
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/{CID}/edit", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        # tenta varios jeitos de clicar a aba
        clicked = False
        for trial in range(3):
            for loc in (pg.get_by_role("tab", name=re.compile("Avalia", re.I)),
                        pg.get_by_text("Avaliações", exact=True)):
                if loc.count():
                    try: loc.first.click(timeout=3000, force=True); clicked=True; break
                    except Exception: pass
            pg.wait_for_timeout(1500)
            # confere se mudou (some o campo Nome do ciclo)
            ident = pg.evaluate("()=>!!document.querySelector('input[name=name]')&&getComputedStyle(document.querySelector('input[name=name]')).display!=='none'")
            body_has_aval_ui = pg.evaluate(r"""()=>/avalia(ç|c)|modelo|autoavalia|gestor avalia|pares|adicionar avalia/i.test(document.body.innerText)""")
            log(f"trial {trial}: clicked={clicked} ainda_identificacao={ident}")
            if not ident: break
        body = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>260};
          const txt=[...document.querySelectorAll('h2,h3,h4,p,label,button,td,[class*=card]')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<60);
          return [...new Set(txt)].slice(0,30);}""")
        log("conteudo aba (top 30):")
        for t in body: log("   ", t)
        tw.snap(pg, PASTA, "avaltab-01", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "avaltab-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
