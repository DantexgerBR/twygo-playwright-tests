"""Headed check — observar comportamento real da tela de Registros.
Roda com TW_HEADED=1 para ver o que realmente carrega.
Faz timelapse de screenshots a cada 2s para 20s.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID   = os.environ.get("REGISTROSF2_ORG_ID", "37079")
ADMIN_EMAIL    = os.environ.get("REGISTROSF2_ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("REGISTROSF2_ADMIN_PASSWORD", "")

RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa12"
EVID.mkdir(parents=True, exist_ok=True)


# FORÇAR HEADED para observar
os.environ["TW_HEADED"] = "1"


with tw.sync_playwright() as p:
    # Usa nova_pagina que respeita TW_HEADED
    browser, ctx, page = tw.nova_pagina(p)

    # NÃO adicionar handler de dialog — deixar comportamento default
    # (console_check funcionou SEM handler de dialog)

    dialogs_vistos = []

    def on_dialog(d):
        dialogs_vistos.append(f"type={d.type} msg={d.message[:80]}")
        print(f"[dialog] Apareceu: type={d.type}, msg={d.message[:80]}")
        # NÃO aceitar automaticamente — deixar default (dismiss)
        d.dismiss()

    page.on("dialog", on_dialog)

    # Login
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    print(f"[headed] Pós-login: {page.url}")

    # Switch para admin via events
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    print(f"[headed] Pós-events switch: {page.url}")

    # Navegar para records via MENU (scroll_into_view + click)
    menu_registros = page.locator("a#records, a[href*='/records']").first
    print(f"[headed] Tentando scroll+click no menu 'Registros'")
    try:
        menu_registros.scroll_into_view_if_needed(timeout=5000)
        menu_registros.click(timeout=10000)
    except Exception as e:
        print(f"[headed] Falhou click menu ({e}), usando goto direto")
        page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)

    print(f"[headed] URL após nav: {page.url}")

    # Timelapse de screenshots a cada 2s por 20s
    print("[headed] Iniciando timelapse (10 screenshots x 2s)...")
    for i in range(10):
        page.wait_for_timeout(2000)
        spinner = page.locator(".chakra-spinner").count()
        table = page.locator("table").count()
        rows = page.locator("table tbody tr").count()
        body_text = page.locator("body").inner_text()
        tem_emitidos = "Emitidos" in body_text
        tem_provedores = "Provedores" in body_text
        tem_kpi = "Carga horária total" in body_text
        print(f"  t={2*(i+1)}s — spinner={spinner}, table={table}, rows={rows}, Emitidos={tem_emitidos}, Provedores={tem_provedores}, KPIs={tem_kpi}")
        tw.snap(page, EVID, f"timelapse_{i+1:02d}_t{2*(i+1)}s")

        # Se KPIs e Provedores já apareceram, parar
        if tem_emitidos and tem_provedores:
            print("[headed] Tela completa! Parando timelapse.")
            break

    print(f"\n[headed] Dialogs vistos: {dialogs_vistos}")

    # Estado final
    body_text = page.locator("body").inner_text()
    print(f"\n[headed] Estado final:")
    print(f"  Emitidos: {'Emitidos' in body_text}")
    print(f"  Provedores: {'Provedores' in body_text}")
    print(f"  Carga horária total: {'Carga horária total' in body_text}")
    print(f"  Ações em massa: {'Ações em massa' in body_text}")
    print(f"  Extrair dados: {'Extrair dados' in body_text}")

    btns = []
    for b in page.locator("button").all():
        t = b.inner_text().strip()[:30]
        if t and len(t) > 1:
            btns.append(t)
    print(f"  Botões: {btns[:20]}")

    tw.snap(page, EVID, "headed_final", full=True)

    ctx.close()
    browser.close()
