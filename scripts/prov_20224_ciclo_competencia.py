"""20224: ciclo+campanha de COMPETENCIAS com Julia (autoavaliacao)."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")
MODELO = "QA 20224 modelo competencias"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    # ===== CICLO =====
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    page.locator('[data-test-id="cycle-form-name-input"]').fill("QA 20224 competencias")
    d = page.locator("input[type=date]")
    d.nth(0).fill("2026-06-19"); d.nth(1).fill("2026-12-31")
    page.locator('[data-test-id="cycle-form-tab-evaluations"]').click(); page.wait_for_timeout(1200)
    page.locator('[data-test-id="cycle-form-evaluation-card-competency"]').first.click(); page.wait_for_timeout(1200)
    # selecionar modelo de competencia
    page.get_by_text("Selecionar modelo", exact=True).last.click(); page.wait_for_timeout(1000)
    tw.snap(page, PASTA, "22-ciclo-comp-modelo-dropdown")
    page.get_by_text(MODELO, exact=False).first.click(timeout=5000); page.wait_for_timeout(800)
    print("modelo competencia selecionado")
    # Etapas
    page.locator('[data-test-id="cycle-form-tab-stages"]').click(); page.wait_for_timeout(1200)
    page.get_by_text("Auto-avaliação", exact=True).first.click(force=True); page.wait_for_timeout(800)
    page.get_by_text("Cálculo automático ponderado", exact=True).first.click(force=True); page.wait_for_timeout(800)
    page.get_by_role("button", name=re.compile("Salvar e programar", re.I)).first.click()
    page.wait_for_timeout(3500)
    print("URL pos-ciclo:", page.url)
    print("TOAST ciclo:", page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,4)"""))
    m = re.search(r"/cycles/(\d+)", page.url)
    cid = m.group(1) if m else None
    print("CICLO ID:", cid)
    tw.snap(page, PASTA, "22b-ciclo-comp-criado")

    if cid:
        # ===== CAMPANHA =====
        page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/{cid}/campaigns/new", wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000); tw.dispensar_nps(page)
        page.locator('[data-test-id="campaign-form-name-input"]').fill("Campanha QA 20224 comp")
        # tipo competencia
        tipo = page.locator('[data-test-id="campaign-form-evaluation-type-competency"]')
        if tipo.count(): tipo.click(); print("tipo competency marcado")
        else:
            tids = page.evaluate(r"""()=>Array.from(document.querySelectorAll('[data-test-id]')).map(e=>e.getAttribute('data-test-id')).filter(t=>/evaluation-type/i.test(t))""")
            print("tipos disponiveis:", [*dict.fromkeys(tids)])
        page.wait_for_timeout(500)
        # cronograma
        page.locator('[data-test-id="campaign-form-tab-schedule"]').click(); page.wait_for_timeout(1200)
        dts = page.locator("input[type=date]")
        for i in range(dts.count()):
            dts.nth(i).fill("2026-06-19" if i % 2 == 0 else "2026-12-31")
        # participante Julia
        page.locator('[data-test-id="campaign-form-tab-participants"]').click(); page.wait_for_timeout(1200)
        page.locator('[data-test-id="campaign-participant-selector-input"]').click(); page.wait_for_timeout(1200)
        page.get_by_placeholder(re.compile("Pesquise por nome", re.I)).fill("julia@sophia.tech.com.br"); page.wait_for_timeout(1800)
        try:
            page.locator("div").filter(has_text="julia@sophia.tech.com.br").last.locator("input[type=checkbox]").last.check(timeout=4000)
        except Exception:
            page.get_by_text("julia@sophia.tech.com.br").last.click()
        page.wait_for_timeout(700)
        page.get_by_role("button", name=re.compile(r"^Vincular$", re.I)).first.click(); page.wait_for_timeout(1500)
        page.locator('[data-test-id="campaign-form-submit-button"]').click(timeout=8000)
        page.wait_for_timeout(3500)
        print("TOAST campanha:", page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,4)"""))
        print("URL campanha:", page.url)
        tw.snap(page, PASTA, "22c-campanha-comp-criada")

    ctx.close(); browser.close()
print("OK")
