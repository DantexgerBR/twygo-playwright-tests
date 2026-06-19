"""Recon 19363 v5: expandir Gestao de Time via JS e ler submenu."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "filtros_dashboards_19363"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.wait_for_timeout(1500)

    # Clicar via JS no item de menu que contem "Gestão de Time"
    clicked = page.evaluate(r"""()=>{
        const el=Array.from(document.querySelectorAll('a,button,div,span,li')).find(e=>/Gest[aã]o de\s*Time/i.test((e.innerText||'')) && (e.innerText||'').length<40);
        if(!el) return false;
        const click=el.closest('a,button')||el; click.scrollIntoView({block:'center'}); click.click(); return true;
    }""")
    print("clicou Gestao de Time?", clicked)
    page.wait_for_timeout(2500)
    tw.snap(page, PASTA, "06-gestao-time-expandido")

    # Submenu: links que aparecem agora (qualquer rota nova)
    links = page.evaluate(r"""()=>Array.from(document.querySelectorAll('a[href]')).map(a=>({t:(a.innerText||'').replace(/\s+/g,' ').trim(),h:a.getAttribute('href')})).filter(x=>x.h&&x.h.includes('/o/36675/'))""")
    base = {'/o/36675/dashboard','/o/36675/events?tab=events','/o/36675/shared_events','/o/36675/records','/o/36675/certificate_models','/o/36675/content_models','/o/36675/knowledge_repositories','/o/36675/events/?tab=libraries','/o/36675/users','/o/36675/companies','/o/36675/exams','/o/36675/surveys','/o/36675/assessments','/o/36675/feed','/o/36675/organization_chart','/o/36675/roles','/o/36675/organization_chart_competencies','/o/36675/admin/pdis','/o/36675/cycles','/o/36675/feedback_log'}
    print("LINKS NOVOS (fora do conhecido):")
    for l in links:
        if l["h"] not in base and "/o/36675/" in l["h"]:
            print("  ", repr(l["t"]), "->", l["h"])

    ctx.close(); browser.close()
print("RECON OK")
