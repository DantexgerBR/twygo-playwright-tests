"""20224 prov passo 3 (v2): criar campanha com Julia (drawer Vincular pessoas)."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/174/campaigns/new", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)

    # 1) Identificacao
    page.locator('[data-test-id="campaign-form-name-input"]').fill("Campanha QA 20224")
    page.locator('[data-test-id="campaign-form-evaluation-type-performance"]').click(); page.wait_for_timeout(800)

    # 2) Cronograma
    page.locator('[data-test-id="campaign-form-tab-schedule"]').click(); page.wait_for_timeout(1500)
    dts = page.locator("input[type=date]")
    for i in range(dts.count()):
        dts.nth(i).fill("2026-06-19" if i % 2 == 0 else "2026-12-31")
    page.wait_for_timeout(400)

    # 3) Quem participa -> drawer Vincular pessoas
    page.locator('[data-test-id="campaign-form-tab-participants"]').click(); page.wait_for_timeout(1200)
    page.locator('[data-test-id="campaign-participant-selector-input"]').click(); page.wait_for_timeout(1200)
    busca = page.get_by_placeholder(re.compile("Pesquise por nome", re.I))
    busca.fill("julia@sophia.tech.com.br"); page.wait_for_timeout(1800)
    tw.snap(page, PASTA, "17c-vincular-busca")
    # marcar checkbox da Julia (card que contem o email)
    card = page.locator("div").filter(has_text="julia@sophia.tech.com.br").last
    cb = card.locator("input[type=checkbox]").last
    try:
        cb.check(timeout=4000)
    except Exception:
        # fallback: clicar no card
        page.get_by_text("julia@sophia.tech.com.br", exact=False).last.click()
    page.wait_for_timeout(800)
    tw.snap(page, PASTA, "17d-julia-marcada")
    # Vincular
    page.get_by_role("button", name=re.compile(r"^Vincular$", re.I)).first.click(); page.wait_for_timeout(1500)
    tw.snap(page, PASTA, "17e-participante-vinculado", full=True)

    # 4) Criar campanha
    page.locator('[data-test-id="campaign-form-submit-button"]').click(timeout=8000)
    page.wait_for_timeout(3500)
    print("URL pos-criar:", page.url)
    toast = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast],[class*=error]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,8)""")
    print("TOAST:", toast)
    tw.snap(page, PASTA, "18-camp-pos-criar", full=True)
    ctx.close(); browser.close()
print("OK")
