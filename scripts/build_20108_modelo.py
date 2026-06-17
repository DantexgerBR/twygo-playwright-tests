# -*- coding: utf-8 -*-
"""20108 — foco no react-select 'Selecionar modelo'. Clica a coordenada do combobox,
captura opcoes (x>260, exclui nav) e seleciona. Se funcionar, salva rascunho."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
NOME = "QA20108 Avaliacao Teste"
log = lambda *a: print(*a, flush=True)

def click_tab(pg, nome):
    for _ in range(4):
        loc = pg.get_by_role("tab", name=re.compile(nome, re.I))
        if loc.count():
            try: loc.first.click(timeout=2500, force=True); pg.wait_for_timeout(1000); return True
            except Exception: pass
        pg.wait_for_timeout(700)
    return False

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.locator("input[name=name]").fill(NOME); pg.locator("input[name=planned_start_date]").fill("2026-06-17"); pg.locator("input[name=planned_end_date]").fill("2026-09-15")
        click_tab(pg, "Avalia")
        st = pg.evaluate(r"""()=>{const card=[...document.querySelectorAll('*')].find(e=>/Avaliação de Desempenho/.test(e.innerText||'')&&e.querySelector&&e.querySelector('input[type=checkbox]')&&e.getBoundingClientRect().height<140&&e.getBoundingClientRect().height>40);
          if(!card)return null;const r=card.getBoundingClientRect();return{x:r.left+30,y:r.top+30};}""")
        if st: pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(1000)
        # localiza o combobox do modelo (react-select control sob "Avaliação de Desempenho")
        cb = pg.evaluate(r"""()=>{const ctrl=[...document.querySelectorAll('[class*=select__control],[class*=css-][role],input[id*=react-select]')].map(e=>e.closest('[class*=select__control]')||e).filter(Boolean);
          // pega o primeiro select__control visivel na area do form (x>260, y entre 360 e 460)
          const c=[...document.querySelectorAll('[class*=select__control]')].find(e=>{const r=e.getBoundingClientRect();return r.left>260&&r.top>360&&r.top<470;});
          if(!c)return null;const r=c.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};}""")
        log("combobox modelo box:", cb)
        if cb: pg.mouse.click(cb["x"], cb["y"]); pg.wait_for_timeout(1200)
        else: pg.mouse.click(548, 402); pg.wait_for_timeout(1200)
        opts = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=select__option],[id*=react-select][id*=option],[role=option]')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()&&e.getBoundingClientRect().left>260).map(e=>(e.innerText||'').trim()).slice(0,12)""")
        log("opcoes modelo:", [*dict.fromkeys(opts)])
        tw.snap(pg, PASTA, "modelo-aberto", full=True)
        if opts:
            # clica a 1a opcao via coordenada
            obox = pg.evaluate(r"""(alvo)=>{const e=[...document.querySelectorAll('[class*=select__option],[role=option]')].find(x=>(x.innerText||'').trim()===alvo&&x.getBoundingClientRect().left>260);
              if(!e)return null;const r=e.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};}""", opts[0])
            if obox: pg.mouse.click(obox["x"], obox["y"]); pg.wait_for_timeout(800); log("escolhi modelo:", opts[0])
        tw.snap(pg, PASTA, "modelo-escolhido", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "modelo-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
