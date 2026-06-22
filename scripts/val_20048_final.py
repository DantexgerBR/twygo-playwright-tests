import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "competencias_20048"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    # ===== FILTRO: opções de coluna =====
    page.goto(c["base_url"] + "/o/19653/succession_people_analysis", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4500)
    tw.dispensar_nps(page)
    page.get_by_text("Filtro", exact=False).first.click()
    page.wait_for_timeout(1500)
    page.get_by_role("button", name="Novo", exact=True).click()
    page.wait_for_timeout(2000)
    # combobox 'Colunas para filtrar' (react-select). Clicar no controle.
    try:
        page.locator("div.chakra-modal__content, aside, .chakra-slide").get_by_role("combobox").first.click(force=True)
    except Exception:
        page.mouse.click(1200, 228)
    page.wait_for_timeout(1500)
    tw.snap(page, PASTA, "FILTRO-opcoes-abertas")
    opts = page.evaluate(
        "()=>{const m=document.querySelectorAll('[role=option],[class*=menu] [class*=option],[id*=react-select] [role=option]');"
        "return Array.from(m).map(e=>(e.innerText||'').trim()).filter(Boolean);}"
    )
    print("OPÇÕES COLUNA:", opts)

    # ===== DRILL-DOWN Dashboard geral =====
    page.goto(c["base_url"] + "/o/19653/succession_dashboards", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    # links azuis em 'Funções com maior risco' — pegar âncoras/clicáveis dentro dos cards
    clicaveis = page.evaluate(
        "()=>Array.from(document.querySelectorAll('a,[role=link],[style*=cursor],td'))"
        ".map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim())"
        ".filter(t=>/risco|liderança|QA|equipe|gestor|especialista/i.test(t)&&t.length<50)"
    )
    print("\nCLICAVEIS dashboard:", sorted(set(clicaveis)))
    # clicar no nome de função 'QA' especificamente
    try:
        page.get_by_text("QA", exact=True).first.click(timeout=4000)
        page.wait_for_timeout(3000)
        print("Após clique QA -> url:", page.url)
        tw.snap(page, PASTA, "DRILL-QA")
        d = page.evaluate("()=>{const m=document.querySelector('.chakra-modal__content,[role=dialog],aside');return m&&m.offsetParent?(m.innerText||'').slice(0,400):'(sem painel)';}")
        print("painel:", d)
    except Exception as e:
        print("QA não clicável:", type(e).__name__)

    ctx.close(); browser.close()
