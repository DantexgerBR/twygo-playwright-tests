# -*- coding: utf-8 -*-
"""Recon da 2ª fase: 'Concluir geração com IA' no curso 807992 (org 37061).
Mapeia se a geração de conteúdo é por atividade ou do curso todo, e o que aparece."""
import re
import sys
import time
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
    url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
    page.goto(url_studio, wait_until="domcontentloaded", timeout=45000)
    tw.dispensar_nps(page)
    page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
    page.wait_for_timeout(3000)

    # estado das atividades
    estado = page.evaluate(
        """()=>[...document.querySelectorAll('[data-test-id^="creation-studio-activity-card-"]')]
            .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).slice(0,40)"""
    )
    print("ATIVIDADES:")
    for a in estado:
        print(f"  - {a}")

    # botões de geração disponíveis
    botoes = page.evaluate(
        """()=>[...document.querySelectorAll('button')].filter(e=>e.offsetParent!==null)
            .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim())
            .filter(t=>/gera|concluir|IA|render/i.test(t))"""
    )
    print(f"\nBOTOES de geração: {botoes}")
    tw.snap(page, PASTA, "20-estudio-antes-concluir", full=True)

    # clicar em "Concluir geração com IA"
    btn = page.get_by_role("button", name=re.compile(r"Concluir geração com IA", re.I)).first
    if btn.count() and btn.is_visible():
        print("\n[ação] clicando 'Concluir geração com IA'...")
        btn.click(timeout=8000)
        page.wait_for_timeout(4000)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, "21-pos-clicar-concluir", full=True)
        # o que apareceu? modal? toast? mudou estado?
        corpo = page.evaluate("()=>document.body.innerText.replace(/\\s+/g,' ').slice(0,800)")
        print(f"[estado pós-clique] {corpo[:500]}")
        modal = page.evaluate(
            """()=>{const m=[...document.querySelectorAll('[role=dialog],[role=alertdialog],.chakra-modal__content')].find(e=>e.offsetParent!==null);
                return m?(m.innerText||'').replace(/\\s+/g,' ').slice(0,400):null;}"""
        )
        print(f"[modal?] {modal}")
    else:
        print("[ação] botão 'Concluir geração com IA' não encontrado no nível atual")

    print(f"\n[recon] url={page.url}")
    ctx.close(); browser.close()
