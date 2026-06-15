# -*- coding: utf-8 -*-
"""Captura o conteúdo gerado do curso SQL (807992): clica cada atividade, lê o
preview, e abre a Aula 1.1 pra ver os slides. Diagnóstico de como extrair."""
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
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio",
              wait_until="domcontentloaded", timeout=45000)
    tw.dispensar_nps(page)
    page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
    page.wait_for_timeout(3000)

    cards = page.locator('[data-test-id^="creation-studio-activity-card-"]')
    n = cards.count()
    print(f"[studio] {n} cards de atividade")
    for i in range(n):
        card = cards.nth(i)
        titulo = card.inner_text().replace("\n", " | ")[:80]
        try:
            card.scroll_into_view_if_needed()
            card.click(timeout=6000, force=True)
            page.wait_for_timeout(3500)
        except Exception as e:
            print(f"  [{i}] erro ao clicar: {e}"); continue
        # texto do preview (painel direito)
        preview = page.evaluate(
            """()=>{
                const cont=document.querySelector('[data-test-id=creation-studio-preview]')
                  || document.querySelector('main');
                return cont? (cont.innerText||'').replace(/\\s+/g,' ').trim() : '';
            }"""
        )
        print(f"\n[card {i}] {titulo}\n  PREVIEW({len(preview)} ch): {preview[:300]}")
        tw.snap(page, PASTA, f"30-preview-card{i}")

    # tentar "Visualizar como aluno"
    try:
        page.get_by_role("button", name=re.compile(r"Visualizar como aluno", re.I)).first.click(timeout=6000)
        page.wait_for_timeout(5000)
        # pode abrir nova aba
        if len(ctx.pages) > 1:
            aluno = ctx.pages[-1]
            aluno.wait_for_timeout(4000)
            tw.snap(aluno, PASTA, "31-visao-aluno")
            txt = aluno.evaluate("()=>document.body.innerText.replace(/\\s+/g,' ').slice(0,600)")
            print(f"\n[visão aluno] {txt[:400]}")
        else:
            tw.snap(page, PASTA, "31-visao-aluno")
            txt = page.evaluate("()=>document.body.innerText.replace(/\\s+/g,' ').slice(0,600)")
            print(f"\n[visão aluno (mesma aba)] {txt[:400]}")
    except Exception as e:
        print(f"[visão aluno] erro: {e}")

    ctx.close(); browser.close()
