# -*- coding: utf-8 -*-
"""Captura evidência dos bugs do Discovery ainda sem print (org 37061, curso 807533):
  14 - rota /events/:id/edit/studio retorna 404
  23 - escolher o tipo em "Adicionar atividade" já cria rascunho órfão
  08 - editor não tem a ação "Salvar como novo" (só Salvar/rascunho/regerar)
Cada item isolado em try/except. Item 23 faz cleanup do rascunho criado."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "evidencia_bugs_discovery"
CURSO = "807533"
ATIV_EXISTENTE = "9288190"  # PDF Estampado já existente no curso (para o item 08)
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    print("[ok] logado\n")

    # ===================================================================== #
    # ITEM 14 — rota /events/:id/edit/studio retorna 404
    # ===================================================================== #
    print("### ITEM 14 — rota /events/:id/edit/studio")
    try:
        rota_velha = f"{c['base_url']}/o/{c['org_id']}/events/{CURSO}/edit/studio"
        resp = page.goto(rota_velha, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)
        status = resp.status if resp else None
        corpo = page.evaluate("()=>document.body.innerText.slice(0,400)")
        eh_404 = bool(re.search(r"404|não encontrad|nao encontrad|not found|página não existe", corpo, re.I)) or status == 404
        print(f"   GET {rota_velha}\n   HTTP status={status} | indício de 404 no corpo={eh_404}")
        print(f"   corpo: {corpo[:160]!r}")
        tw.snap(page, PASTA, "14-rota-events-studio-404", full=True)
        # contraprova: a rota real responde
        resp2 = page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio",
                          wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        print(f"   contraprova rota real /contents/{CURSO}/edit?tab=studio -> status={resp2.status if resp2 else None}")
        tw.snap(page, PASTA, "14-rota-real-ok")
    except Exception as e:
        print(f"   ERRO {e}")
    print()

    # ===================================================================== #
    # ITEM 23 — escolher o tipo já cria rascunho órfão
    # ===================================================================== #
    print("### ITEM 23 — rascunho órfão ao escolher o tipo")
    ativ_id = None
    url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
    try:
        for _ in range(3):
            page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
            tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
                break
            except Exception:
                print("   [retry] hidratação")
        page.wait_for_timeout(2000)
        # contar atividades antes
        antes = page.locator('[data-test-id^="creation-studio-activity-card-"]').count()
        print(f"   atividades ANTES de escolher o tipo: {antes}")
        tw.snap(page, PASTA, "23-lista-antes")

        # abrir seletor e escolher um tipo (Texto) — NÃO confirmar/preencher nada
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(1000)
        page.locator(tid("creation-studio-type-selector-text")).first.click(timeout=8000)
        page.wait_for_timeout(4000)
        tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url)
        ativ_id = m.group(1) if m else None
        criou_na_hora = ativ_id is not None
        print(f"   APÓS só escolher o tipo: já abriu editor com id? {criou_na_hora} (url {page.url})")
        tw.snap(page, PASTA, "23-apos-escolher-tipo-editor")

        # voltar à lista SEM salvar e ver o rascunho órfão
        page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(3000)
        depois = page.locator('[data-test-id^="creation-studio-activity-card-"]').count()
        card_txt = ""
        if ativ_id:
            card = page.locator(tid(f"creation-studio-activity-card-{ativ_id}"))
            if card.count():
                card.first.scroll_into_view_if_needed()
                card_txt = card.first.inner_text().replace("\n", " | ")
        print(f"   atividades DEPOIS (sem salvar): {depois} (delta={depois-antes}) | card órfão: {card_txt!r}")
        tw.snap(page, PASTA, "23-lista-depois-com-orfao")
    except Exception as e:
        print(f"   ERRO {e}")
    finally:
        if ativ_id:
            try:
                page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
                page.wait_for_timeout(2000)
                card = page.locator(tid(f"creation-studio-activity-card-{ativ_id}")).first
                card.scroll_into_view_if_needed()
                card.click(timeout=8000, force=True)
                page.wait_for_timeout(2500)
                page.locator(tid("creation-studio-preview-delete")).first.click(timeout=8000, force=True)
                page.wait_for_timeout(1500)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role(
                    "button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000)
                page.wait_for_timeout(3000)
                print(f"   [cleanup] rascunho órfão {ativ_id} excluído")
            except Exception as e:
                print(f"   [cleanup] FALHOU ({e}) — excluir manualmente {ativ_id}")
    print()

    # ===================================================================== #
    # ITEM 08 — editor não tem "Salvar como novo"
    # ===================================================================== #
    print("### ITEM 08 — ação 'Salvar como novo' inexistente no editor")
    try:
        url_form = f"{c['base_url']}/o/{c['org_id']}/studio/activities/{ATIV_EXISTENTE}/edit?type=pdf&eventId={CURSO}"
        page.goto(url_form, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        tw.dispensar_nps(page)
        # listar TODAS as ações/botões visíveis com "salvar" no texto + procurar menu secundário
        acoes = page.evaluate(
            """()=>[...document.querySelectorAll('button,[role=button],[role=menuitem],a')]
                .filter(e=>e.offsetParent!==null && /salvar|publicar|duplicar|como novo|regerar|rascunho/i.test(e.innerText||''))
                .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim())"""
        )
        corpo = page.evaluate("()=>document.body.innerText")
        tem_salvar_novo = bool(re.search(r"Salvar como novo", corpo, re.I))
        print(f"   ações de salvar/publicar visíveis: {acoes}")
        print(f"   'Salvar como novo' presente? {tem_salvar_novo}")
        tw.snap(page, PASTA, "08-editor-sem-salvar-como-novo", full=True)
    except Exception as e:
        print(f"   ERRO {e}")

    print("\n=== fim da captura ===")
    ctx.close(); browser.close()
