# -*- coding: utf-8 -*-
"""20108 build passo 1b — cria ciclo, habilita Avaliacao de Desempenho, SELECIONA o
modelo no dropdown, salva rascunho. Verifica criacao."""
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
        for loc in (pg.get_by_role("tab", name=re.compile(nome, re.I)), pg.get_by_text(nome, exact=True)):
            if loc.count():
                try: loc.first.click(timeout=2500, force=True); pg.wait_for_timeout(1000); return True
                except Exception: pass
        pg.wait_for_timeout(700)
    return False

def click_xy_text(pg, alvo, xmin=260):
    box = pg.evaluate(r"""(a)=>{const[al,xm]=a;const els=[...document.querySelectorAll('div,span,p,li,[role=option]')]
      .filter(e=>{const t=(e.innerText||'').replace(/\s+/g,' ').trim();return t===al})
      .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=xm});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();
      return{x:r.left+r.width/2,y:r.top+r.height/2}}""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(600); return True

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:45])) if r.request.method in ("POST","PUT","PATCH") and "/api/" in r.url and "cycle" in r.url.lower() else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.locator("input[name=name]").fill(NOME, timeout=4000)
        pg.locator("input[name=planned_start_date]").fill("2026-06-17", timeout=4000)
        pg.locator("input[name=planned_end_date]").fill("2026-09-15", timeout=4000)
        click_tab(pg, "Avalia")
        # marca Desempenho
        st = pg.evaluate(r"""()=>{const card=[...document.querySelectorAll('*')].find(e=>/Avaliação de Desempenho/.test(e.innerText||'')&&e.querySelector&&e.querySelector('input[type=checkbox]')&&e.getBoundingClientRect().height<140&&e.getBoundingClientRect().height>40);
          if(!card)return null;const r=card.getBoundingClientRect();return{x:r.left+30,y:r.top+30};}""")
        if st: pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(1000)
        # abre dropdown "Selecionar modelo"
        click_xy_text(pg, "Selecionar modelo"); pg.wait_for_timeout(1000)
        opts = pg.evaluate(r"""()=>[...document.querySelectorAll('[role=option],[class*=option],li')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()).map(e=>(e.innerText||'').trim()).slice(0,12)""")
        log("modelos disponiveis:", [*dict.fromkeys(opts)])
        # escolhe o 1o modelo
        if opts:
            click_xy_text(pg, opts[0]); pg.wait_for_timeout(800)
            log("modelo escolhido:", opts[0])
        tw.snap(pg, PASTA, "b1b-01-modelo", full=True)
        # salvar rascunho
        net.clear()
        sr = pg.get_by_role("button", name=re.compile("Salvar como rascunho|Salvar rascunho", re.I))
        if sr.count(): sr.first.click(timeout=4000); pg.wait_for_timeout(3500)
        log("net:", net[-4:], "| url:", pg.url[-45:])
        ok = any(s in (200,201) for _,s,_ in net) or "/cycles/" in pg.url and "/new" not in pg.url
        log("CRIOU CICLO:", ok)
        tw.snap(pg, PASTA, "b1b-02-salvo", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "b1b-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
