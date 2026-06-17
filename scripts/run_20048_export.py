# -*- coding: utf-8 -*-
"""20048 final — no dashboard de Competencias (37048) clica 'Extrair dados' e ve o que
acontece (download? escolha de formato Excel/PDF/imagem?). Reconfirma ausencia de
filtros area/gestor/funcao. Tenta drill-down (clicar indicador)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20048_competencias"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    downloads = []
    pg.on("download", lambda d: downloads.append(d.suggested_filename))
    try:
        pg.goto(base+f"/o/{c['org_id']}/organization_chart_competencies", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(4000)
        # reconfirma filtros no topo
        filtros = pg.evaluate(r"""()=>{const top=[...document.querySelectorAll('select,[class*=select__control],[role=combobox],button,label')].filter(e=>{const r=e.getBoundingClientRect();return r.top>120&&r.top<330&&r.left>300&&r.width>50});
          return top.map(e=>(e.innerText||e.getAttribute('aria-label')||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<35);}""")
        log("controles topo (filtros?):", [*dict.fromkeys(filtros)])
        # clica 'Extrair dados' do 1o widget
        ex = pg.get_by_role("button", name=re.compile("Extrair dados", re.I))
        log("Extrair dados count:", ex.count())
        if ex.count():
            ex.first.click(timeout=4000); pg.wait_for_timeout(2500)
            # apareceu modal de formato? ou baixou?
            fmt = pg.evaluate(r"""()=>{const opts=[...document.querySelectorAll('[role=menuitem],button,a,li,label')].filter(e=>e.offsetParent!==null&&/excel|xlsx|pdf|imagem|png|csv|planilha|formato/i.test(e.innerText||'')).map(e=>(e.innerText||'').trim());
              const modalTxt=(document.querySelector('.chakra-modal__content,[role=dialog]')||{}).innerText||'';
              return {opts:[...new Set(opts)].slice(0,8), modalTxt:modalTxt.slice(0,200)};}""")
            log("formatos/opcoes export:", fmt["opts"])
            log("modal export txt:", fmt["modalTxt"].replace("\n"," | ")[:160])
            log("downloads:", downloads)
            tw.snap(pg, PASTA, "export-01", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "export-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
