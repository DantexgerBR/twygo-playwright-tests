# -*- coding: utf-8 -*-
"""20108 build — cria ciclo c/ Desempenho+modelo, inspeciona a aba Etapas e tenta
'Salvar e programar'. Determina se o 500 e por Etapas faltando ou bug real."""
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
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:42])) if r.request.method in ("POST","PUT") and "/api/" in r.url and "cycle" in r.url.lower() else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.locator("input[name=name]").fill(NOME); pg.locator("input[name=planned_start_date]").fill("2026-06-17"); pg.locator("input[name=planned_end_date]").fill("2026-09-15")
        click_tab(pg, "Avalia")
        st = pg.evaluate(r"""()=>{const card=[...document.querySelectorAll('*')].find(e=>/Avaliação de Desempenho/.test(e.innerText||'')&&e.querySelector&&e.querySelector('input[type=checkbox]')&&e.getBoundingClientRect().height<140&&e.getBoundingClientRect().height>40);if(!card)return null;const r=card.getBoundingClientRect();return{x:r.left+30,y:r.top+30};}""")
        if st: pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(1000)
        mb = pg.evaluate(r"""()=>{const c=[...document.querySelectorAll('[class*=select__control]')].find(e=>{const r=e.getBoundingClientRect();return r.left>260&&r.top>360&&r.top<480});if(!c)return null;const r=c.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};}""")
        if mb: pg.mouse.click(mb["x"], mb["y"]); pg.wait_for_timeout(1500)
        srch = pg.get_by_placeholder(re.compile("Buscar modelo", re.I))
        if srch.count(): srch.first.fill("QA20108"); pg.wait_for_timeout(1200)
        res = pg.get_by_text(re.compile("QA20108 Modelo Desempenho", re.I))
        if res.count(): res.first.click(timeout=4000, force=True); pg.wait_for_timeout(1000)
        # ---- aba Etapas ----
        click_tab(pg, "Etapas")
        et = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>260};
          const txt=[...document.querySelectorAll('h2,h3,h4,p,label,button,[role=switch],input')].filter(vis).map(e=>(e.innerText||e.getAttribute('aria-label')||e.name||e.type||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<45);
          const checks=[...document.querySelectorAll('input[type=checkbox],[role=switch]')].filter(vis).length;
          return {txt:[...new Set(txt)].slice(0,25), checks};}""")
        log("ETAPAS txt:", et["txt"]); log("ETAPAS checks/switches:", et["checks"])
        tw.snap(pg, PASTA, "etapas-01", full=True)
        # tenta Salvar e programar
        net.clear()
        sp = pg.get_by_role("button", name=re.compile("Salvar e programar", re.I))
        if sp.count(): sp.first.click(timeout=4000); pg.wait_for_timeout(3500)
        toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,4)""")
        log("net:", net[-4:]); log("toast:", [*dict.fromkeys(toast)]); log("url:", pg.url[-45:])
        tw.snap(pg, PASTA, "etapas-02-salvar", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "etapas-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
