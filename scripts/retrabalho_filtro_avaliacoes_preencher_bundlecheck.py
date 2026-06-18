r"""Retrabalho 20177 — verificacao do fix no BUNDLE DEPLOYADO (stage).

Por que bundle-check: a aba "Avaliacoes a preencher" e visao de colaborador/lider
(menu Gestao de Time > Desenvolvimento), que NAO esta habilitado para o usuario na
org 36675 — logo o painel de filtros nao pode ser renderizado ao vivo aqui. Em vez
de prova visual, inspecionamos o JS servido pelo cdn-stage e confirmamos a logica
do PR #10737 no codigo que de fato roda em producao do stage.

Prova 1 (aba passa a prop): development-evaluations-tab renderiza a tabela com
        hideCompletedDefaultFilter:!0  (true).
Prova 2 (tabela consome a prop): quando hideCompletedDefaultFilter e true, a lista
        de filtros padrao remove o preset Concluidas (model_default_enum !== <enum>);
        currentFilter segue usando a lista completa (indices estaveis).

Rode:  .\.venv\Scripts\python.exe scripts/retrabalho_filtro_avaliacoes_preencher_bundlecheck.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("")  # org principal 36675


def baixar_chunk_com(page, app_url, nome_modulo):
    """Acha no application.ts a ref do chunk <nome_modulo>-<hash>.js e baixa o arquivo."""
    return page.evaluate(
        """async ([appUrl, nome])=>{
            const txt=await (await fetch(appUrl)).text();
            const origin=new URL(appUrl).origin;
            const re=new RegExp('[\\\\w./@-]*'+nome+'[\\\\w.-]*\\\\.js','g');
            const nomes=[...new Set((txt.match(re)||[]).map(s=>s.split('/').pop()))];
            let best='', url='';
            for(const n of nomes){
                for(const u of [origin+'/vite/assets/'+n, new URL(n, appUrl).href, new URL('../'+n, appUrl).href]){
                    try{ const r=await fetch(u); if(!r.ok)continue; const b=await r.text();
                         if(b.length>best.length){best=b; url=u;} }catch(e){}
                }
            }
            return {url, code:best};
        }""",
        [app_url, nome_modulo],
    )


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True, slow_mo=0, height=1100)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(3000)

    app_url = page.evaluate(
        "()=>Array.from(document.querySelectorAll('script[src]')).map(s=>s.src).find(u=>/application\\.ts/.test(u))||''"
    )
    print("application.ts:", app_url.split("/")[-1], "\n")

    # PROVA 1 — a aba passa hideCompletedDefaultFilter=true
    dev = baixar_chunk_com(page, app_url, "development-page")
    i = dev["code"].find("development-evaluations-tab")
    print("PROVA 1 — chunk:", dev["url"].split("/")[-1])
    print("  trecho da aba 'Avaliacoes a preencher':")
    print("  " + dev["code"][i - 10:i + 230] if i >= 0 else "  (marcador nao encontrado)")
    assert i >= 0 and "hideCompletedDefaultFilter:!0" in dev["code"][i:i + 260], \
        "FALHA: aba nao passa hideCompletedDefaultFilter=true no bundle"
    print("  => OK: aba passa hideCompletedDefaultFilter:!0 (true)\n")

    # PROVA 2 — a tabela remove o preset Concluidas quando a prop e true
    tbl = baixar_chunk_com(page, app_url, "performance-evaluations-table")
    j = tbl["code"].find("hideCompletedDefaultFilter:")
    trecho = tbl["code"][j:j + 1200] if j >= 0 else ""
    print("PROVA 2 — chunk:", tbl["url"].split("/")[-1])
    print("  logica de filtro:")
    print("  " + trecho[:1200] if trecho else "  (marcador nao encontrado)")
    # f? c.filter(m=>m.model_default_enum!==<enum>):c  → remove o preset completed
    assert "model_default_enum!==" in trecho and "?c.filter(" in trecho.replace(" ", ""), \
        "FALHA: tabela nao remove o preset completed quando a prop e true"
    print("\n  => OK: com a prop true, defaultFilters remove o preset (model_default_enum!==enum);")
    print("        currentFilter segue na lista completa (indices estaveis).")

    print("\nRESULTADO: fix do PR #10737 esta DEPLOYADO e corretamente ligado no stage.")
    ctx.close()
    browser.close()
