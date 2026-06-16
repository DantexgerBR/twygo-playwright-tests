# -*- coding: utf-8 -*-
"""20033 reapply v2 — esconde widget de chat, usa 'Limpar filtro', reabre Filtro,
seleciona 'qa20033flow' em Meus filtros e Aplica. Compara com estado A (4 cols data,
Impacto/Cobertura ocultas, 1 linha). Cliques escopados ao dialog chakra com force."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20033_filtro"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
NOME = "qa20033flow"
log = lambda *a: print(*a, flush=True)

HIDE_CHAT = r"""()=>{document.querySelectorAll('iframe,[class*=intercom],[id*=intercom],[class*=launcher],[class*=chat-widget],[class*=octadesk]').forEach(e=>{try{e.style.display='none';}catch(_){}});}"""

def estado(pg):
    return pg.evaluate(r"""()=>{const ths=[...document.querySelectorAll('thead th,[role=columnheader]')]
      .filter(e=>{const r=e.getBoundingClientRect();return r.left<950&&r.width>0;})
      .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean);
      return {cols:ths, rows:document.querySelectorAll('tbody tr').length};}""")

def drawer(pg):
    return pg.locator(".chakra-modal__content, [role=dialog]").last

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        url = base+f"/o/{c['org_id']}/succession_initiatives"
        pg.goto(url, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.evaluate(HIDE_CHAT)
        log("inicial:", estado(pg))
        # limpar qualquer filtro ativo
        lf = pg.get_by_role("button", name=re.compile("Limpar filtro", re.I))
        if lf.count(): lf.first.click(); pg.wait_for_timeout(1500); log("apos Limpar filtro:", estado(pg))

        # abrir Filtro e verificar drawer
        pg.get_by_role("button", name=re.compile(r"^Filtro$", re.I)).first.click(timeout=5000)
        pg.get_by_text(re.compile("Lista de filtros|Filtro r")).first.wait_for(timeout=6000)
        pg.evaluate(HIDE_CHAT); pg.wait_for_timeout(500)
        d = drawer(pg)
        log("drawer texto:", (d.inner_text(timeout=3000) or "")[:300].replace("\n"," | "))

        # expandir Meus filtros (dentro do dialog)
        d.get_by_text("Meus filtros", exact=True).first.click(force=True); pg.wait_for_timeout(1200)
        log("drawer apos Meus filtros:", (d.inner_text() or "")[:400].replace("\n"," | "))
        tw.snap(pg, PASTA, "r2-01-meus-filtros", full=True)

        # selecionar o filtro salvo
        alvo = d.get_by_text(NOME, exact=False)
        log("ocorrencias do nome no drawer:", alvo.count())
        if alvo.count():
            alvo.first.click(force=True); pg.wait_for_timeout(1200)
        tw.snap(pg, PASTA, "r2-02-selecionado", full=True)

        # aplicar
        d.get_by_role("button", name=re.compile("^Aplicar$", re.I)).first.click(force=True); pg.wait_for_timeout(2500)
        st = estado(pg); log("REAPLICADO:", st)
        tw.snap(pg, PASTA, "r2-03-reaplicado", full=True)

        impacto = any("Impacto" in x for x in st["cols"])
        cobertura = any("Cobertura" in x for x in st["cols"])
        log(f"\nEsperado fix OK: Impacto OCULTO, Cobertura OCULTA, rows=1")
        log(f"Obtido: Impacto_visivel={impacto} Cobertura_visivel={cobertura} rows={st['rows']}")
        ok = (not impacto) and (not cobertura) and st["rows"] == 1
        log("REAPLICACAO CONSISTENTE COM ESTADO A:", ok)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-500:])
        try: tw.snap(pg, PASTA, "r2-ERRO", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
