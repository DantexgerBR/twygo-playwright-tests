# -*- coding: utf-8 -*-
"""Recon 20108 v2 — abre kebab e clica 'Gerenciar campanhas' por COORDENADA (mouse).
Mapeia a tela de campanhas + fluxo de criar campanha/atribuir avaliacao."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

def click_txt(pg, alvo):
    box = pg.evaluate(r"""(al)=>{const els=[...document.querySelectorAll('[role=menuitem],button,a,div,span,p')]
      .filter(e=>{const t=(e.innerText||'').replace(/\s+/g,' ').trim();return t===al||t.endsWith(al)})
      .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();
      return{x:r.left+r.width/2,y:r.top+r.height/2}}""", alvo)
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(600); return True

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.locator("tbody tr").first.locator("button").last.click(timeout=4000); pg.wait_for_timeout(1200)
        ok = click_txt(pg, "Gerenciar campanhas"); log("clicou Gerenciar campanhas:", ok); pg.wait_for_timeout(3000)
        log("url:", pg.url[-55:])
        info = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>260};
          const heads=[...document.querySelectorAll('h1,h2,h3')].filter(vis).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,6);
          const btns=[...document.querySelectorAll('button')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<28&&!/Dashboard|Aprendiz|Compart|Registros|Modelos|Usu|Empresas|Question|Provas|Pesquisas|Avaliações$|Comunid|Skills|Organo|Funções de|Compet|individual|resposta|metros|Processos|Reposit/.test(t));
          const rows=document.querySelectorAll('tbody tr').length;
          return {heads, btns:[...new Set(btns)].slice(0,15), rows};}""")
        log("heads:", info["heads"], "rows:", info["rows"])
        log("btns:", info["btns"])
        tw.snap(pg, PASTA, "camp2-01", full=True)
        # criar campanha
        for alvo in ("Nova campanha","Adicionar campanha","Criar campanha","Adicionar","Nova","Criar"):
            if click_txt(pg, alvo): log("cliquei criar:", alvo); pg.wait_for_timeout(2500); break
        info2 = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>260};
          const inputs=[...document.querySelectorAll('input,textarea,[role=combobox]')].filter(vis).map(e=>(e.placeholder||e.name||e.getAttribute('aria-label')||e.tagName)).slice(0,12);
          const labels=[...document.querySelectorAll('label,h2,h3')].filter(vis).map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<42).slice(0,15);
          return {inputs:[...new Set(inputs)], labels:[...new Set(labels)]};}""")
        log("\n[criar] inputs:", info2["inputs"]); log("  labels:", info2["labels"])
        tw.snap(pg, PASTA, "camp2-02-criar", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "camp2-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
