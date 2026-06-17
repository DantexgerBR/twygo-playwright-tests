# -*- coding: utf-8 -*-
"""20074 (tooltip nos badges de status) + 20096 S1 (titulos negrito) no Dashboard
geral do 19653 (agora com dados reais). Mede font-weight + tag + contexto de cada
titulo (pra descartar artefato) e faz hover nos badges de status."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20074_20096"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

TITULOS = ['Risco atual','Projeção em 6 meses','Projeção em 12 meses','Projeção de risco',
           'Áreas com maior risco','Funções com maior risco','Mapa de risco de saída']

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_dashboards", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(4000)
        tw.snap(pg, PASTA, "00-dashboard", full=True)

        # 20096 S1 — medir titulo: pega o elemento de MENOR area cujo innerText == titulo (a folha)
        log("=== 20096 S1 — font-weight dos titulos ===")
        med = pg.evaluate(r"""(titulos)=>titulos.map(t=>{
          const cands=[...document.querySelectorAll('h1,h2,h3,h4,h5,p,span,div')]
            .filter(e=>(e.innerText||'').trim()===t&&e.getBoundingClientRect().width>0);
          if(!cands.length)return{t,fw:'(nao achou)'};
          cands.sort((a,b)=>(a.offsetWidth*a.offsetHeight)-(b.offsetWidth*b.offsetHeight));
          const e=cands[0];const cs=getComputedStyle(e);
          return{t,fw:cs.fontWeight,tag:e.tagName,fs:cs.fontSize,cls:(e.className||'').toString().slice(0,30)};})""", TITULOS)
        for x in med: log(f"   {x['t']:24} fw={x.get('fw'):>4} tag={x.get('tag')} fs={x.get('fs')} cls={x.get('cls','')}")

        # 20074 — badges de status (Alto/Médio/Baixo/Crítico): hover e captura tooltip
        log("\n=== 20074 — tooltip nos badges de status ===")
        badges = pg.evaluate(r"""()=>[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&/^(Baixo|M[ée]dio|Alto|Cr[íi]tico)$/i.test((e.innerText||'').trim())&&e.getBoundingClientRect().width>0).map((e,i)=>{const r=e.getBoundingClientRect();return{i,txt:e.innerText.trim(),x:r.left+r.width/2,y:r.top+r.height/2,title:e.getAttribute('title')||e.closest('[title]')?.getAttribute('title')||'',aria:e.getAttribute('aria-label')||''}}).slice(0,5)""")
        log(f"   badges encontrados: {[(x['txt'],x['title'],x['aria']) for x in badges]}")
        achou_tooltip = False
        for bd in badges[:3]:
            pg.mouse.move(bd["x"], bd["y"]); pg.wait_for_timeout(1300)
            tip = pg.evaluate(r"""()=>[...document.querySelectorAll('[role=tooltip],[class*=tooltip i],[class*=Tooltip],.chakra-tooltip')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()).map(e=>e.innerText.trim()).slice(0,3)""")
            log(f"   hover '{bd['txt']}' (title='{bd['title']}') -> tooltip={tip}")
            if tip or bd["title"] or bd["aria"]: achou_tooltip = True
            tw.snap(pg, PASTA, f"20074-hover-{bd['txt']}")
        log(f"\n20074 tem tooltip/title/aria nos status: {achou_tooltip}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "erro")
        except: pass
    finally:
        ctx.close(); b.close()
