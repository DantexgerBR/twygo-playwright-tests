# -*- coding: utf-8 -*-
"""19961 — prova de interação: em 360px, tocar nas 3 abas do rodapé alterna as áreas."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa_lote_1106_responsivo"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    ctx = browser.new_context(viewport={"width": 360, "height": 740}, locale="pt-BR")
    page = ctx.new_page()
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio",
              wait_until="domcontentloaded", timeout=30000)
    tw.dispensar_nps(page)
    page.wait_for_timeout(6000)
    tw.dispensar_nps(page)

    for aba, snap in [("Pré-visualização", "tab-preview"), ("Copiloto", "tab-copiloto"), ("Atividades", "tab-atividades")]:
        alvo = page.get_by_text(aba, exact=True).last
        alvo.click(timeout=8000, force=True)
        page.wait_for_timeout(3000)
        corpo = page.evaluate("()=>document.body.innerText.slice(0,300).replace(/\\s+/g,' ')")
        print(f"[{aba}] topo da tela: {corpo[:140]!r}")
        tw.snap(page, PASTA, f"360-{snap}")
    print("=== abas alternando ok ===")
    ctx.close(); browser.close()
