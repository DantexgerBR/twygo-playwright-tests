# -*- coding: utf-8 -*-
"""Recon 20108 — em /cycles/139/campaigns clica '+ Adicionar' e mapeia o form de
criar campanha (nome, avaliacao/modelo, participantes, datas)."""
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
        pg.goto(base+f"/o/{c['org_id']}/cycles/{CID}/campaigns", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.get_by_role("button", name=re.compile("Adicionar", re.I)).first.click(timeout=5000)
        pg.wait_for_timeout(2500)
        log("url:", pg.url[-50:])
        info = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>260};
          const inputs=[...document.querySelectorAll('input,textarea,select,[role=combobox]')].filter(vis).map(e=>({k:e.placeholder||e.name||e.getAttribute('aria-label')||e.tagName,type:e.type||e.tagName}));
          const labels=[...document.querySelectorAll('label,h1,h2,h3,legend,[role=tab]')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<45);
          const btns=[...document.querySelectorAll('button')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<26&&!/Dashboard|Aprendiz|Compart|Registros|Modelos de|Usuários|Empresas|Questionários|Provas|Pesquisas|Comunid|Skills|Organo|Funções de|Compet|Análise|resposta|metros|Processos|Reposit|Dashboard geral/.test(t));
          return {inputs:inputs.slice(0,14), labels:[...new Set(labels)].slice(0,18), btns:[...new Set(btns)].slice(0,14)};}""")
        log("labels/abas:", info["labels"])
        log("inputs:", info["inputs"])
        log("btns:", info["btns"])
        tw.snap(pg, PASTA, "add-01-form", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "add-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
