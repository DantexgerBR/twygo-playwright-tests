# -*- coding: utf-8 -*-
"""20108 build — campanha ciclo 166. Abre 'Vincular pessoas', espera carregar, dumpa
linhas de pessoa (deteccao ampla), seleciona 1, Vincular, Criar campanha."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
CID = "166"
log = lambda *a: print(*a, flush=True)

def click_tab(pg, nome):
    for _ in range(4):
        loc = pg.get_by_role("tab", name=re.compile(nome, re.I))
        if loc.count():
            try: loc.first.click(timeout=2500, force=True); pg.wait_for_timeout(900); return True
            except Exception: pass
        pg.wait_for_timeout(700)
    return False

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    apis = []
    pg.on("response", lambda r: apis.append((r.status, r.url.split("/api/v1")[-1][:55])) if "/api/v1" in r.url and r.request.method=="GET" else None)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:45])) if r.request.method in ("POST","PUT") and "/api/" in r.url and "campaign" in r.url.lower() else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/{CID}/campaigns/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.locator("input[name=name]").fill("QA20108 Campanha")
        click_tab(pg, "Cronograma")
        for nm, val in [("start_date","2026-06-17"),("end_date","2026-09-15"),("self_start_date","2026-06-17"),("self_end_date","2026-09-15")]:
            f = pg.locator(f"input[name={nm}]")
            if f.count(): f.fill(val)
        click_tab(pg, "Quem participa"); pg.wait_for_timeout(800)
        apis.clear()
        pg.get_by_text("Definir participantes", exact=True).last.click(timeout=4000); pg.wait_for_timeout(7000)
        log("API GETs apos abrir drawer:", [a for a in apis if not any(x in a[1] for x in ("notification","feature","nps"))][-10:])
        # dump linhas do drawer (qualquer elemento com email ou nome clicavel, x>850, y>360)
        linhas = pg.evaluate(r"""()=>{const out=[];const all=[...document.querySelectorAll('*')].filter(e=>{const r=e.getBoundingClientRect();return r.left>850&&r.top>360&&r.width>100&&r.height>20&&r.height<70&&e.children.length<=4&&(e.innerText||'').trim().length>3&&(e.innerText||'').trim().length<60});
          all.forEach(e=>out.push((e.innerText||'').replace(/\s+/g,' ').trim()));return [...new Set(out)].slice(0,12);}""")
        log("linhas drawer:", linhas)
        tw.snap(pg, PASTA, "camp4-drawer", full=True)
        # tenta "Selecionar todos" (se houver poucas pessoas)
        seltodos = pg.get_by_text("Selecionar todos", exact=True)
        if seltodos.count():
            seltodos.first.click(timeout=3000); pg.wait_for_timeout(1200); log("cliquei Selecionar todos")
        sel = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]');return drw?(drw.innerText.match(/Pessoas \((\d+)/)||[])[1]||'?':'?'}""")
        log("pessoas selecionadas:", sel)
        tw.snap(pg, PASTA, "camp4-selecionados", full=True)
        vinc = pg.get_by_role("button", name=re.compile("^Vincular$", re.I))
        log("Vincular habilitado:", vinc.count() and not vinc.first.is_disabled())
        if vinc.count() and not vinc.first.is_disabled():
            vinc.first.click(timeout=4000); pg.wait_for_timeout(1500); log("Vinculei")
            net.clear()
            pg.get_by_role("button", name=re.compile("Criar campanha", re.I)).first.click(timeout=4000); pg.wait_for_timeout(3500)
            toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,4)""")
            log("net:", net[-4:]); log("toast:", [*dict.fromkeys(toast)]); log("url:", pg.url[-45:])
        tw.snap(pg, PASTA, "camp4-final", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "camp4-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
