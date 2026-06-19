"""20224 prov passo 2: criar e PROGRAMAR ciclo com autoavaliacao usando o modelo."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")
MODELO = "QA 20224 modelo desempenho"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)

    # 1) Identificacao
    page.get_by_placeholder("Ex.: Ciclo Anual 2026").fill("QA 20224 autoavaliacao")
    d = page.locator("input[type=date]")
    d.nth(0).fill("2026-06-19"); d.nth(1).fill("2026-12-31")

    # 2) Avaliacoes: marcar Desempenho + selecionar modelo
    page.get_by_role("tab", name=re.compile("Avaliações", re.I)).first.click(); page.wait_for_timeout(1200)
    page.locator('[data-test-id="cycle-form-evaluation-card-performance"]').first.click(); page.wait_for_timeout(1200)
    # abrir dropdown "Selecionar modelo"
    page.get_by_text("Selecionar modelo", exact=True).first.click(); page.wait_for_timeout(1200)
    tw.snap(page, PASTA, "08-dropdown-modelo")
    opts = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=option],li,[role=menuitem]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,30)""")
    print("OPCOES MODELO:", opts)
    try:
        page.get_by_text(MODELO, exact=False).first.click(timeout=4000); page.wait_for_timeout(1000)
        print("modelo selecionado")
    except Exception as ex:
        print("erro selecionar modelo:", str(ex)[:120])

    # 3) Etapas: Auto-avaliacao + Resultado final
    page.get_by_role("tab", name=re.compile("Etapas", re.I)).first.click(); page.wait_for_timeout(1200)
    # dump data-test-ids p/ os cards
    tids = page.evaluate(r"""()=>Array.from(document.querySelectorAll('[data-test-id]')).map(e=>e.getAttribute('data-test-id')).filter(t=>/stage|auto|self|cycle-form|ponder|result/i.test(t))""")
    print("DATA-TEST-IDS etapas:", [*dict.fromkeys(tids)][:25])
    page.get_by_text("Auto-avaliação", exact=True).first.click(force=True); page.wait_for_timeout(1000)
    page.get_by_text("Cálculo automático ponderado", exact=True).first.click(force=True); page.wait_for_timeout(1000)
    tw.snap(page, PASTA, "09-etapas-preenchida", full=True)

    # 4) Configuracoes adicionais (participantes?)
    page.get_by_role("tab", name=re.compile("Configurações adicionais", re.I)).first.click(); page.wait_for_timeout(1500)
    tw.snap(page, PASTA, "10-config-adicionais", full=True)
    cfgtxt = page.evaluate(r"""()=>document.body.innerText.replace(/\n{2,}/g,'\n')""")
    i = cfgtxt.find("Configurações adicionais")
    print("CONFIG ADICIONAIS:", cfgtxt[i:i+500] if i>=0 else cfgtxt[:300])

    # 5) Salvar e programar
    page.get_by_role("button", name=re.compile("Salvar e programar", re.I)).first.click()
    page.wait_for_timeout(3500)
    print("URL pos-salvar:", page.url)
    toast = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast],[class*=error]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,8)""")
    print("TOAST/ERRO:", toast)
    tw.snap(page, PASTA, "11-pos-salvar-programar", full=True)

    ctx.close(); browser.close()
print("OK")
