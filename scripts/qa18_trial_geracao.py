# -*- coding: utf-8 -*-
"""QA 1.18 — fase B: disparar geração IA real no Estúdio (Trial 37062, curso 807899).

Fluxo (skills testar-estudio-criacao-twygo + testar-geracao-ia-copiloto-twygo):
  Estúdio → Adicionar atividade → tipo Page (cria rascunho c/ 3 pendências)
  → salvar título → badge "pendentes" → popover → linha 'roteiro'
  → task de geração ENFILEIRADA no backend (popula ai_generation_tasks).
Não aprova nada (aprovar cascateia gerações caras).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa18_e2e_1106"
CURSO_ID = "807899"
TITULO = "QA118-GERACAO roteiro"

c = tw.cfg("NOVOTRIAL")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    # Estúdio com retry de hidratação (3x)
    url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO_ID}/edit?tab=studio"
    for tentativa in range(3):
        page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page)
        try:
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
            break
        except Exception:
            print(f"[retry] lista não hidratou (tentativa {tentativa+1})")
    page.wait_for_timeout(2000)
    tw.snap(page, PASTA, "11-estudio-aberto")

    # Adicionar atividade → tipo Page (clicar JÁ CRIA o rascunho)
    page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
    page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
    tw.snap(page, PASTA, "12-type-selector")
    page.locator(tid("creation-studio-type-selector-page")).first.click(timeout=8000)
    page.wait_for_timeout(3000)
    tw.snap(page, PASTA, "13-pos-criar-page")

    # Form da atividade: título + Salvar (título só persiste com Salvar)
    try:
        campo = page.locator('input[name="title"]:visible').first
        campo.wait_for(state="visible", timeout=10000)
        campo.fill(TITULO)
        page.locator(tid("creation-studio-activity-page-save")).first.click(timeout=8000)
        page.wait_for_timeout(3000)
        print(f"[ok] atividade salva: {TITULO}")
    except Exception as e:
        print(f"[warn] form de título não apareceu ({e}) — seguindo com 'Nova atividade'")
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "14-atividade-salva")

    # Voltar pra lista do Estúdio se o save navegou pra outra tela
    if "tab=studio" not in page.url:
        page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(2000)

    # Badge "N pendentes" da atividade nova → popover → linha roteiro
    badge = page.locator(tid("studio-pending-artifacts-badge") + ":visible").last
    badge.scroll_into_view_if_needed()
    badge.click(timeout=10000)
    pop = page.locator(tid("studio-pending-artifacts-popover") + ":visible").first
    pop.wait_for(state="visible", timeout=10000)
    tw.snap(page, PASTA, "15-popover-pendencias")

    pop.locator(tid("studio-pending-artifacts-row-roteiro")).first.click(timeout=8000)
    print("[ok] linha 'roteiro' clicada — geração disparada")

    # Espera o copiloto abrir e a task ser enfileirada (mensagem/validation card)
    page.wait_for_timeout(8000)
    tw.snap(page, PASTA, "16-copiloto-pos-disparo")
    corpo = page.locator('[data-test-id^="studio-copilot-validation-"], ' + tid("copilot-drawer"))
    print(f"[info] elementos de copiloto/validação visíveis: {corpo.count()}")
    page.wait_for_timeout(15000)
    tw.snap(page, PASTA, "17-copiloto-30s")

    texto_drawer = ""
    try:
        texto_drawer = page.locator(tid("copilot-drawer")).inner_text(timeout=5000)
    except Exception:
        pass
    print("[drawer]", texto_drawer[:600].replace("\n", " | "))
    print("\n=== GERACAO DISPARADA (curso 807899, atividade Page, etapa roteiro) ===")
    ctx.close(); browser.close()
