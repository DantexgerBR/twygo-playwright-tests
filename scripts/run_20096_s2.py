# -*- coding: utf-8 -*-
"""20096-S2 (filtro destacado) — mede o botao 'Filtro' (cor/borda/badge) ANTES e DEPOIS
de aplicar um filtro na Analise individual (19653). Se ganha destaque/badge => fix OK."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20074_20096"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)
HIDE = r"""()=>{document.querySelectorAll('iframe,[class*=intercom],[id*=intercom],[class*=launcher],[class*=octadesk]').forEach(e=>{try{e.style.display='none'}catch(_){}})}"""

def estilo_filtro(pg):
    return pg.evaluate(r"""()=>{const b=[...document.querySelectorAll('button')].find(e=>/filtro/i.test(e.innerText||'')&&e.getBoundingClientRect().top<300&&e.getBoundingClientRect().left>900);
      if(!b)return null;const cs=getComputedStyle(b);
      const badge=b.querySelector('[class*=badge i],[class*=count i],.chakra-badge')?.innerText||'';
      return {bg:cs.backgroundColor,border:cs.borderColor,color:cs.color,badge,txt:(b.innerText||'').replace(/\s+/g,' ').trim()};}""")

def click_txt(pg, alvo, xmin=950):
    box = pg.evaluate(r"""(a)=>{const[al,xm]=a;const els=[...document.querySelectorAll('a,button,div,span,p,label')].filter(e=>{const t=(e.innerText||'').trim();return t===al||t==='+ '+al}).filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>=xm});if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2}}""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(500); return True

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_people_analysis", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000); pg.evaluate(HIDE)
        antes = estilo_filtro(pg); log("Filtro ANTES:", antes)
        tw.snap(pg, PASTA, "s2-01-antes", full=True)
        # abre drawer Filtro e aplica um filtro qualquer (Novo -> 1a coluna -> Aplicar)
        pg.get_by_role("button", name=re.compile(r"Filtro", re.I)).first.click(timeout=5000); pg.wait_for_timeout(1500); pg.evaluate(HIDE)
        click_txt(pg, "Novo"); pg.wait_for_timeout(1800)
        # tenta aplicar direto (filtro de coluna pode ter default) ou so Aplicar
        click_txt(pg, "Aplicar"); pg.wait_for_timeout(2500)
        depois = estilo_filtro(pg); log("Filtro DEPOIS:", depois)
        tw.snap(pg, PASTA, "s2-02-depois", full=True)
        if antes and depois:
            mudou = (antes["bg"]!=depois["bg"]) or (antes["border"]!=depois["border"]) or (depois["badge"] and depois["badge"]!=antes["badge"])
            log("\nBotao Filtro mudou de estado (destacado)?", mudou)
            log("  badge depois:", depois["badge"])
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "s2-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
