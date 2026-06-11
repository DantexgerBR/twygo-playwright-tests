# -*- coding: utf-8 -*-
"""QA 1.18 — fase A (retry 3): Descrição via API CKEDITOR.setData (digitar no
iframe não sincroniza o form — validação seguia acusando vazio)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa18_e2e_1106"
NOME_CURSO = "QA 1.18 E2E - curso descartavel 1106"
DESC = "Curso descartavel criado pelo QA 1.18 para popular tabelas de historico (sera excluido)."

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

    # Descrição via API do CKEditor (setData dispara 'change' → React sincroniza)
    res = page.evaluate(
        """(html) => {
            if (!window.CKEDITOR) return 'sem CKEDITOR global';
            const keys = Object.keys(CKEDITOR.instances);
            if (!keys.length) return 'sem instancias';
            const ed = CKEDITOR.instances[keys[0]];
            ed.setData('<p>' + html + '</p>');
            ed.updateElement();
            ed.fire('change');
            const ta = ed.element && ed.element.$;
            if (ta) {
                ta.dispatchEvent(new Event('input', {bubbles: true}));
                ta.dispatchEvent(new Event('change', {bubbles: true}));
            }
            return 'ok: ' + keys[0];
        }""",
        DESC,
    )
    print(f"[ck] {res}")
    page.wait_for_timeout(1000)
    tw.snap(page, PASTA, "09-form-ck-api")

    btn = page.get_by_role("button", name=re.compile("^Salvar", re.I)).first
    btn.scroll_into_view_if_needed()
    btn.click(timeout=8000)
    try:
        page.wait_for_url(re.compile(r"/(contents|e|events)/\d+"), timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "10-curso-salvo")
    m = re.search(r"/(?:contents|e|events)/(\d+)", page.url)
    print(f"[ok] url pós-save: {page.url}")
    print(f"\n=== CURSO_ID={m.group(1) if m else None} ===")
    ctx.close(); browser.close()
