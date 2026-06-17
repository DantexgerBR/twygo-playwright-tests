# -*- coding: utf-8 -*-
"""20069 v2 — clica o lapis (editar) por coordenada na 1a linha de Analise individual
19653, inspeciona o form (campo e-mail/obrigatorio + Salvar), testa salvar."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20069_email"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    posts = []
    pg.on("response", lambda r: posts.append((r.request.method, r.status, r.url[-60:])) if r.request.method in ("POST","PUT","PATCH") and "twygoead.com/api" in r.url else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_people_analysis", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        # acha o icone mais a direita da 1a linha de dados (lapis), via JS: elemento clicavel x>1380
        box = pg.evaluate(r"""()=>{
          // pega a primeira linha de dados: elemento que contem um email
          const rows=[...document.querySelectorAll('*')].filter(e=>/@/.test(e.innerText||'')&&e.getBoundingClientRect().height<90&&e.getBoundingClientRect().height>30);
          // procura icone editar (svg/path) na area direita
          const icons=[...document.querySelectorAll('svg,[class*=icon i],[role=button]')].filter(e=>{const r=e.getBoundingClientRect();return r.left>1380&&r.top>240&&r.top<320&&r.width>0;});
          if(icons.length){const r=icons[0].getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2,n:icons.length};}
          return null;}""")
        log("lapis box:", box)
        if box: pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(2500)
        else: pg.mouse.click(1449, 276); pg.wait_for_timeout(2500)
        log("url:", pg.url[-45:])
        tw.snap(pg, PASTA, "30-editor", full=True)
        form = pg.evaluate(r"""()=>{const inputs=[...document.querySelectorAll('input,textarea')].filter(e=>e.offsetParent!==null).map(e=>({ph:e.placeholder||'',name:e.name||'',type:e.type,req:e.required||e.getAttribute('aria-required')==='true',val:(e.value||'').slice(0,25)}));
          const labels=[...document.querySelectorAll('label,h2,h3')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim().length<35).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,18);
          const btns=[...document.querySelectorAll('button')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(t=>t&&!/school|Administrador|chevron|keyboard|^\d$/.test(t));
          return {inputs:inputs.slice(0,15), labels:[...new Set(labels)], btns:[...new Set(btns)]};}""")
        log("inputs:", form["inputs"])
        log("labels:", form["labels"])
        log("btns:", form["btns"])
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "erro2", full=True)
        except: pass
    finally:
        log("POSTs:", posts[-6:]); ctx.close(); b.close()
