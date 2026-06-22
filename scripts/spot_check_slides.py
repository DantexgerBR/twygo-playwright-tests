# -*- coding: utf-8 -*-
"""Spot-check visual: abre o player do aluno, entra numa Aula e captura os slides
renderizados em intervalos (pra ler o TEXTO dentro do slide, não só os títulos)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("NOVOEST")
ALVOS = [("nr35", "807994", "Fundamentos da NR-35"),
         ("atendimento", "807995", "Princípios da Comunicação")]


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1280, height=760)
    tw.login(page, c)

    for slug, cid, aula_nome in ALVOS:
        PASTA = tw.ROOT / "evidencias" / f"qualidade_ia_{slug}"
        print(f"\n=== spot-check {slug} ({cid}) — aula '{aula_nome}' ===")
        # abrir player direto
        aluno = page
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio",
                  wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page)
        page.wait_for_timeout(2500)
        try:
            with ctx.expect_page(timeout=8000) as nova:
                page.get_by_role("button", name=re.compile(r"Visualizar como aluno", re.I)).first.click(timeout=6000)
            aluno = nova.value
        except Exception:
            aluno = ctx.pages[-1]
        aluno.wait_for_timeout(6000)
        tw.dispensar_nps(aluno)

        # abrir a aula
        try:
            aluno.get_by_text(re.compile(aula_nome, re.I)).first.click(timeout=6000, force=True)
            aluno.wait_for_timeout(7000)
        except Exception as e:
            print(f"  [!] não abri a aula: {e}")
        tw.dispensar_nps(aluno)

        # dar play se houver
        for sel in ["button[aria-label*='play' i]", ".vjs-big-play-button", "button:has-text('Iniciar')"]:
            try:
                b = aluno.locator(sel).first
                if b.count() and b.is_visible():
                    b.click(timeout=3000); break
            except Exception:
                pass

        # capturar slides em intervalos (cada slide ~10s)
        for k, t in enumerate([1, 11, 22, 34, 46]):
            aluno.wait_for_timeout(t * 1000 if k == 0 else (t - [1,11,22,34,46][k-1]) * 1000)
            tw.snap(aluno, PASTA, f"80-slide-{k}")
        # fechar a aba do player p/ a próxima iteração
        if aluno is not page:
            aluno.close()

    ctx.close(); browser.close()
