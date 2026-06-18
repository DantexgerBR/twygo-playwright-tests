"""Exploração: abrir edição de um conteúdo e achar a aba Dashboard (card 19792)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "facelift_dashboard_19792"
EVID = tw.ROOT / "evidencias" / SLUG
c = tw.cfg("GOATWY")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    EVID.mkdir(parents=True, exist_ok=True)

    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin", wait_until="domcontentloaded")
    page.wait_for_timeout(4000); tw.dispensar_nps(page)

    # clicar no primeiro nome de conteúdo (link da linha)
    primeiro = page.locator("table tbody tr").first
    print("linhas:", page.locator("table tbody tr").count())
    # tenta clicar no texto do nome
    nome_cell = primeiro.locator("td").nth(1)
    print("celula nome:", nome_cell.inner_text()[:50])
    nome_cell.click()
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print("URL após clicar conteúdo:", page.url)
    tw.snap(page, EVID, "01_apos_click_conteudo", full=True)

    # dump abas/tabs visíveis
    abas = page.evaluate(
        r"""()=>{
        const out=new Set();
        document.querySelectorAll('[role=tab],button,a').forEach(e=>{
            const t=(e.innerText||'').replace(/\s+/g,' ').trim();
            if(t && t.length<24 && /dashboard|aprendiz|geral|config|conteud|detal|identif|present|particip/i.test(t)) out.add(e.tagName+': '+t);
        });
        return [...out];
    }"""
    )
    print("ABAS candidatas:", abas)

    ctx.close(); browser.close()
print("\nFIM")
