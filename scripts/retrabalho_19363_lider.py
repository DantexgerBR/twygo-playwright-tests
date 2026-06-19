"""19363: confirmar coluna 'Colaborador' no filtro da dashboard de competencias do LIDER."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "filtros_dashboards_19363"
c = tw.cfg("")
ca = dict(c); ca["email"] = "adriana@twygo.com"; ca["senha"] = "123456"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, ca, admin=False)
    page.wait_for_timeout(2500)
    try:
        b = page.get_by_role("button", name=re.compile(r"^Aceitar$", re.I)).first
        if b.count() and b.is_visible(): b.click(); page.wait_for_timeout(1000)
    except Exception: pass

    page.goto(f"{c['base_url']}/o/{c['org_id']}/organization_chart_competencies?as_team_manager=true",
              wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)

    page.get_by_role("button", name=re.compile("Filtro", re.I)).first.click(timeout=5000); page.wait_for_timeout(1200)
    page.get_by_text("Novo", exact=True).first.click(timeout=4000); page.wait_for_timeout(1200)
    page.get_by_role("button", name=re.compile("Op[cç][õo]es de filtro", re.I)).first.click(timeout=4000)
    page.wait_for_timeout(1500)
    tw.snap(page, PASTA, "18-adriana-colunas-filtro")

    # dump das colunas: itens do dropdown aberto (checkbox labels curtos)
    cols = page.evaluate(r"""()=>{
        const cands=Array.from(document.querySelectorAll('label,[role=option],[role=menuitem],li'))
          .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim())
          .filter(t=>t && t.length<25 && /^(Área|Area|Função|Funcao|Gestor|Colaborador|Cargo|Empresa|Time|Equipe|Período|Periodo)$/i.test(t));
        return [...new Set(cands)];
    }""")
    print("COLUNAS FILTRO LIDER:", cols)
    print("TEM COLABORADOR?", any(re.match(r"colaborador", x, re.I) for x in cols))

    ctx.close(); browser.close()
print("OK")
