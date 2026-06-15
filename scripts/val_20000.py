# -*- coding: utf-8 -*-
"""20000 [P1] — Cena reconfigurada fixamente para 5s ao salvar roteiro.
Cria uma Aula nova, adiciona roteiro numa parte, clica 'Salvar roteiro' e checa
se a duração da cena vira 00:00:05 (bug) ou mantém/ajusta. Cleanup ao final."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoC"
CURSO = "807533"
ROTEIRO = ("Bem-vindos a esta aula sobre liderança de equipes. Hoje vamos explorar como a comunicação "
           "clara, o feedback construtivo e a empatia transformam a gestão de pessoas e elevam os "
           "resultados do time ao longo do tempo, com exemplos práticos do dia a dia corporativo.")
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"


def duracoes(page):
    return page.evaluate(
        r"""()=>{const out=[];document.querySelectorAll('*').forEach(e=>{const t=(e.innerText||'').trim();
            if(/^Duração:?\s*\d{2}:\d{2}:\d{2}$/.test(t) && e.children.length<3) out.push(t.replace(/\s+/g,' '));});return out;}"""
    )


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
        # criar Aula nova (parte limpa)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000); page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-lesson")).first.click(timeout=8000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
        print(f"[ok] Aula {aid}")
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(3000)
        # se não houver parte, adicionar
        if "Adicionar parte" in page.evaluate("()=>document.body.innerText") and not duracoes(page):
            try:
                page.get_by_role("button", name=re.compile(r"Adicionar parte", re.I)).first.click(timeout=5000)
                page.wait_for_timeout(2500)
            except Exception: pass
        dur_antes = duracoes(page)
        print(f"[antes] durações: {dur_antes}")
        tw.snap(page, PASTA, "20000-antes", full=True)

        # selecionar a parte (abre o painel Roteiro à direita)
        try:
            parte = page.get_by_text(re.compile(r"^Parte 1$", re.I)).first
            parte.click(timeout=5000, force=True); page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[!] selecionar parte: {e}")
        # abrir painel Roteiro se preciso
        if not page.get_by_placeholder(re.compile(r"roteiro", re.I)).count():
            try:
                page.get_by_text(re.compile(r"^Roteiro$", re.I)).first.click(timeout=4000, force=True); page.wait_for_timeout(1500)
            except Exception: pass
        # digitar roteiro na textarea (pelo placeholder) e salvar
        ta = page.get_by_placeholder(re.compile(r"conteúdo do roteiro|roteiro", re.I)).first
        ta.click(timeout=5000); ta.fill(ROTEIRO)
        page.wait_for_timeout(800)
        tw.snap(page, PASTA, "20000-roteiro-preenchido", full=True)
        btn = page.get_by_role("button", name=re.compile(r"Salvar roteiro", re.I)).first
        if not btn.count():
            btn = page.get_by_text(re.compile(r"Salvar roteiro", re.I)).first
        btn.scroll_into_view_if_needed(); page.wait_for_timeout(500)
        btn.click(timeout=6000, force=True)
        page.wait_for_timeout(6000); tw.dispensar_nps(page)
        dur_depois = duracoes(page)
        print(f"[depois de Salvar roteiro] durações: {dur_depois}")
        tw.snap(page, PASTA, "20000-pos-salvar-roteiro", full=True)

        virou_5s = any("00:00:05" in d for d in dur_depois)
        # bug = a cena virou 5s fixos após salvar o roteiro
        veredito = "FALHOU (cena resetou p/ 00:00:05)" if virou_5s else "PASSOU (duração não fixou em 5s)"
        print(f"\n=> 20000: {veredito} | antes={dur_antes} depois={dur_depois}")
    except Exception as e:
        print(f"=> 20000: ERRO {e}")
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
