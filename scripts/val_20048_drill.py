import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "competencias_20048"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/succession_dashboards", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(5500)
    tw.dispensar_nps(page)

    # Inspecionar 'Funções com maior risco': cada função é link/clicável?
    info = page.evaluate(r"""()=>{
        const out=[];
        document.querySelectorAll('a,button,[role=button],[role=link]').forEach(e=>{
            const t=(e.innerText||'').replace(/\s+/g,' ').trim();
            if(t && t.length<60 && /risco|QA|equipe|gestor|especialista|liderança|ver todas|rr/i.test(t)){
                const cs=getComputedStyle(e);
                out.push({t, tag:e.tagName, href:e.getAttribute('href'), cursor:cs.cursor});
            }
        });
        // elementos com cursor pointer dentro dos cards de indicadores
        return out;
    }""")
    print("=== INDICADORES CLICAVEIS ===")
    for x in info:
        print(f"  [{x['tag']}] {x['t']!r} href={x['href']} cursor={x['cursor']}")

    # Tentar clicar 'Ver todas' (drill das funções de risco)
    try:
        page.get_by_text("Ver todas", exact=False).first.click(timeout=4000)
        page.wait_for_timeout(3000)
        print("\nApós 'Ver todas' -> url:", page.url)
        tw.snap(page, PASTA, "DRILL-ver-todas")
    except Exception as e:
        print("Ver todas:", type(e).__name__)

    # clicar no número de 'Ações' (indicador) ou no card 'Risco atual'
    try:
        page.get_by_text("Risco atual", exact=True).first.click(timeout=3000)
        page.wait_for_timeout(2000)
        tw.snap(page, PASTA, "DRILL-risco-atual")
        print("Após 'Risco atual' -> url:", page.url, "| painel:",
              page.evaluate("()=>{const m=document.querySelector('.chakra-modal__content,[role=dialog]');return m&&m.offsetParent?'ABRIU':'(nao)';}"))
    except Exception as e:
        print("Risco atual:", type(e).__name__)

    ctx.close(); browser.close()
