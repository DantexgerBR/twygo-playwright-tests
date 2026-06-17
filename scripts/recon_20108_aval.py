# -*- coding: utf-8 -*-
"""Recon 20108 — abre o editar do ciclo 139 e o passo 'Avaliacoes' pra ver se ja ha
modelo de avaliacao configurado (senao precisa criar)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
CID = "139"
log = lambda *a: print(*a, flush=True)

def click_txt(pg, alvo):
    box = pg.evaluate(r"""(al)=>{const els=[...document.querySelectorAll('[role=tab],button,a,div,span')]
      .filter(e=>{const t=(e.innerText||'').replace(/\s+/g,' ').trim();return t===al})
      .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>260});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();
      return{x:r.left+r.width/2,y:r.top+r.height/2}}""", alvo)
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(800); return True

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        for path in (f"/o/{c['org_id']}/cycles/{CID}/edit", f"/o/{c['org_id']}/cycles/{CID}/identification"):
            pg.goto(base+path, wait_until="domcontentloaded", timeout=25000); pg.wait_for_timeout(2500)
            if "doesn't exist" not in pg.content()[:5000] and "/cycles" in pg.url:
                log("edit url ok:", pg.url[-45:]); break
        tw.dispensar_nps(pg); pg.wait_for_timeout(1500)
        # ir pro passo Avaliacoes
        click_txt(pg, "Avaliações"); pg.wait_for_timeout(1500)
        info = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>260};
          const heads=[...document.querySelectorAll('h1,h2,h3,[role=tab]')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<45).slice(0,12);
          const txt=document.body.innerText;
          const semaval=/nenhuma avalia|adicione uma avalia|sem avalia|n[aã]o h[aá]/i.test(txt);
          const btns=[...document.querySelectorAll('button')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/avalia|adicionar|modelo|selec|nova|criar|\+/i.test(t)).slice(0,10);
          const rows=document.querySelectorAll('tbody tr,[class*=card],[class*=item]').length;
          return {heads, semaval, btns:[...new Set(btns)], rows};}""")
        log("heads/abas:", info["heads"])
        log("sem avaliacao?:", info["semaval"], "| rows/cards:", info["rows"])
        log("btns avaliacao:", info["btns"])
        tw.snap(pg, PASTA, "aval-01", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "aval-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
