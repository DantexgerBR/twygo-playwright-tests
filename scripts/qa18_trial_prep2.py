# -*- coding: utf-8 -*-
"""QA 1.18 — fase A (retry): criar curso na Trial 37062 preenchendo o form certo.

Form 'Novo curso': Nome (placeholder 'Nome do curso') + react-select
'Tipo de experiência' (obrigatório; QA 1.3 mostrou que vazio barra o save
silenciosamente) → Salvar.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa18_e2e_1106"
NOME_CURSO = "QA 1.18 E2E - curso descartavel 1106"

c = tw.cfg("NOVOTRIAL")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new?kind=course",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)

    # Nome
    nome = page.get_by_placeholder("Nome do curso")
    nome.first.fill(NOME_CURSO)
    print(f"[ok] Nome = {NOME_CURSO}")

    # Tipo de experiência (react-select): digita 'Curso' e confirma com Enter
    tipo = page.locator("input[id^='react-select']").first
    tipo.click()
    tipo.fill("Curso")
    page.wait_for_timeout(1200)
    page.keyboard.press("Enter")
    page.wait_for_timeout(800)
    tw.snap(page, PASTA, "05-form-preenchido")

    # Salvar (botão pode estar no fim da página)
    btn = page.get_by_role("button", name=re.compile("^Salvar", re.I)).first
    btn.scroll_into_view_if_needed()
    btn.click(timeout=8000)
    print("[ok] Salvar clicado")
    try:
        page.wait_for_url(re.compile(r"/(contents|e|events)/\d+"), timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "06-curso-salvo")
    m = re.search(r"/(?:contents|e|events)/(\d+)", page.url)
    print(f"[ok] url pós-save: {page.url}")
    print(f"\n=== CURSO_ID={m.group(1) if m else None} ===")
    ctx.close(); browser.close()
