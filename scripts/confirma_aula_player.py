# -*- coding: utf-8 -*-
"""Confirma o conteúdo das Aulas do SQL (807992) na VISÃO DO ALUNO (player).
Abre 'Visualizar como aluno', navega pelas atividades e captura screenshots —
em especial para ver se as Aulas têm slides/vídeo ou estão vazias."""
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
    page.wait_for_timeout(2000)

    # clicar "Visualizar como aluno" (pode abrir nova aba)
    aluno = page
    try:
        with ctx.expect_page(timeout=8000) as nova:
            page.get_by_role("button", name=re.compile(r"Visualizar como aluno", re.I)).first.click(timeout=6000)
        aluno = nova.value
        print("[player] abriu em nova aba")
    except Exception:
        print("[player] mesma aba (ou botão não abriu nova)")
        page.wait_for_timeout(4000)
        aluno = ctx.pages[-1]
    aluno.wait_for_timeout(6000)
    tw.dispensar_nps(aluno)
    print(f"[player] url={aluno.url}")
    tw.snap(aluno, PASTA, "70-player-inicial", full=True)

    # listar a navegação do curso (sumário de atividades)
    nav = aluno.evaluate(
        """()=>[...document.querySelectorAll('a,button,li,[role=button]')]
            .filter(e=>e.offsetParent!==null)
            .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim())
            .filter(t=>/SQL|Modelagem|Conceitos|Consultas|Introdução|Aula|Página/i.test(t))
            .slice(0,20)"""
    )
    print(f"[player] itens do curso: {nav}")

    # tentar abrir cada atividade do sumário e capturar
    for i, alvo in enumerate(["Introdução ao SQL", "Principais Conceitos", "Consultas Básicas"]):
        try:
            el = aluno.get_by_text(re.compile(alvo, re.I)).first
            if el.count():
                el.click(timeout=6000, force=True)
                aluno.wait_for_timeout(6000)
                tw.dispensar_nps(aluno)
                txt = aluno.evaluate("()=>document.body.innerText.replace(/\\s+/g,' ').length")
                print(f"[player] '{alvo}': conteúdo visível ~{txt} ch")
                tw.snap(aluno, PASTA, f"71-player-{i}-{re.sub(r'[^a-z]+','',alvo.lower())[:10]}", full=True)
        except Exception as e:
            print(f"[player] '{alvo}': {e}")

    ctx.close(); browser.close()
