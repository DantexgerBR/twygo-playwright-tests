# -*- coding: utf-8 -*-
"""20108 build passo 3 (completo) — cria ciclo: Identificacao + Avaliacoes(Desempenho
+modelo QA20108) + Etapas(Auto-avaliacao + Resultado final 'Calculo automatico
ponderado') -> Salvar e programar. Verifica criacao."""
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

def click_txt(pg, alvo, xmin=260):
    box = pg.evaluate(r"""(a)=>{const[al,xm]=a;const els=[...document.querySelectorAll('label,span,p,div,button')]
      .filter(e=>{const t=(e.innerText||'').replace(/\s+/g,' ').trim();return t===al})
      .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=xm});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();
      return{x:r.left+ (al.length>3? 10 : r.width/2), y:r.top+r.height/2}}""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(500); return True

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:42])) if r.request.method in ("POST","PUT") and "/api/" in r.url and "cycle" in r.url.lower() else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.locator("input[name=name]").fill(NOME); pg.locator("input[name=planned_start_date]").fill("2026-06-17"); pg.locator("input[name=planned_end_date]").fill("2026-09-15")
        # Avaliacoes
        click_tab(pg, "Avalia")
        st = pg.evaluate(r"""()=>{const card=[...document.querySelectorAll('*')].find(e=>/Avaliação de Desempenho/.test(e.innerText||'')&&e.querySelector&&e.querySelector('input[type=checkbox]')&&e.getBoundingClientRect().height<140&&e.getBoundingClientRect().height>40);if(!card)return null;const r=card.getBoundingClientRect();return{x:r.left+30,y:r.top+30};}""")
        if st: pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(1000)
        mb = pg.evaluate(r"""()=>{const c=[...document.querySelectorAll('[class*=select__control]')].find(e=>{const r=e.getBoundingClientRect();return r.left>260&&r.top>360&&r.top<480});if(!c)return null;const r=c.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};}""")
        if mb: pg.mouse.click(mb["x"], mb["y"]); pg.wait_for_timeout(1500)
        srch = pg.get_by_placeholder(re.compile("Buscar modelo", re.I))
        if srch.count(): srch.first.fill("QA20108"); pg.wait_for_timeout(1200)
        res = pg.get_by_text(re.compile("QA20108 Modelo Desempenho", re.I))
        if res.count(): res.first.click(timeout=4000, force=True); pg.wait_for_timeout(1000); log("modelo selecionado")
        # Etapas
        click_tab(pg, "Etapas")
        log("marcando Auto-avaliação:", click_txt(pg, "Auto-avaliação"))
        log("marcando Resultado:", click_txt(pg, "Cálculo automático ponderado"))
        tw.snap(pg, PASTA, "step3-01-etapas", full=True)
        # salvar e programar
        net.clear()
        sp = pg.get_by_role("button", name=re.compile("Salvar e programar", re.I))
        if sp.count(): sp.first.click(timeout=4000); pg.wait_for_timeout(4000)
        toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,4)""")
        log("net:", net[-4:]); log("toast:", [*dict.fromkeys(toast)]); log("url:", pg.url[-50:])
        ok = any(s in (200,201) for _,s,_ in net) or ("/cycles" in pg.url and "/new" not in pg.url)
        log("CICLO CRIADO:", ok)
        tw.snap(pg, PASTA, "step3-02-salvo", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "step3-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
