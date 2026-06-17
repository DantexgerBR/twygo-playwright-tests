# -*- coding: utf-8 -*-
"""20069 — abre o editor de pessoa (lapis) em Analise individual 19653 e inspeciona
o form: campo e-mail (obrigatorio?), botao Salvar. Depois testa salvar com e-mail
preenchido e captura validacao/Network (bug: e-mail obrigatorio nao salva)."""
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
    pg.on("response", lambda r: posts.append((r.request.method, r.status, r.url)) if r.request.method in ("POST","PUT","PATCH") and "/api/" in r.url else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_people_analysis", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        # clicar o lapis (ultimo botao/svg clicavel da 1a linha, x grande)
        box = pg.evaluate(r"""()=>{const tr=document.querySelector('tbody tr');if(!tr)return null;
          const cands=[...tr.querySelectorAll('button,a,svg,[role=button]')].filter(e=>e.getBoundingClientRect().width>0);
          const e=cands[cands.length-1]; if(!e)return null; const r=e.getBoundingClientRect();
          return {x:r.left+r.width/2,y:r.top+r.height/2};}""")
        if box: pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(2500)
        tw.snap(pg, PASTA, "10-editor-aberto", full=True)
        form = pg.evaluate(r"""()=>{const inputs=[...document.querySelectorAll('input,textarea')].filter(e=>e.offsetParent!==null).map(e=>({ph:e.placeholder||'',name:e.name||'',type:e.type,req:e.required||e.getAttribute('aria-required')==='true',val:(e.value||'').slice(0,25)}));
          const labels=[...document.querySelectorAll('label,h2,h3,p')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim().length<35).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,20);
          const btns=[...document.querySelectorAll('button')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean);
          return {inputs, labels:[...new Set(labels)], btns:[...new Set(btns)]};}""")
        log("inputs:", form["inputs"])
        log("labels:", form["labels"])
        log("btns:", form["btns"])
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "erro", full=True)
        except: pass
    finally:
        log("POSTs:", posts[-5:]); ctx.close(); b.close()
