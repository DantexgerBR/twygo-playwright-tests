# -*- coding: utf-8 -*-
"""Recon 20033 — fluxo de filtro nas listas Continuidade (37048). Abre Filtro,
dumpa campos + botões (Aplicar/Salvar/Limpar) em Análise individual e Parâmetros."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20033_filtro"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

def recon_filtro(pg, url, nome):
    pg.goto(url, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
    rows0 = pg.evaluate("()=>document.querySelectorAll('tbody tr,[class*=row]').length")
    fbtn = pg.get_by_role("button", name=re.compile(r"Filtro", re.I)).first
    log(f"\n[{nome}] {url[-30:]} rows={rows0} botão Filtro={fbtn.count()}")
    if fbtn.count():
        fbtn.click(timeout=5000); pg.wait_for_timeout(2000)
        campos = pg.evaluate(r"""()=>{const labels=[...document.querySelectorAll('label,p,span,h3,h4')].map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<30);
          const btns=[...document.querySelectorAll('button')].map(b=>(b.innerText||'').trim()).filter(t=>/aplicar|salvar|limpar|filtrar|fechar/i.test(t));
          const selects=[...document.querySelectorAll('select,[class*=select__control],[role=combobox]')].length;
          return {labels:labels.slice(0,20), btns:[...new Set(btns)], selects};}""")
        log(f"  campos/labels: {campos['labels']}")
        log(f"  botões filtro: {campos['btns']}")
        log(f"  selects no painel: {campos['selects']}")
        tw.snap(pg, PASTA, "filtro-"+re.sub(r'\W+','_',nome.lower())[:16], full=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        recon_filtro(pg, base+f"/o/{c['org_id']}/succession_people_analysis", "AnaliseIndividual")
        recon_filtro(pg, base+f"/o/{c['org_id']}/succession_initiatives", "Parametros")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
