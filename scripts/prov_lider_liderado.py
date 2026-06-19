"""33085519 lider->liderado: ciclo desempenho c/ etapa Avaliacao do lider + campanha (liderado=dante.tavares)."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "desempenho_seguir_33085519"
c = tw.cfg("")
LIDERADO = "dante.tavares@twygo.com"
MODELO = "QA 20224 modelo desempenho"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    # ===== CICLO =====
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    page.locator('[data-test-id="cycle-form-name-input"]').fill("QA 33085519 lider-liderado")
    d = page.locator("input[type=date]"); d.nth(0).fill("2026-06-19"); d.nth(1).fill("2026-12-31")
    page.locator('[data-test-id="cycle-form-tab-evaluations"]').click(); page.wait_for_timeout(1000)
    page.locator('[data-test-id="cycle-form-evaluation-card-performance"]').first.click(); page.wait_for_timeout(1000)
    page.get_by_text("Selecionar modelo", exact=True).last.click(); page.wait_for_timeout(1000)
    page.get_by_text(MODELO, exact=False).first.click(timeout=5000); page.wait_for_timeout(800)
    # Etapas: Avaliacao do lider
    page.locator('[data-test-id="cycle-form-tab-stages"]').click(); page.wait_for_timeout(1000)
    page.locator('[data-test-id="cycle-form-collection-type-leader-card"]').first.click(); page.wait_for_timeout(800)
    # Resultado: Adocao da nota do lider
    page.get_by_text("Adoção da nota do líder", exact=True).first.click(force=True); page.wait_for_timeout(800)
    page.get_by_role("button", name=re.compile("Salvar e programar", re.I)).first.click()
    page.wait_for_timeout(3500)
    print("TOAST ciclo:", page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast],[class*=error]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,5)"""))
    print("URL:", page.url)
    tw.snap(page, PASTA, "07-ciclo-lider-criado", full=True)
    m = re.search(r"/cycles/(\d+)", page.url); cid = m.group(1) if m else None
    print("CICLO ID:", cid)

    if cid:
        # ===== CAMPANHA (participante = liderado) =====
        page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/{cid}/campaigns/new", wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000); tw.dispensar_nps(page)
        page.locator('[data-test-id="campaign-form-name-input"]').fill("Campanha QA lider")
        tp = page.locator('[data-test-id="campaign-form-evaluation-type-performance"]')
        if tp.count(): tp.click()
        page.wait_for_timeout(500)
        page.locator('[data-test-id="campaign-form-tab-schedule"]').click(); page.wait_for_timeout(1200)
        dts = page.locator("input[type=date]")
        for i in range(dts.count()): dts.nth(i).fill("2026-06-19" if i%2==0 else "2026-12-31")
        page.locator('[data-test-id="campaign-form-tab-participants"]').click(); page.wait_for_timeout(1200)
        page.locator('[data-test-id="campaign-participant-selector-input"]').click(); page.wait_for_timeout(1200)
        page.get_by_placeholder(re.compile("Pesquise por nome", re.I)).fill(LIDERADO); page.wait_for_timeout(1800)
        try:
            page.locator("div").filter(has_text=LIDERADO).last.locator("input[type=checkbox]").last.check(timeout=4000)
        except Exception:
            page.get_by_text(LIDERADO).last.click()
        page.wait_for_timeout(700)
        page.get_by_role("button", name=re.compile(r"^Vincular$", re.I)).first.click(); page.wait_for_timeout(1500)
        page.locator('[data-test-id="campaign-form-submit-button"]').click(timeout=8000)
        page.wait_for_timeout(3500)
        print("TOAST campanha:", page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,5)"""))
        print("URL campanha:", page.url)
        m2 = re.search(r"/campaigns/(\d+)", page.url)
        print("CAMPANHA ID:", m2.group(1) if m2 else "?")
        tw.snap(page, PASTA, "07b-campanha-lider-criada", full=True)

    ctx.close(); browser.close()
print("OK")
