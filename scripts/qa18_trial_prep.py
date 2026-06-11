# -*- coding: utf-8 -*-
"""QA 1.18 (Novo Estúdio) — fase A do E2E: garantir 1 curso na Trial 37062.

A Trial foi re-semeada em 10/06 ao ativar o Estúdio e a listagem de Conteúdos
ficou vazia. Este script loga, confere a listagem e, se não houver curso,
cria um descartável via form legado (/contents/new?kind=course). Imprime o
event_id do curso a usar na fase B (geração via copiloto).
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
    print(f"[ok] logado, url atual: {page.url}")
    tw.snap(page, PASTA, "01-listagem-conteudos")

    # Conta cursos na listagem (linhas de tabela ou cards; vazio = "Não há dados")
    page.wait_for_timeout(2000)
    vazio = page.get_by_text(re.compile("Não há dados", re.I)).count() > 0
    linhas = page.locator("tr[data-item-id]").count()
    print(f"[info] listagem vazia? {vazio} | linhas tr[data-item-id]: {linhas}")

    curso_id = None
    if not vazio and linhas > 0:
        # pega o primeiro curso da lista (link com /contents/{id} ou /e/{id})
        href = page.locator("tr[data-item-id] a[href*='/contents/'], tr[data-item-id] a[href*='/e/']").first.get_attribute("href")
        m = re.search(r"/(?:contents|e)/(\d+)", href or "")
        curso_id = m.group(1) if m else None
        print(f"[ok] curso existente encontrado: id={curso_id} (href={href})")
    else:
        # cria curso via form legado
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new?kind=course",
                  wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, "02-form-novo-curso")

        # campo Nome: tenta seletor Rails clássico, depois label/placeholder
        preenchido = False
        for sel in ["#event_name", "input[name='event[name]']"]:
            loc = page.locator(sel)
            if loc.count():
                loc.first.fill(NOME_CURSO); preenchido = True; break
        if not preenchido:
            campos = page.locator("input[type='text']:visible")
            print(f"[debug] inputs text visíveis: {campos.count()}")
            for i in range(campos.count()):
                ph = (campos.nth(i).get_attribute("placeholder") or "") + " " + (campos.nth(i).get_attribute("id") or "")
                print(f"  - input[{i}]: {ph}")
            campos.first.fill(NOME_CURSO); preenchido = True
        print(f"[ok] nome preenchido: {NOME_CURSO}")

        # salvar
        salvo = False
        for nome_btn in ["Salvar", "Criar", "Continuar", "Avançar"]:
            b = page.get_by_role("button", name=re.compile(nome_btn, re.I)).first
            if b.count() and b.is_visible():
                b.click(timeout=5000); salvo = True
                print(f"[ok] cliquei em '{nome_btn}'"); break
        if not salvo:
            page.locator("input[type=submit]:visible").first.click(timeout=5000)
            print("[ok] cliquei em input[type=submit]")
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, "03-curso-salvo")
        m = re.search(r"/(?:contents|e|events)/(\d+)", page.url)
        curso_id = m.group(1) if m else None
        print(f"[ok] pós-save url: {page.url}")

    print(f"\n=== CURSO_ID={curso_id} ===")
    tw.snap(page, PASTA, "04-estado-final")
    ctx.close(); browser.close()
