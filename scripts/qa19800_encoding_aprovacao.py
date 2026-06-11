# -*- coding: utf-8 -*-
"""Card 19800 [P1] — validar fixes: (1) encoding nas mensagens do chat do copiloto
(PR twygo-ai-knowledge-agent#373: decodificar escapes unicode soltos) e
(2) atividade nascendo com roteiro pré-aprovado (PR twyg-app#10544: não preencher
narrator_script com o summary ao criar atividade).

Fluxo (Trial 37062): criar curso → criar atividade Page → conferir badge de
pendências (Roteiro deve estar PENDENTE) → disparar geração do roteiro →
varrer texto do chat por escapes \\uXXXX e mojibake → aguardar card de validação
AGUARDANDO aprovação (Aprovar/Regerar/Rejeitar — NÃO aprovar).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa19800_encoding_aprovacao"
NOME_CURSO = "QA19800 validacao encoding e aprovacao"
TITULO_ATIV = "QA19800 atividade roteiro"
DESC = "Curso descartavel da validacao do card 19800 (sera excluido)."

c = tw.cfg("NOVOTRIAL")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    # --- 1) curso descartável (form legado; gotchas do 1.18) ---
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new?kind=course",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    page.get_by_placeholder("Nome do curso").first.fill(NOME_CURSO)
    tipo = page.locator("input[id^='react-select']").first
    tipo.click(); tipo.fill("Curso")
    page.wait_for_timeout(1200)
    page.keyboard.press("Enter")
    page.evaluate(
        "(h)=>{const ed=CKEDITOR.instances[Object.keys(CKEDITOR.instances)[0]];"
        "ed.setData('<p>'+h+'</p>');ed.updateElement();ed.fire('change');}",
        DESC,
    )
    page.wait_for_timeout(800)
    btn = page.get_by_role("button", name=re.compile("^Salvar", re.I)).first
    btn.scroll_into_view_if_needed(); btn.click(timeout=8000)
    page.wait_for_url(re.compile(r"/contents/\d+"), timeout=25000)
    curso_id = re.search(r"/contents/(\d+)", page.url).group(1)
    print(f"[ok] curso criado: {curso_id}")

    # --- 2) atividade Page no Estúdio ---
    url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{curso_id}/edit?tab=studio"
    for _ in range(3):
        page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page)
        try:
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
            break
        except Exception:
            print("[retry] hidratação do Estúdio")
    page.wait_for_timeout(2000)
    page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
    page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
    page.locator(tid("creation-studio-type-selector-page")).first.click(timeout=8000)
    page.wait_for_timeout(3000)
    try:
        campo = page.locator('input[name="title"]:visible').first
        campo.wait_for(state="visible", timeout=10000)
        campo.fill(TITULO_ATIV)
        page.locator(tid("creation-studio-activity-page-save")).first.click(timeout=8000)
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[warn] form de título: {e}")
    tw.dispensar_nps(page)
    if "tab=studio" not in page.url:
        page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(2000)

    # --- 3) FIX 2 (parte A): atividade deve NASCER com Roteiro PENDENTE ---
    badge = page.locator(tid("studio-pending-artifacts-badge") + ":visible").last
    badge.scroll_into_view_if_needed()
    badge_txt = badge.inner_text()
    print(f"[fix2] badge de pendências da atividade nova: {badge_txt!r}")
    badge.click(timeout=10000)
    pop = page.locator(tid("studio-pending-artifacts-popover") + ":visible").first
    pop.wait_for(state="visible", timeout=10000)
    pop_txt = pop.inner_text().replace("\n", " | ")
    roteiro_pendente = pop.locator(tid("studio-pending-artifacts-row-roteiro")).count() > 0
    print(f"[fix2] popover: {pop_txt!r}")
    print(f"[fix2] linha 'Roteiro' PENDENTE presente? {roteiro_pendente}")
    tw.snap(page, PASTA, "01-popover-roteiro-pendente")

    # --- 4) disparar geração do roteiro ---
    pop.locator(tid("studio-pending-artifacts-row-roteiro")).first.click(timeout=8000)
    print("[ok] geração do roteiro disparada")
    page.wait_for_timeout(10000)
    tw.snap(page, PASTA, "02-chat-pos-disparo")

    # --- 5) FIX 1: varrer texto do chat por escapes unicode crus / mojibake ---
    drawer = page.locator(tid("copilot-drawer"))
    texto = drawer.inner_text(timeout=10000)
    escapes = re.findall(r"\\u[0-9a-fA-F]{4}", texto)
    mojibake = re.findall(r"Ã[§©¡£µ¢ªº­]|â€|ï¿½", texto)
    print(f"[fix1] escapes \\uXXXX no chat: {escapes or 'NENHUM ✔'}")
    print(f"[fix1] mojibake no chat: {mojibake or 'NENHUM ✔'}")
    print("[fix1] amostra do chat:", texto[:500].replace("\n", " | "))
    m = re.search(r"event_content_id:\s*(\d+)", texto)
    ec_id = m.group(1) if m else None
    print(f"[info] event_content_id: {ec_id}")

    # --- 6) FIX 2 (parte B): aguardar card de validação AGUARDANDO aprovação ---
    aprovado_sozinho = None
    card_visivel = False
    for tentativa in range(36):  # até ~3 min
        page.wait_for_timeout(5000)
        cards = page.locator('[data-test-id^="studio-copilot-validation-message-"]')
        if cards.count():
            ultimo = cards.last
            aprovar = ultimo.locator(tid("studio-copilot-validation-approve"))
            regerar = ultimo.locator(tid("studio-copilot-validation-regenerate"))
            rejeitar = ultimo.locator(tid("studio-copilot-validation-reject"))
            if aprovar.count() and aprovar.first.is_visible():
                card_visivel = True
                print(f"[fix2] card de validação APARECEU aguardando ação — "
                      f"Aprovar={aprovar.count() > 0} Regerar={regerar.count() > 0} Rejeitar={rejeitar.count() > 0}")
                break
    tw.snap(page, PASTA, "03-card-validacao")
    if card_visivel:
        # texto do card (também serve pro check de encoding)
        card_txt = page.locator('[data-test-id^="studio-copilot-validation-message-"]').last.inner_text()
        esc_card = re.findall(r"\\u[0-9a-fA-F]{4}", card_txt)
        print(f"[fix1] escapes no card de validação: {esc_card or 'NENHUM ✔'}")
        print("[fix2] card aguarda decisão do usuário (NÃO aprovando — fim do teste).")
    else:
        print("[warn] card de validação não apareceu em ~3min — conferir no banco se a task completou")

    texto_final = drawer.inner_text(timeout=10000)
    (PASTA / "chat-completo.txt").write_text(texto_final, encoding="utf-8")
    tw.snap(page, PASTA, "04-estado-final")
    print(f"\n=== CURSO={curso_id} EC={ec_id} (verificar no MySQL: narrator_script vazio + approved_by NULL) ===")
    ctx.close(); browser.close()
