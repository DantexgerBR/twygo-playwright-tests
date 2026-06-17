# -*- coding: utf-8 -*-
"""20074 inspect — verifica se a celula do nome de funcao tem ellipsis/noOfLines
(condicao de truncamento) e se ha wrapper de Tooltip chakra. Decide se 'sem tooltip'
e bug ou so porque os nomes do 19653 nao truncam."""
import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20074_20096"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_dashboards", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(4000)
        info = pg.evaluate(r"""()=>{
          const nome='Líder de Equipe de Migração de Banco de Dados';
          const e=[...document.querySelectorAll('*')].find(x=>x.children.length===0&&(x.innerText||'').trim()===nome);
          if(!e)return{achou:false};
          const cs=getComputedStyle(e);
          const trunca=e.scrollWidth>e.offsetWidth || e.scrollHeight>e.offsetHeight;
          // sobe a arvore procurando wrapper de tooltip chakra
          let tipWrap='';let n=e;for(let i=0;i<6&&n;i++){const a=(n.getAttribute&&(n.getAttribute('aria-describedby')||''))||'';const cls=(n.className||'').toString();if(/tooltip|popover/i.test(cls)||a){tipWrap=cls.slice(0,40)+' aria='+a;break;}n=n.parentElement;}
          return{achou:true, whiteSpace:cs.whiteSpace, textOverflow:cs.textOverflow, overflow:cs.overflow,
            webkitLineClamp:cs.webkitLineClamp, scrollW:e.scrollWidth, offsetW:e.offsetWidth, scrollH:e.scrollHeight, offsetH:e.offsetHeight,
            trunca, tipWrap, outer:e.outerHTML.slice(0,120)};}""")
        log("inspect funcao name:")
        for k,v in info.items(): log(f"   {k}: {v}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
