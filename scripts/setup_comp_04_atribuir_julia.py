"""Setup: atribuir Julia a funcao 'rh' (roles/1452) na aba Pessoas atribuidas."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/roles/1452/edit", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    page.locator('[data-test-id="tab-assigned-people"]').click(); page.wait_for_timeout(2000)
    tw.snap(page, PASTA, "32-pessoas-atribuidas", full=True)
    btns = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('button,a')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<30&&/Adicionar|Vincular|Atribuir|pessoa|Incluir/i.test(t)))]""")
    print("BTNS:", btns)
    # clicar botao de adicionar pessoa
    clicked = False
    for nome in ["Adicionar", "Vincular", "Atribuir", "Incluir"]:
        b = page.get_by_role("button", name=re.compile(nome, re.I))
        if b.count() and b.first.is_visible():
            b.first.click(); clicked = True; print("clicou:", nome); break
    page.wait_for_timeout(1800)
    tw.snap(page, PASTA, "33-add-pessoa-drawer")
    # buscar Julia (drawer estilo Vincular pessoas)
    busca = page.get_by_placeholder(re.compile("Pesquise por nome|nome ou e-mail|Pesquisar", re.I))
    if busca.count():
        busca.first.fill("julia@sophia.tech.com.br"); page.wait_for_timeout(1800)
        try:
            page.locator("div").filter(has_text="julia@sophia.tech.com.br").last.locator("input[type=checkbox]").last.check(timeout=4000)
        except Exception:
            page.get_by_text("julia@sophia.tech.com.br").last.click()
        page.wait_for_timeout(700)
        vinc = page.get_by_role("button", name=re.compile(r"^(Vincular|Adicionar|Confirmar)$", re.I))
        if vinc.count(): vinc.first.click(); page.wait_for_timeout(1500)
    else:
        print("sem campo de busca; inputs:", page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('input')).map(i=>i.placeholder||i.getAttribute('aria-label')||i.type))].slice(0,12)"""))
    tw.snap(page, PASTA, "34-julia-atribuida")
    # salvar funcao
    page.locator('[data-test-id="organization-chart-role-edit-save-button"]').click(); page.wait_for_timeout(2500)
    toast = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,5)""")
    print("TOAST:", toast)
    print("URL:", page.url)
    ctx.close(); browser.close()
print("OK")
