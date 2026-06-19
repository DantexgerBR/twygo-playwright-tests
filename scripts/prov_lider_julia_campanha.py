"""33085519 lider->liderado: nova campanha no ciclo 178 com JULIA (liderada da Adriana)."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "desempenho_seguir_33085519"
c = tw.cfg("")
LIDERADO = "julia@sophia.tech.com.br"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/178/campaigns/new", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    page.locator('[data-test-id="campaign-form-name-input"]').fill("Campanha QA lider Julia")
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
    print("TOAST:", page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,5)"""))
    print("URL:", page.url)
    m = re.search(r"/campaigns/(\d+)", page.url); print("CAMPANHA ID:", m.group(1) if m else "?")
    tw.snap(page, PASTA, "15-campanha-lider-julia", full=True)
    # status (auto-ativa? ciclo 178 ja ativo)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/178/campaigns", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(3000)
    print("CAMPANHAS 178:", page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/Campanha QA lider/i.test(t))"""))
    ctx.close(); browser.close()
print("OK")
