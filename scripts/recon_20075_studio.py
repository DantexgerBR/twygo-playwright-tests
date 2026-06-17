# -*- coding: utf-8 -*-
"""20075 recon — abre o conteudo 807533 no Novo Estudio (org 37061, tab=studio) e
inspeciona: tipo da atividade (Aula?), input de roteiro/narrador, roteiros de slide.
DEV: na Aula o roteiro e por slide (lista de roteiros), nao narrator_script."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20075_narrator"
c = tw.cfg("NOVOEST"); base = c["base_url"].rstrip("/")
CID = "807533"
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        url = base+f"/o/{c['org_id']}/contents/{CID}/edit?tab=studio"
        pg.goto(url, wait_until="domcontentloaded", timeout=35000); tw.dispensar_nps(pg); pg.wait_for_timeout(4000)
        log("url:", pg.url[-55:])
        info = pg.evaluate(r"""()=>{const txt=document.body.innerText;
          const tipo=(txt.match(/Aula|V[ií]deo|Quiz|P[aá]gina|Player/g)||[]).slice(0,5);
          const heads=[...document.querySelectorAll('h1,h2,h3,[role=tab]')].map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<40).slice(0,12);
          const roteiroLabels=[...document.querySelectorAll('label,p,span,h3,h4')].map(e=>(e.innerText||'').trim()).filter(t=>/roteiro|narrador|narra|script|slide/i.test(t)).slice(0,10);
          const editors=[...document.querySelectorAll('textarea,[contenteditable=true],[class*=editor i]')].filter(e=>e.offsetParent!==null).map(e=>({tag:e.tagName,len:(e.innerText||e.value||'').length,prev:(e.innerText||e.value||'').slice(0,50)}));
          return {tipo:[...new Set(tipo)], heads:[...new Set(heads)], roteiroLabels:[...new Set(roteiroLabels)], editors:editors.slice(0,8)};}""")
        log("tipo detectado:", info["tipo"])
        log("heads/abas:", info["heads"])
        log("labels roteiro/narrador:", info["roteiroLabels"])
        log("editores (texto):");
        for e in info["editors"]: log("   ", e)
        tw.snap(pg, PASTA, "01-studio-807533", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
