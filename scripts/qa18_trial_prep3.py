# -*- coding: utf-8 -*-
"""QA 1.18 — fase A (retry 2): Nome + Tipo de experiência + Descrição (CKEditor) → Salvar."""
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

    page.get_by_placeholder("Nome do curso").first.fill(NOME_CURSO)
    tipo = page.locator("input[id^='react-select']").first
    tipo.click(); tipo.fill("Curso")
    page.wait_for_timeout(1200)
    page.keyboard.press("Enter")
    print("[ok] Nome + Tipo preenchidos")

    # Descrição: CKEditor clássico (iframe .cke_wysiwyg_frame) ou contenteditable inline
    desc_ok = False
    try:
        frame = page.frame_locator("iframe.cke_wysiwyg_frame")
        body = frame.locator("body")
        body.click(timeout=5000)
        body.fill("Curso descartavel criado pelo QA 1.18 para popular tabelas de historico (sera excluido).")
        desc_ok = True
    except Exception as e:
        print(f"[warn] iframe CKE falhou: {e}")
        ce = page.locator("[contenteditable='true']:visible").first
        ce.click(timeout=5000)
        ce.fill("Curso descartavel criado pelo QA 1.18 para popular tabelas de historico (sera excluido).")
        desc_ok = True
    print(f"[ok] Descrição preenchida: {desc_ok}")
    tw.snap(page, PASTA, "07-form-completo")

    btn = page.get_by_role("button", name=re.compile("^Salvar", re.I)).first
    btn.scroll_into_view_if_needed()
    btn.click(timeout=8000)
    try:
        page.wait_for_url(re.compile(r"/(contents|e|events)/\d+"), timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "08-curso-salvo")
    m = re.search(r"/(?:contents|e|events)/(\d+)", page.url)
    print(f"[ok] url pós-save: {page.url}")
    print(f"\n=== CURSO_ID={m.group(1) if m else None} ===")
    ctx.close(); browser.close()
