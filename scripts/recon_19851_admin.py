# -*- coding: utf-8 -*-
"""19851 baseline (admin) — abre 'Adicionar acao' em Continuidade>Acoes de resposta no
19653 e verifica se 'Funcao vinculada' e 'Iniciativa' populam (vs vazias do bug)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

def opcoes_dropdown(pg, label):
    # clica o select sob o label e captura opcoes
    box = pg.evaluate(r"""(label)=>{const labs=[...document.querySelectorAll('label,p,span')].filter(e=>(e.innerText||'').trim().startsWith(label)&&e.getBoundingClientRect().left>900);
      if(!labs.length)return null;const l=labs[0];const r=l.getBoundingClientRect();
      // o controle do select fica logo abaixo do label
      return {x:r.left+120,y:r.bottom+22};}""", label)
    if not box: return None
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(1000)
    opts = pg.evaluate(r"""()=>[...document.querySelectorAll('[role=option],[class*=option],li,[class*=menu] [class*=item]')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()&&e.getBoundingClientRect().left>900).map(e=>(e.innerText||'').trim()).slice(0,12)""")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
    return [*dict.fromkeys(opts)]

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_actions", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.get_by_role("button", name=re.compile("Adicionar", re.I)).first.click(timeout=5000); pg.wait_for_timeout(2000)
        tw.snap(pg, PASTA, "admin-01-drawer", full=True)
        # dump labels do drawer
        labels = pg.evaluate(r"""()=>[...document.querySelectorAll('label,h2,h3,p')].filter(e=>e.offsetParent!==null&&e.getBoundingClientRect().left>900).map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<40).slice(0,12)""")
        log("labels drawer:", [*dict.fromkeys(labels)])
        fn = opcoes_dropdown(pg, "Função vinculada")
        log("Função vinculada opcoes:", fn)
        ini = opcoes_dropdown(pg, "Iniciativa")
        log("Iniciativa opcoes:", ini)
        log("\nADMIN popula? Funcao:", bool(fn), "Iniciativa:", bool(ini))
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "admin-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
