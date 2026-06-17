# -*- coding: utf-8 -*-
"""20048 — checa o formato de export de um widget TABULAR (Funcoes de negocio mais
aderentes) no dashboard Competencias 37048. Grafico so deu 'Imagem'; tabela pode ter
Excel/PDF. Card pede Excel/PDF/imagem."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20048_competencias"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/organization_chart_competencies", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(4000)
        # clica o 'Extrair dados' associado a um widget tabular -> mede por coordenada
        # pega todos os 'Extrair dados' e clica o da "Funcoes de negocio mais aderentes"
        box = pg.evaluate(r"""()=>{const h=[...document.querySelectorAll('h2,h3')].find(e=>/Fun[cç][oõ]es de neg[oó]cio mais aderentes/i.test(e.innerText||''));
          if(!h)return null;const card=h.closest('div');const bt=[...card.querySelectorAll('button')].find(e=>/Extrair/i.test(e.innerText||''))||[...document.querySelectorAll('button')].find(e=>/Extrair/i.test(e.innerText||'')&&Math.abs(e.getBoundingClientRect().top-h.getBoundingClientRect().top)<40);
          if(!bt)return null;const r=bt.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};}""")
        log("box Extrair (tabular):", box)
        if box: pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(2500)
        fmt = pg.evaluate(r"""()=>{const m=document.querySelector('.chakra-modal__content,[role=dialog]');const txt=m?m.innerText:'';
          const radios=[...document.querySelectorAll('[role=dialog] label,[class*=modal] label,[role=radio]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean);
          const fmts=(txt.match(/excel|xlsx|pdf|imagem|png|csv|planilha/gi)||[]);
          return {modal:txt.slice(0,200).replace(/\n/g,' | '), radios:[...new Set(radios)].slice(0,8), fmts:[...new Set(fmts.map(f=>f.toLowerCase()))]};}""")
        log("modal:", fmt["modal"])
        log("opcoes(radios):", fmt["radios"])
        log("FORMATOS detectados:", fmt["fmts"])
        tw.snap(pg, PASTA, "export2-tabular", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "export2-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
