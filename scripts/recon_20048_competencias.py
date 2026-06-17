# -*- coding: utf-8 -*-
"""20048 recon — dashboard de Competencias (Skills) no 37048. Procura: filtros
(area/gestor/funcao), botoes de export (Excel/PDF/imagem), e indicadores clicaveis
(drill-down). Tenta varias rotas."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20048_competencias"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

ROTAS = ["/organization_chart_competencies"]

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        achou = False
        for path in ROTAS:
            pg.goto(base+f"/o/{c['org_id']}{path}", wait_until="domcontentloaded", timeout=20000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
            ok = "doesn't exist" not in pg.content()[:4000]
            head = pg.evaluate(r"""()=>[...document.querySelectorAll('h1,h2,[role=tab]')].map(e=>(e.innerText||'').trim()).filter(t=>/compet|dashboard|matriz|versatil/i.test(t)).slice(0,5)""")
            log(f"[{path}] ok={ok} url={pg.url[-30:]} head={head}")
            if ok and head: achou = True; break
        if not achou:
            log("nenhuma rota direta; tentando via menu Skills>Competencias")
            pg.goto(base+f"/o/{c['org_id']}/events?profile=admin", wait_until="domcontentloaded", timeout=20000); pg.wait_for_timeout(2000)
            comp = pg.get_by_role("link", name=re.compile("Compet", re.I))
            if comp.count(): comp.first.click(timeout=4000); pg.wait_for_timeout(3000); log("via menu ->", pg.url[-35:])
        pg.wait_for_timeout(2000)
        # analisa a tela
        info = pg.evaluate(r"""()=>{const txt=document.body.innerText;
          const filtros=[...document.querySelectorAll('button,label,[role=combobox],select')].map(e=>(e.innerText||e.getAttribute('aria-label')||'').trim()).filter(t=>/filtr|[aá]rea|gestor|fun[cç][aã]o/i.test(t)).slice(0,10);
          const export_=[...document.querySelectorAll('button,a')].map(e=>(e.innerText||'').trim()).filter(t=>/export|extrair|excel|pdf|imagem|download|baixar|csv/i.test(t)).slice(0,8);
          const abas=[...document.querySelectorAll('[role=tab]')].map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,6);
          const cards=[...document.querySelectorAll('h2,h3')].map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<45).slice(0,12);
          return {filtros:[...new Set(filtros)], export_:[...new Set(export_)], abas, cards:[...new Set(cards)]};}""")
        log("\nabas:", info["abas"])
        log("cards/widgets:", info["cards"])
        log("FILTROS (area/gestor/funcao):", info["filtros"])
        log("EXPORT:", info["export_"])
        tw.snap(pg, PASTA, "01-dashboard", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
