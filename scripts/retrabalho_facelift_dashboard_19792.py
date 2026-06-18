"""Validação card 19792 [Facelift] - aba Dashboard da edição de Conteúdo.

Esperado (PR 10629): dashboards TODOS visíveis por padrão; botão 'Mostrar/Esconder
Dashboard' NÃO existe mais (removido Collapse + i18n dashboard.show/hide).

Fluxo: Aprendizagem > Conteúdos > editar curso > aba 'Dashboard'.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "facelift_dashboard_19792"
EVID = tw.ROOT / "evidencias" / SLUG
c = tw.cfg("GOATWY")


def descobrir_segundo_id(page):
    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin", wait_until="domcontentloaded")
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    # abre 2a linha pra capturar o id pela URL
    page.locator("table tbody tr").nth(1).locator("td").nth(1).click()
    page.wait_for_timeout(4000)
    import re as _re
    m = _re.search(r"/contents/(\d+)/", page.url)
    return m.group(1) if m else None


def validar(page, content_id, snap_nome):
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{content_id}/edit?tab=dashboard",
              wait_until="domcontentloaded")
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print("\nURL:", page.url)
    try:
        page.get_by_role("button", name="Dashboard", exact=True).first.click()
        page.wait_for_timeout(2500)
    except Exception:
        pass
    tw.dispensar_nps(page)
    tw.snap(page, EVID, snap_nome, full=True)
    # 1) Procurar botão 'Mostrar/Esconder Dashboard' (texto que deveria ter sido removido)
    botoes_show_hide = page.evaluate(
        r"""()=>{
        const out=[];
        document.querySelectorAll('button,a,[role=button]').forEach(e=>{
            const t=(e.innerText||e.getAttribute('aria-label')||'').replace(/\s+/g,' ').trim();
            if(/mostrar dashboard|esconder dashboard|exibir dashboard|ocultar dashboard|show dashboard|hide dashboard/i.test(t))
                out.push(t);
        });
        return out;
    }"""
    )

    # 2) Contar dashboards/cards visíveis e detectar Collapse colapsado
    dash_info = page.evaluate(
        r"""()=>{
        // procura blocos de dashboard (canvas/iframe/cards de grafico). Heuristica ampla.
        const charts = document.querySelectorAll('canvas, svg.recharts-surface, .recharts-wrapper, [class*=dashboard]');
        // Chakra Collapse colapsado costuma ter height:0 / display:none no .chakra-collapse
        const collapses = Array.from(document.querySelectorAll('.chakra-collapse'));
        const colapsados = collapses.filter(el=>{
            const cs=getComputedStyle(el);
            return cs.height==='0px' || cs.display==='none' || el.offsetHeight===0;
        }).length;
        // textos visiveis na area
        const titulos=[];
        document.querySelectorAll('h2,h3,h4,.chakra-heading,[class*=title]').forEach(h=>{
            const t=(h.innerText||'').replace(/\s+/g,' ').trim();
            if(t && t.length<50) titulos.push(t);
        });
        return {nCharts:charts.length, nCollapses:collapses.length, nColapsados:colapsados,
                titulos:[...new Set(titulos)].slice(0,20)};
    }"""
    )

    print(f"=== RESULTADO conteúdo {content_id} ===")
    print("Botão 'Mostrar/Esconder Dashboard' encontrado:", botoes_show_hide or "NENHUM (esperado)")
    print("Charts/cards detectados:", dash_info["nCharts"])
    print("Chakra collapses:", dash_info["nCollapses"], "| colapsados (ocultos):", dash_info["nColapsados"])
    print("Títulos visíveis na aba:", dash_info["titulos"][:14])
    return {"id": content_id, "btn": botoes_show_hide, "charts": dash_info["nCharts"],
            "colapsados": dash_info["nColapsados"]}


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    EVID.mkdir(parents=True, exist_ok=True)

    r1 = validar(page, "787735", "10_aba_dashboard")
    id2 = descobrir_segundo_id(page)
    r2 = validar(page, id2, "11_aba_dashboard_conteudo2") if id2 and id2 != "787735" else None

    print("\n\n############ RESUMO 19792 ############")
    for r in (r1, r2):
        if not r:
            continue
        ok = (not r["btn"]) and r["colapsados"] == 0 and r["charts"] > 0
        print(f"  conteúdo {r['id']}: botão show/hide={r['btn'] or 'ausente'} | colapsados={r['colapsados']} | charts={r['charts']} -> {'OK' if ok else 'FALHOU'}")

    ctx.close(); browser.close()
print("\nFIM validação 19792")
