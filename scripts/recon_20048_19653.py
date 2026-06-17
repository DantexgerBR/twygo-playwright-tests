# -*- coding: utf-8 -*-
"""20048 — dashboard de Competencias no 19653 (tem organograma/funcoes). Procura
filtros (area/gestor/funcao), export por widget, e testa drill-down (clicar indicador)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20048_competencias"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/organization_chart_competencies", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(4000)
        info = pg.evaluate(r"""()=>{
          // filtros: combobox/select/botoes com area/gestor/funcao no topo (acima dos widgets)
          const filtros=[...document.querySelectorAll('button,[role=combobox],select,label,[class*=select__control]')].map(e=>(e.innerText||e.getAttribute('aria-label')||e.getAttribute('placeholder')||'').replace(/\s+/g,' ').trim()).filter(t=>/^.{0,3}(filtr|[aá]rea|gestor|fun[cç][aã]o|per[ií]odo|n[ií]vel)/i.test(t)&&t.length<30).slice(0,12);
          const export_=[...document.querySelectorAll('button,a')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/export|extrair|excel|pdf|imagem|baixar|csv/i.test(t)).slice(0,10);
          const widgets=[...document.querySelectorAll('h2,h3')].map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<45&&!/perfil|suporte|admin/i.test(t)).slice(0,12);
          const semdados=/sem dados|nenhuma [aá]rea|n[aã]o h[aá] dados/i.test(document.body.innerText);
          // clicaveis com cursor pointer nos numeros/indicadores
          return {filtros:[...new Set(filtros)], export_n:export_.length, export_:[...new Set(export_)], widgets:[...new Set(widgets)], semdados};}""")
        log("widgets:", info["widgets"])
        log("FILTROS topo:", info["filtros"])
        log("EXPORT (qtd):", info["export_n"], info["export_"][:4])
        log("sem dados?:", info["semdados"])
        tw.snap(pg, PASTA, "19653-dashboard", full=True)
        # drill-down: tenta clicar o "Extrair dados" do 1o widget pra ver formato
        ex = pg.get_by_role("button", name=re.compile("Extrair dados", re.I))
        log("\nbotoes Extrair dados:", ex.count())
        if ex.count():
            ex.first.click(timeout=4000); pg.wait_for_timeout(1500)
            fmt = pg.evaluate(r"""()=>[...document.querySelectorAll('[role=menuitem],button,a,li')].filter(e=>e.offsetParent!==null&&/excel|pdf|imagem|csv|png|xlsx|planilha|baixar/i.test(e.innerText||'')).map(e=>(e.innerText||'').trim()).slice(0,8)""")
            log("formatos de export oferecidos:", [*dict.fromkeys(fmt)])
            tw.snap(pg, PASTA, "19653-export-formatos", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "19653-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
