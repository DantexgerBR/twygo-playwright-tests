# -*- coding: utf-8 -*-
"""20108 build — cria campanha completa no ciclo 166: nome + 4 datas + participante.
Clica 'Definir participantes', escolhe um usuario, Criar campanha."""
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
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:45])) if r.request.method in ("POST","PUT") and "/api/" in r.url and "campaign" in r.url.lower() else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/{CID}/campaigns/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.locator("input[name=name]").fill("QA20108 Campanha", timeout=4000)
        click_tab(pg, "Cronograma")
        for nm, val in [("start_date","2026-06-17"),("end_date","2026-09-15"),("self_start_date","2026-06-17"),("self_end_date","2026-09-15")]:
            f = pg.locator(f"input[name={nm}]")
            if f.count(): f.fill(val); log(f"  {nm}={val}")
        click_tab(pg, "Quem participa")
        pg.wait_for_timeout(800)
        # abre seletor de participantes
        pg.get_by_text("Definir participantes", exact=True).last.click(timeout=4000); pg.wait_for_timeout(1500)
        # captura opcoes (usuarios)
        opts = pg.evaluate(r"""()=>[...document.querySelectorAll('[role=option],[class*=option],li,[class*=menu] div')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()&&e.getBoundingClientRect().left>260).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t.length<50).slice(0,10)""")
        log("opcoes participante:", [*dict.fromkeys(opts)][:8])
        tw.snap(pg, PASTA, "camp2-quem-aberto", full=True)
        # tenta digitar pra buscar e escolher 1o
        ti = pg.locator("input:visible").last
        try:
            ti.type("a", delay=60); pg.wait_for_timeout(1500)
        except Exception: pass
        opts2 = pg.evaluate(r"""()=>[...document.querySelectorAll('[role=option],[class*=option],li')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()&&e.getBoundingClientRect().left>260).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t.length<50).slice(0,8)""")
        log("opcoes apos busca:", [*dict.fromkeys(opts2)][:8])
        if opts2:
            ob = pg.evaluate(r"""(alvo)=>{const e=[...document.querySelectorAll('[role=option],[class*=option],li')].find(x=>(x.innerText||'').replace(/\s+/g,' ').trim()===alvo&&x.getBoundingClientRect().left>260);if(!e)return null;const r=e.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};}""", opts2[0])
            if ob: pg.mouse.click(ob["x"], ob["y"]); pg.wait_for_timeout(1000); log("escolhi participante:", opts2[0])
        tw.snap(pg, PASTA, "camp2-participante", full=True)
        # criar campanha
        net.clear()
        pg.get_by_role("button", name=re.compile("Criar campanha", re.I)).first.click(timeout=4000); pg.wait_for_timeout(3500)
        toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,4)""")
        log("net:", net[-4:]); log("toast:", [*dict.fromkeys(toast)]); log("url:", pg.url[-45:])
        tw.snap(pg, PASTA, "camp2-criada", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "camp2-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
