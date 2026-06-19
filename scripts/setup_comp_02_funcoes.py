"""Setup competencias: funcoes de negocio (quais tem competencias) + usuarios."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/roles?profile=admin", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "29-funcoes-negocio", full=True)
    rows = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&!/^Fun[cç]/.test(t)).slice(0,20)""")
    print("FUNCOES (linhas):", rows)
    # tambem a estrutura do organograma (quem esta em qual area/funcao)
    print("\n--- Matriz de versatilidade (pessoas x competencias) ---")
    page.goto(f"{c['base_url']}/o/{c['org_id']}/organization_chart_competencies?profile=admin&tab=versatility", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "30-matriz-versatilidade", full=True)
    mv = page.evaluate(r"""()=>{const b=(document.body.innerText||'').replace(/\n{2,}/g,'\n');const i=b.search(/Matriz|versatil/i);return b.slice(i, i+500);}""")
    print(mv[:500])
    ctx.close(); browser.close()
print("OK")
