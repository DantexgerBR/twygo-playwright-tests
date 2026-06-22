"""Recon10 — login e ir DIRETO para records (sem events/switch) + aguardar stats."""
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


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    page.on("dialog", lambda d: (print(f"[dialog] {d.type}: {d.message[:80]}"), d.accept()))

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
    print(f"[recon10] Pós-login URL: {page.url}")

    # Ir DIRETO para records (sem events)
    print("[recon10] Goto /records direto (sem events)")
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    print(f"[recon10] URL após goto: {page.url}")

    # Aguardar stats e records
    stats_recebidas = False
    try:
        with page.expect_response(
            lambda r: f"/records/stats" in r.url and r.status == 200,
            timeout=20000
        ) as stats_info:
            pass
        stats = stats_info.value.json()
        print(f"[recon10] Stats: {stats.get('data', {}).get('by_status', {})}")
        stats_recebidas = True
    except Exception as e:
        print(f"[recon10] Timeout stats: {e}")

    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=15000
        ):
            pass
        print("[recon10] Records API respondeu")
    except Exception:
        pass

    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    spinner = page.locator(".chakra-spinner").count()
    table = page.locator("table").count()
    rows = page.locator("table tbody tr").count()
    print(f"\n[recon10] spinner={spinner}, table={table}, rows={rows}")

    body = page.locator("body").inner_text()
    print(f"[recon10] Emitidos: {'Emitidos' in body}")
    print(f"[recon10] Provedores: {'Provedores' in body}")
    print(f"[recon10] Carga horária total: {'Carga horária total' in body}")
    print(f"[recon10] Ações em massa: {'Ações em massa' in body}")

    btns = []
    for b in page.locator("button").all():
        t = b.inner_text().strip()[:30]
        if t and len(t) > 1:
            btns.append(t)
    print(f"[recon10] Botões: {btns[:20]}")

    tw.snap(page, EVID, "recon10_direto", full=True)

    # Se ainda no /dashboard_students, é aluno - precisa troca de perfil
    if "/dashboard_students" in page.url:
        print("[recon10] Redirecionou para dashboard_students (aluno) - precisa switch admin")

    ctx.close()
    browser.close()
