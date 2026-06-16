# -*- coding: utf-8 -*-
"""20033 — abre o builder de filtro (drawer "Lista de filtros" > "+ Novo") na lista
Parâmetros (succession_initiatives, 36 linhas) e dumpa os campos do builder.
Clique escopado à região do drawer (x>1000) pra não pegar o "Novo" errado do menu."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20033_filtro"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

# clica o elemento com texto == alvo dentro da região x>xmin (drawer), via mouse real
def click_no_drawer(pg, alvo, xmin=1000):
    box = pg.evaluate(r"""(arg)=>{
      const [alvo,xmin]=arg;
      const els=[...document.querySelectorAll('a,button,div,span,p')]
        .filter(e=>{const t=(e.innerText||'').trim(); return t===alvo || t==='+ '+alvo || t==='+'+alvo;})
        .filter(e=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0&&r.left>=xmin;});
      if(!els.length) return null;
      const r=els[0].getBoundingClientRect();
      return {x:r.left+r.width/2, y:r.top+r.height/2};
    }""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); return True

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_initiatives", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.get_by_role("button", name=re.compile(r"Filtro", re.I)).first.click(timeout=5000)
        pg.wait_for_timeout(1500)
        ok = click_no_drawer(pg, "Novo")
        log("clicou +Novo no drawer:", ok)
        pg.wait_for_timeout(2500)
        # dump do builder: inputs, selects, botões, labels (região direita)
        info = pg.evaluate(r"""()=>{
          const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>900;};
          const inputs=[...document.querySelectorAll('input')].filter(vis).map(e=>({ph:e.placeholder||'',name:e.name||'',type:e.type}));
          const selects=[...document.querySelectorAll('select,[class*=select__control],[role=combobox],[class*=chakra-select]')].filter(vis).map(e=>(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,40));
          const btns=[...document.querySelectorAll('button')].filter(vis).map(e=>(e.innerText||'').trim()).filter(Boolean);
          const labels=[...document.querySelectorAll('label,h2,h3,h4,p')].filter(vis).map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<45);
          return {inputs, selects:[...new Set(selects)], btns:[...new Set(btns)], labels:[...new Set(labels)].slice(0,25)};
        }""")
        log("inputs:", info["inputs"])
        log("selects:", info["selects"])
        log("btns:", info["btns"])
        log("labels:", info["labels"])
        tw.snap(pg, PASTA, "builder-aberto", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
    finally:
        ctx.close(); b.close()
