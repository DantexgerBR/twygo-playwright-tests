# -*- coding: utf-8 -*-
"""Lote desktop org 37061 / curso 807533 — valida 5 retrabalhos:
  19847 Ctrl+J toggle do copiloto (PR 10616)
  19821 drawer do copiloto 50% + botão expandir até 100% (PR 10639)
  19814 controles de colapsar/ocultar o menu lateral (sem PR)
  19826 lista do Estúdio reflete display_label (PR 10615)
  19809 "Criar curso com IA" abre o assistente (sem PR)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa_lote_1106_desktop"
CURSO = "807533"
ATIV = "9288190"
LABEL_TESTE = "Aula Customizada QA"
LABEL_ORIGINAL = "PDF Estampado"

c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
VW = 1366

with tw.sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=350)
    ctx = browser.new_context(viewport={"width": VW, "height": 768}, locale="pt-BR")
    page = ctx.new_page()
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

    # ---------- 19814: controles do menu lateral ----------
    print("\n### 19814 — colapsar/ocultar menu lateral")
    controles = page.evaluate(
        """()=>[...document.querySelectorAll('button,[role=button],a')]
            .filter(b=>b.offsetParent!==null)
            .map(b=>(b.getAttribute('aria-label')||b.title||(b.innerText||'').trim()))
            .filter(t=>/recolher|colapsar|ocultar|esconder|collapse|expandir menu|menu_open/i.test(t))"""
    )
    print(f"[19814] controles de colapso/ocultar encontrados: {controles or 'NENHUM'}")
    tw.snap(page, PASTA, "19814-menu-lateral")

    # ---------- 19847: Ctrl+J toggle ----------
    print("\n### 19847 — Ctrl+J toggle do copiloto")
    page.keyboard.press("Control+j")
    page.wait_for_timeout(2500)
    aberto = page.locator(tid("copilot-drawer")).first.is_visible()
    print(f"[19847] após 1º Ctrl+J: drawer visível? {aberto}")
    tw.snap(page, PASTA, "19847-ctrlj-abriu")
    page.keyboard.press("Control+j")
    page.wait_for_timeout(2500)
    fechado = not page.locator(tid("copilot-drawer")).first.is_visible()
    print(f"[19847] após 2º Ctrl+J: drawer fechou? {fechado}")
    tw.snap(page, PASTA, "19847-ctrlj-fechou")

    # ---------- 19821: drawer 50% + expandir ----------
    print("\n### 19821 — drawer 50% + expandir até 100%")
    page.keyboard.press("Control+j")
    page.wait_for_timeout(3000)
    drawer = page.locator(tid("copilot-drawer")).first
    box = drawer.bounding_box() or {}
    w1 = box.get("width", 0)
    print(f"[19821] largura ao abrir: {w1:.0f}px de {VW} ({100*w1/VW:.0f}%)")
    tw.snap(page, PASTA, "19821-drawer-aberto")
    expandir = page.get_by_role("button", name=re.compile("expandir|maximizar|expand", re.I))
    visiveis = [i for i in range(expandir.count()) if expandir.nth(i).is_visible()]
    if not visiveis:
        # fallback: procurar por test-id/aria dentro do drawer
        cand = drawer.locator("button[aria-label*='xpand' i], [data-test-id*='expand']")
        visiveis = [0] if cand.count() and cand.first.is_visible() else []
        expandir = cand
    if visiveis:
        expandir.nth(visiveis[0]).click(timeout=5000)
        page.wait_for_timeout(1500)
        box2 = drawer.bounding_box() or {}
        w2 = box2.get("width", 0)
        print(f"[19821] após expandir: {w2:.0f}px ({100*w2/VW:.0f}%)")
        tw.snap(page, PASTA, "19821-drawer-expandido")
        # tenta restaurar (mesmo botão, agora 'recolher/minimizar')
        rest = drawer.locator("button[aria-label*='ecolher' i], button[aria-label*='inimizar' i], [data-test-id*='collapse'], [data-test-id*='shrink']")
        if rest.count() and rest.first.is_visible():
            rest.first.click(timeout=4000); page.wait_for_timeout(1000)
    else:
        print("[19821] botão de expandir NÃO encontrado")
    # fechar o copiloto antes de seguir (portal intercepta cliques)
    try:
        page.locator(tid("copilot-drawer-close")).first.click(timeout=4000)
        page.wait_for_timeout(1000)
    except Exception:
        page.keyboard.press("Control+j"); page.wait_for_timeout(1500)

    # ---------- 19826: display_label na lista ----------
    print("\n### 19826 — lista reflete display_label")
    url_form = f"{c['base_url']}/o/{c['org_id']}/studio/activities/{ATIV}/edit?type=pdf&eventId={CURSO}"
    page.goto(url_form, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    campo = page.locator(tid("activity-appearance-displayLabel-input") + ":visible").first
    if not campo.count():
        campo = page.locator('[data-test-id*="displayLabel"]:visible, input[name*="display" i]:visible').first
    campo.scroll_into_view_if_needed()
    valor_antes = campo.input_value()
    print(f"[19826] valor atual do campo: {valor_antes!r}")
    campo.fill(LABEL_TESTE)
    page.get_by_role("button", name=re.compile("^Salvar", re.I)).first.click(timeout=8000)
    page.wait_for_timeout(3000)
    tw.snap(page, PASTA, "19826-form-salvo")

    page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
    page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(3000)
    card = page.locator(tid(f"creation-studio-activity-card-{ATIV}"))
    card.first.scroll_into_view_if_needed()
    texto_card = card.first.inner_text().replace("\n", " | ")
    reflete = LABEL_TESTE.lower() in texto_card.lower()
    print(f"[19826] card da atividade: {texto_card!r}")
    print(f"[19826] lista exibe '{LABEL_TESTE}'? {reflete}")
    tw.snap(page, PASTA, "19826-lista")

    # restaurar label original
    page.goto(url_form, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    campo = page.locator(tid("activity-appearance-displayLabel-input") + ":visible").first
    if not campo.count():
        campo = page.locator('[data-test-id*="displayLabel"]:visible, input[name*="display" i]:visible').first
    campo.scroll_into_view_if_needed()
    campo.fill(LABEL_ORIGINAL)
    page.get_by_role("button", name=re.compile("^Salvar", re.I)).first.click(timeout=8000)
    page.wait_for_timeout(3000)
    print(f"[19826] label restaurado para {LABEL_ORIGINAL!r}")

    # ---------- 19809: Criar curso com IA ----------
    print("\n### 19809 — Criar curso com IA")
    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    page.get_by_role("button", name=re.compile("Criar curso com IA", re.I)).first.click(timeout=8000)
    page.wait_for_timeout(4000)
    toast = page.get_by_text(re.compile("não foi habilitada|nao foi habilitada", re.I))
    bloqueado = toast.count() > 0 and toast.first.is_visible()
    corpo = page.evaluate("()=>document.body.innerText.slice(0,2000)")
    wizard = bool(re.search(r"(passo|etapa)\s*1|assistente|qual.{0,30}curso", corpo, re.I)) or "wizard" in page.url
    print(f"[19809] toast de bloqueio? {bloqueado} | indício de assistente aberto? {wizard} | url={page.url}")
    tw.snap(page, PASTA, "19809-criar-com-ia")

    print("\n=== FIM DO LOTE DESKTOP ===")
    ctx.close(); browser.close()
