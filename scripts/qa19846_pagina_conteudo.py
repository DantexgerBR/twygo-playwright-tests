# -*- coding: utf-8 -*-
"""19846 [P0] — editar atividade Página apagava o conteúdo publicado (editor
reabria vazio e Salvar persistia o vazio; intermitente ~4/5).

Valida: criar Página com conteúdo → salvar → REABRIR o form 5x (editor deve
carregar o conteúdo nas 5) → salvar sem alterar → reabrir e conferir que o
conteúdo persiste. Org 37061, curso 807533. Cleanup: excluir a atividade.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa19846_pagina_conteudo"
CURSO = "807533"
TITULO = "QA19846 pagina conteudo"
CONTEUDO = "Conteudo de teste QA19846 - este texto nao pode sumir ao reabrir o formulario."

c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'


def ler_editor(page):
    """Texto do editor de conteúdo (Slate/Plate contenteditable) visível."""
    return page.evaluate(
        """()=>{
            const eds=[...document.querySelectorAll("[contenteditable='true']")]
                .filter(e=>e.offsetParent!==null);
            return eds.map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).join(' || ');
        }"""
    )


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
    for _ in range(3):
        page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page)
        try:
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
            break
        except Exception:
            print("[retry] hidratação")
    page.wait_for_timeout(2000)

    # criar atividade Página (clicar no tipo JÁ CRIA — capturar id da URL do form)
    page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
    page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
    page.locator(tid("creation-studio-type-selector-page")).first.click(timeout=8000)
    page.wait_for_timeout(4000)
    m = re.search(r"/studio/activities/(\d+)/edit", page.url)
    ativ_id = m.group(1) if m else None
    print(f"[ok] atividade criada: {ativ_id} (url {page.url})")
    url_form = page.url

    # título + conteúdo no editor
    campo = page.locator('input[name="title"]:visible').first
    campo.wait_for(state="visible", timeout=10000)
    campo.fill(TITULO)
    editor = page.locator("[contenteditable='true']:visible").first
    editor.click(timeout=8000)
    editor.type(CONTEUDO, delay=10)
    page.wait_for_timeout(800)
    tw.snap(page, PASTA, "01-form-preenchido")
    page.locator(tid("creation-studio-activity-page-save")).first.click(timeout=8000)
    page.wait_for_timeout(4000)
    print("[ok] salvo com conteúdo")

    # REABRIR 5x — o editor deve carregar o conteúdo em todas
    cargas = []
    for i in range(1, 6):
        page.goto(url_form, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        tw.dispensar_nps(page)
        texto = ler_editor(page)
        carregou = "QA19846" in texto
        cargas.append(carregou)
        print(f"[reabertura {i}/5] conteúdo carregado? {carregou} | editor: {texto[:90]!r}")
        if i == 1:
            tw.snap(page, PASTA, "02-reabertura-1")
    print(f"[resultado] cargas com conteúdo: {sum(cargas)}/5")

    # salvar SEM alterar e reconferir
    page.locator(tid("creation-studio-activity-page-save")).first.click(timeout=8000)
    page.wait_for_timeout(4000)
    page.goto(url_form, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(6000)
    tw.dispensar_nps(page)
    texto_final = ler_editor(page)
    preservou = "QA19846" in texto_final
    print(f"[salvar sem alterar] conteúdo preservado? {preservou} | editor: {texto_final[:90]!r}")
    tw.snap(page, PASTA, "03-pos-save-sem-alterar")

    # cleanup: excluir a atividade (card → preview → Excluir → confirmar)
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
        print("[cleanup] atividade excluída")
    except Exception as e:
        print(f"[cleanup] FALHOU ({e}) — excluir manualmente a atividade {ativ_id} do curso {CURSO}")
    tw.snap(page, PASTA, "04-cleanup")

    print(f"\n=== 19846: cargas {sum(cargas)}/5 | preservou pós-save: {preservou} ===")
    ctx.close(); browser.close()
