# -*- coding: utf-8 -*-
"""19797 [P1] — Ao regerar, o conteúdo/roteiro fica vazio.
Cria Aula, adiciona roteiro numa parte, 'Salvar e regerar', espera render e
reabre conferindo se o roteiro/conteúdo persiste (não vazio). Cleanup ao final."""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoC"
CURSO = "807533"
ROTEIRO = "Esta é a introdução da aula. Vamos aprender os tres pilares da lideranca: comunicacao, confianca e feedback."
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"


def ler_roteiro(page):
    ta = page.get_by_placeholder(re.compile(r"conteúdo do roteiro|roteiro", re.I)).first
    return ta.input_value() if ta.count() else "(sem textarea)"


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=1000)
    tw.login(page, c)
    aid = None
    try:
        for _ in range(3):
            page.goto(url_studio, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); break
            except Exception: pass
        page.wait_for_timeout(2500)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000); page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-lesson")).first.click(timeout=8000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
        print(f"[ok] Aula {aid}")
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True); page.wait_for_timeout(3000)
        # selecionar parte + roteiro
        try:
            page.get_by_text(re.compile(r"^Parte 1$", re.I)).first.click(timeout=5000, force=True); page.wait_for_timeout(2000)
        except Exception: pass
        if not page.get_by_placeholder(re.compile(r"roteiro", re.I)).count():
            try:
                page.get_by_text(re.compile(r"^Roteiro$", re.I)).first.click(timeout=4000, force=True); page.wait_for_timeout(1500)
            except Exception: pass
        ta = page.get_by_placeholder(re.compile(r"conteúdo do roteiro|roteiro", re.I)).first
        ta.click(timeout=8000); ta.fill(ROTEIRO); page.wait_for_timeout(1000)
        btn = page.get_by_role("button", name=re.compile(r"Salvar roteiro", re.I)).first
        if not btn.count():
            btn = page.get_by_text(re.compile(r"Salvar roteiro", re.I)).first
        btn.scroll_into_view_if_needed(); page.wait_for_timeout(500)
        btn.click(timeout=6000, force=True); page.wait_for_timeout(4000)
        print(f"[antes regerar] roteiro: {ler_roteiro(page)[:60]!r}")
        tw.snap(page, PASTA, "19797-antes-regerar", full=True)

        # Salvar e regerar
        page.get_by_role("button", name=re.compile(r"Salvar e regerar", re.I)).first.click(timeout=8000)
        page.wait_for_timeout(8000); tw.dispensar_nps(page)
        # esperar render (até ~4min)
        fim = time.time() + 240
        while time.time() < fim:
            corpo = page.evaluate("()=>document.body.innerText")
            if not re.search(r"sendo renderizad|Renderizando|processament", corpo, re.I):
                break
            page.wait_for_timeout(15000)
        # reabrir a aula e ler roteiro/conteúdo
        page.goto(f"{c['base_url']}/o/{c['org_id']}/studio/activities/{aid}/edit?type=lesson&eventId={CURSO}",
                  wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True); page.wait_for_timeout(3000)
        try:
            page.get_by_text(re.compile(r"^Parte 1$", re.I)).first.click(timeout=5000, force=True); page.wait_for_timeout(2000)
        except Exception: pass
        if not page.get_by_placeholder(re.compile(r"roteiro", re.I)).count():
            try:
                page.get_by_text(re.compile(r"^Roteiro$", re.I)).first.click(timeout=4000, force=True); page.wait_for_timeout(1500)
            except Exception: pass
        roteiro_final = ler_roteiro(page)
        partes = page.evaluate(r"""()=>[...document.querySelectorAll('*')].filter(e=>/^Parte \d+$/.test((e.innerText||'').trim())).length""")
        tw.snap(page, PASTA, "19797-pos-regerar", full=True)
        vazio = (not roteiro_final) or roteiro_final.strip() == "" or roteiro_final == "(sem textarea)"
        print(f"[pós regerar] roteiro: {roteiro_final[:60]!r} | partes={partes}")
        print(f"=> 19797: {'FALHOU (roteiro/conteúdo vazio após regerar)' if vazio else 'PASSOU (conteúdo persiste após regerar)'}")
    except Exception as e:
        print(f"=> 19797: ERRO {e}")
    finally:
        if aid:
            try:
                page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); page.wait_for_timeout(2000)
                cd = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
                cd.scroll_into_view_if_needed(); cd.click(timeout=8000, force=True); page.wait_for_timeout(2000)
                page.locator(tid("creation-studio-preview-delete")).first.click(timeout=8000, force=True); page.wait_for_timeout(1200)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000); page.wait_for_timeout(2500); print(f"[cleanup] {aid}")
            except Exception as e:
                print(f"[cleanup] manual {aid} ({e})")
    ctx.close(); browser.close()
