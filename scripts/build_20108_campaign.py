# -*- coding: utf-8 -*-
"""20108 build — cria campanha no ciclo 166: Identificacao(nome) + Cronograma(datas) +
Quem participa(adiciona participante). Mapeia cada aba e preenche."""
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
            try: loc.first.click(timeout=2500, force=True); pg.wait_for_timeout(1000); return True
            except Exception: pass
        pg.wait_for_timeout(700)
    return False

def dump(pg, tag):
    info = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>260};
      const inputs=[...document.querySelectorAll('input,textarea,[role=combobox]')].filter(vis).map(e=>({n:e.name||e.id||e.getAttribute('aria-label')||'',ph:e.placeholder||'',t:e.type||e.tagName}));
      const labels=[...document.querySelectorAll('label,h2,h3,p')].filter(vis).map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<45);
      const btns=[...document.querySelectorAll('button')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<26);
      return {inputs:inputs.slice(0,12), labels:[...new Set(labels)].slice(0,15), btns:[...new Set(btns)].slice(0,12)};}""")
    log(f"[{tag}] inputs:", info["inputs"]); log("  labels:", info["labels"]); log("  btns:", info["btns"])

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:42])) if r.request.method in ("POST","PUT") and "/api/" in r.url and ("campaign" in r.url.lower() or "cycle" in r.url.lower()) else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/{CID}/campaigns/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        log("url:", pg.url[-45:])
        # Identificacao
        nm = pg.locator("input[name=name]")
        if nm.count(): nm.fill("QA20108 Campanha", timeout=4000); log("nome preenchido")
        dump(pg, "identificacao")
        # Cronograma
        click_tab(pg, "Cronograma")
        dump(pg, "cronograma")
        # preenche datas se houver
        dts = pg.locator("input[type=date]")
        log("date inputs cronograma:", dts.count())
        if dts.count() >= 2:
            dts.nth(0).fill("2026-06-17"); dts.nth(1).fill("2026-09-15"); log("datas cronograma preenchidas")
        elif dts.count() == 1:
            dts.nth(0).fill("2026-09-15")
        tw.snap(pg, PASTA, "camp-cron", full=True)
        # Quem participa
        click_tab(pg, "Quem participa")
        dump(pg, "quem-participa")
        tw.snap(pg, PASTA, "camp-quem", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "camp-erro", full=True)
        except: pass
    finally:
        log("net:", net[-5:]); ctx.close(); b.close()
