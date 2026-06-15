# -*- coding: utf-8 -*-
"""Abre o curso SQL (807992) na VISÃO DO ALUNO e captura o conteúdo real gerado
(texto + screenshots), navegando pelas atividades/slides. É a forma fiel de
avaliar a qualidade do que a IA gerou."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qualidade_ia_sql"
CURSO = "807992"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)

    # abrir a visão do aluno direto pela rota do conteúdo
    for rota in [f"/e/{CURSO}/learning", f"/e/{CURSO}", f"/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"]:
        page.goto(f"{c['base_url']}{rota}", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(5000)
        tw.dispensar_nps(page)
        print(f"[rota {rota}] url={page.url}")
        if "/edit" in rota:
            # clicar Visualizar como aluno
            try:
                page.get_by_role("button", name=re.compile(r"Visualizar como aluno", re.I)).first.click(timeout=6000)
                page.wait_for_timeout(6000)
                if len(ctx.pages) > 1:
                    page = ctx.pages[-1]
                    page.wait_for_timeout(4000)
            except Exception as e:
                print(f"  [visualizar como aluno] {e}")
        tw.dispensar_nps(page)
        corpo = page.evaluate("()=>document.body.innerText.replace(/\\s+/g,' ')")
        if len(corpo) > 200 and "Não há conteúdo" not in corpo[:200]:
            break

    tw.snap(page, PASTA, "40-aluno-inicial", full=True)
    print(f"\n[aluno] url final: {page.url}")
    corpo = page.evaluate("()=>document.body.innerText.replace(/\\s+/g,' ')")
    print(f"[aluno] corpo({len(corpo)} ch): {corpo[:600]}")

    # listar itens de navegação do conteúdo (atividades/slides)
    itens = page.evaluate(
        """()=>[...document.querySelectorAll('a,button,li,[role=button],[role=tab]')]
            .filter(e=>e.offsetParent!==null)
            .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim())
            .filter(t=>t && t.length>3 && t.length<80).slice(0,40)"""
    )
    print(f"\n[aluno] itens navegáveis: {itens}")

    ctx.close(); browser.close()
