# -*- coding: utf-8 -*-
"""Recon 20108 — clica '+ Adicionar' em Avaliacoes (37048) e mapeia o form de criar
avaliacao: nome, usable_in (Desempenho?), como adicionar secao/questao."""
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
        pg.goto(base+f"/o/{c['org_id']}/assessments", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.get_by_role("button", name=re.compile("Adicionar", re.I)).first.click(timeout=5000)
        pg.wait_for_timeout(2500)
        log("url:", pg.url[-45:])
        info = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>260};
          const inputs=[...document.querySelectorAll('input,textarea,select')].filter(vis).map(e=>({name:e.name||'',id:e.id||'',ph:e.placeholder||'',type:e.type||e.tagName}));
          const labels=[...document.querySelectorAll('label,h1,h2,h3,legend,[role=tab]')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<45);
          const radios=[...document.querySelectorAll('input[type=radio],input[type=checkbox]')].filter(vis).map(e=>({id:e.id||'',name:e.name||'',val:e.value||''}));
          const btns=[...document.querySelectorAll('button')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<26);
          return {inputs:inputs.slice(0,16), labels:[...new Set(labels)].slice(0,18), radios:radios.slice(0,10), btns:[...new Set(btns)].slice(0,14)};}""")
        log("labels:", info["labels"])
        log("inputs:", info["inputs"])
        log("radios/checks:", info["radios"])
        log("btns:", info["btns"])
        # procura especificamente o controle usable_in / "onde usar"
        usable = pg.evaluate(r"""()=>{const t=document.body.innerText;const m=t.match(/.{0,30}(desempenho|compet[eê]ncia|onde.{0,10}usar|tipo de avalia|finalidade).{0,30}/gi);return m?[...new Set(m)].slice(0,6):[]}""")
        log("contexto usable_in:", usable)
        tw.snap(pg, PASTA, "addaval-01", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "addaval-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
