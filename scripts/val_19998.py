# -*- coding: utf-8 -*-
"""19998 — Perda de dados na aba Identificação ao regerar Aula sem salvar.
Cria Aula, preenche título na aba Dados SEM salvar, vai pra Conteúdo, Salvar e
regerar, volta pra Dados e confere se o título foi preservado ou virou 'Nova atividade'.
Cleanup: exclui a atividade criada. (org 37061, curso 807533)"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoB"
CURSO = "807533"
TITULO = "QA19998 Titulo Customizado"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    ativ_id = None
    try:
        for _ in range(3):
            page.goto(url_studio, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); break
            except Exception: pass
        page.wait_for_timeout(2500)
        # criar Aula
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-lesson")).first.click(timeout=8000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); ativ_id = m.group(1) if m else None
        print(f"[ok] Aula criada: {ativ_id}")

        # aba Dados: preencher título SEM salvar
        campo = page.locator('input[name="title"]:visible').first
        campo.wait_for(state="visible", timeout=10000)
        campo.fill(TITULO)
        page.wait_for_timeout(800)
        tw.snap(page, PASTA, "01-dados-preenchido")
        print(f"[ok] título preenchido (sem salvar): {campo.input_value()!r}")

        # ir pra Conteúdo (sem salvar) — observar se há modal de aviso
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(2500)
        modal_aviso = page.evaluate("""()=>{const d=[...document.querySelectorAll('[role=dialog],[role=alertdialog],.chakra-modal__content')].find(e=>e.offsetParent!==null && /salvar|não salv|altera|descartar|deseja sair/i.test(e.innerText||''));return d?(d.innerText||'').replace(/\\s+/g,' ').slice(0,160):null;}""")
        print(f"[info] modal de aviso ao trocar de aba? {modal_aviso}")
        tw.snap(page, PASTA, "02-modal-aviso")
        # escolher "Sair e salvar" (preserva os dados da Identificação)
        if modal_aviso:
            page.get_by_role("button", name=re.compile(r"Sair e salvar", re.I)).first.click(timeout=6000)
            page.wait_for_timeout(4000); tw.dispensar_nps(page)
            print("[ok] cliquei 'Sair e salvar'")
        tw.snap(page, PASTA, "02b-conteudo")

        # Salvar e regerar
        btn = page.get_by_role("button", name=re.compile(r"Salvar e regerar", re.I)).first
        btn.scroll_into_view_if_needed()
        btn.click(timeout=8000)
        page.wait_for_timeout(6000)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, "03-pos-regerar")

        # voltar pra Dados e conferir o título
        page.get_by_text(re.compile(r"^Dados$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(3000)
        campo2 = page.locator('input[name="title"]:visible').first
        titulo_final = campo2.input_value() if campo2.count() else "(campo não encontrado)"
        preservou = TITULO in titulo_final
        print(f"[resultado] título após regerar: {titulo_final!r} | preservou? {preservou}")
        tw.snap(page, PASTA, "04-dados-pos-regerar")
        print(f"\n=> 19998: {'PASSOU (dados preservados)' if preservou else 'FALHOU (dados perdidos / virou Nova atividade)'}")
    except Exception as e:
        print(f"=> 19998: ERRO {e}")
    finally:
        if ativ_id:
            try:
                page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
                page.wait_for_timeout(2000)
                card = page.locator(tid(f"creation-studio-activity-card-{ativ_id}")).first
                card.scroll_into_view_if_needed(); card.click(timeout=8000, force=True); page.wait_for_timeout(2000)
                page.locator(tid("creation-studio-preview-delete")).first.click(timeout=8000, force=True); page.wait_for_timeout(1200)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000)
                page.wait_for_timeout(2500); print(f"[cleanup] atividade {ativ_id} excluída")
            except Exception as e:
                print(f"[cleanup] excluir manualmente {ativ_id} ({e})")
    ctx.close(); browser.close()
