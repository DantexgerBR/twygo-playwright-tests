"""Diag: o sistema reconhece Adriana como avaliadora (lider direto) da Julia no ciclo 178?"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "desempenho_seguir_33085519"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    # Status dos times (admin) - filtrar pelo ciclo 178
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles?profile=admin", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    page.get_by_text("Status dos times", exact=False).first.click(timeout=5000); page.wait_for_timeout(3000)
    tw.snap(page, PASTA, "19-status-times-todos", full=True)
    # dump linhas com colaborador/lider/campanha/status
    rows = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/Julia|Dante|Adriana|lider|Campanha QA lider|Inici|Conclu|pendente|A iniciar/i.test(t)).slice(0,25)""")
    print("STATUS TIMES:")
    for r in rows: print("  ", r)

    # Detalhe da campanha 194 (participantes + lider resolvido)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/178/campaigns/194/edit", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(3000)
    print("\nURL camp194 edit:", page.url)
    tw.snap(page, PASTA, "20-camp194-detalhe", full=True)
    # ver participantes/quem participa
    try:
        page.locator('[data-test-id="campaign-form-tab-participants"]').click(); page.wait_for_timeout(1500)
        part = page.evaluate(r"""()=>{const b=(document.body.innerText||'').replace(/\n{2,}/g,'\n');const i=b.search(/Participante|Julia|lider/i);return b.slice(i, i+400);}""")
        print("PARTICIPANTES:", part[:400])
    except Exception as ex:
        print("erro participantes:", str(ex)[:80])

    # Organograma: Julia tem lider direto?
    page.goto(f"{c['base_url']}/o/{c['org_id']}/organization_chart?profile=admin", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "21-organograma", full=True)
    org = page.evaluate(r"""()=>{const b=(document.body.innerText||'').replace(/\n{2,}/g,'\n');const i=b.search(/Julia|Adriana|Organograma/i);return b.slice(i, i+500);}""")
    print("\nORGANOGRAMA:", org[:500])
    ctx.close(); browser.close()
print("OK")
