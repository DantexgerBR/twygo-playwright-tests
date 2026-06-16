# -*- coding: utf-8 -*-
"""20033 probe — abre builder, clica o combobox de valor (Iniciativa) e dumpa opções;
expande "Colunas para exibir" e "Salvar filtro" e dumpa seus controles."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20033_filtro"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

def click_txt_drawer(pg, alvo, xmin=1000):
    box = pg.evaluate(r"""(arg)=>{const [alvo,xmin]=arg;
      const els=[...document.querySelectorAll('a,button,div,span,p,h2,h3,h4')]
        .filter(e=>{const t=(e.innerText||'').trim();return t===alvo||t==='+ '+alvo||t==='+'+alvo;})
        .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=xmin;});
      if(!els.length)return null;const r=els[0].getBoundingClientRect();
      return {x:r.left+r.width/2,y:r.top+r.height/2};}""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); return True

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_initiatives", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.get_by_role("button", name=re.compile(r"Filtro", re.I)).first.click(timeout=5000); pg.wait_for_timeout(1200)
        click_txt_drawer(pg, "Novo"); pg.wait_for_timeout(2000)

        # clica o combobox de valor (a caixa com chevron sob "Iniciativa", x~1220 y~228)
        pg.mouse.click(1220, 228); pg.wait_for_timeout(1200)
        opts = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0;};
          return [...document.querySelectorAll('[role=option],[class*=option],li,[class*=menu] div')]
            .filter(vis).map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<50).slice(0,15);}""")
        log("opcoes combobox valor:", [*dict.fromkeys(opts)][:12])
        tw.snap(pg, PASTA, "probe-combobox", full=True)

        # fecha menu, expande "Colunas para exibir"
        pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
        click_txt_drawer(pg, "Colunas para exibir"); pg.wait_for_timeout(800)
        cols = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>900;};
          return [...document.querySelectorAll('label,[class*=checkbox]')].filter(vis).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,20);}""")
        log("colunas p/ exibir:", [*dict.fromkeys(cols)])

        click_txt_drawer(pg, "Salvar filtro"); pg.wait_for_timeout(800)
        sv = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>900;};
          return {inputs:[...document.querySelectorAll('input[type=text]')].filter(vis).map(e=>e.placeholder||e.name||'(text)'),
                  btns:[...document.querySelectorAll('button')].filter(vis).map(e=>(e.innerText||'').trim()).filter(Boolean)};}""")
        log("salvar-filtro inputs:", sv["inputs"]); log("btns:", [*dict.fromkeys(sv["btns"])])
        tw.snap(pg, PASTA, "probe-salvar", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
    finally:
        ctx.close(); b.close()
