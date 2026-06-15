# -*- coding: utf-8 -*-
"""Diagnóstico: por que 'Assistente de criação' some? E o SQL/git já renderizaram?"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qualidade_ia_diag"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)

    # 1) estado da página de criação com IA
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new_with_ai",
              wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(6000)
    tw.dispensar_nps(page)
    corpo = page.evaluate("()=>document.body.innerText.replace(/\\s+/g,' ')")
    tem_assistente = "Assistente de cria" in corpo
    print(f"[new_with_ai] tem 'Assistente de criação'? {tem_assistente}")
    # procurar banner de bloqueio/limite
    msg = re.findall(r"(renderiz[^.]*|limite[^.]*|aguarde[^.]*|em andamento[^.]*|já existe[^.]*|não é possível[^.]*)", corpo, re.I)
    print(f"[new_with_ai] mensagens relevantes: {msg[:6]}")
    print(f"[new_with_ai] corpo(400): {corpo[:400]}")
    tw.snap(page, PASTA, "01-new-with-ai", full=True)

    # 2) estado de render dos cursos já criados
    for slug, cid in [("sql", "807992"), ("git", "807993")]:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio",
                  wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page)
        try:
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(3000)
        corpo = page.evaluate("()=>document.body.innerText.replace(/\\s+/g,' ')")
        pend = len(re.findall(r"pendentes", corpo, re.I))
        rend = bool(re.search(r"sendo renderizadas|Renderizando", corpo, re.I))
        banner = re.findall(r"Há \d+ atividades[^.]*minutos?", corpo)
        print(f"\n[{slug} {cid}] ocorrências 'pendentes'={pend} | renderizando={rend} | banner={banner}")
        tw.snap(page, PASTA, f"02-{slug}-studio", full=True)
    ctx.close(); browser.close()
