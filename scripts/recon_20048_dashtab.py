# -*- coding: utf-8 -*-
"""20048 — aba DASHBOARD de Competencias no 19653. Verifica barra de filtros
(area/gestor/funcao), export por widget e drill-down (clicar indicador/numero)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20048_competencias"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/organization_chart_competencies", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        # garante aba Dashboard (tab no conteudo: x 400-1100, topo); texto pode ter \n
        box = pg.evaluate(r"""()=>{const cands=[...document.querySelectorAll('a,button,span,div,[role=tab],p')].filter(x=>(x.innerText||'').replace(/\s+/g,' ').trim()==='Dashboard');
          const tab=cands.find(x=>{const r=x.getBoundingClientRect();return r.left>400&&r.left<1100&&r.top<360&&r.width>0&&r.width<260;});
          if(!tab)return {n:cands.length};const r=tab.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};}""")
        log("box tab Dashboard:", box)
        if box and box.get("x"): pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(2500)
        # barra de filtros: selects/combobox na area superior (y<400, x>300)
        filt = pg.evaluate(r"""()=>{const el=[...document.querySelectorAll('select,[class*=select__control],[role=combobox],button')].filter(e=>{const r=e.getBoundingClientRect();return r.top<420&&r.top>120&&r.left>300&&r.width>60});
          return el.map(e=>(e.innerText||e.getAttribute('aria-label')||e.getAttribute('placeholder')||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<35).slice(0,15);}""")
        log("controles no topo (possiveis filtros):", [*dict.fromkeys(filt)])
        temfiltro = pg.evaluate(r"""()=>/por [aá]rea|por gestor|por fun[cç][aã]o|filtrar por/i.test(document.body.innerText)""")
        log("texto menciona 'por area/gestor/funcao':", temfiltro)
        # export por widget
        ex = pg.get_by_role("button", name=re.compile("Extrair dados", re.I))
        log("Extrair dados (widgets):", ex.count())
        # widgets do dashboard
        widgets = pg.evaluate(r"""()=>[...document.querySelectorAll('h2,h3')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/evolu|cobertura|radar|fun[cç]|compet[eê]ncias (mais|menos)|aderen|s[oó]lid|deficit/i.test(t)).slice(0,10)""")
        log("widgets dashboard:", [*dict.fromkeys(widgets)])
        tw.snap(pg, PASTA, "dashtab-19653", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "dashtab-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
