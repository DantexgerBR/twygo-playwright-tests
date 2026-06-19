"""20224: o que a Avaliacao de Competencias exige? (modelo vs competencias definidas)
+ explorar Lista de competencias / Funcoes de negocio p/ setup minimo."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    # 1) Avaliacoes do ciclo: clicar competency card e ver o que aparece
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    page.locator('[data-test-id="cycle-form-tab-evaluations"]').click(); page.wait_for_timeout(1200)
    page.locator('[data-test-id="cycle-form-evaluation-card-competency"]').first.click(); page.wait_for_timeout(1500)
    tw.snap(page, PASTA, "23-competency-card-expandido", full=True)
    comp = page.evaluate(r"""()=>{
        const card=document.querySelector('[data-test-id="cycle-form-evaluation-card-competency"]');
        const t=card?(card.innerText||'').replace(/\s+/g,' ').trim():'(sem card)';
        const tids=Array.from(document.querySelectorAll('[data-test-id]')).map(e=>e.getAttribute('data-test-id')).filter(x=>/competency/i.test(x));
        return {cardTxt:t.slice(0,300), tids:[...new Set(tids)]};
    }""")
    print("COMPETENCY CARD:", comp["cardTxt"])
    print("COMPETENCY TIDS:", comp["tids"])

    # 2) Lista de competencias (definicao)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/organization_chart_competencies?profile=admin", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    try:
        page.get_by_text("Lista de competências", exact=False).first.click(timeout=4000); page.wait_for_timeout(2500)
    except Exception as ex:
        print("erro aba lista:", str(ex)[:80])
    tw.snap(page, PASTA, "24-lista-competencias", full=True)
    lc = page.evaluate(r"""()=>{
        const btns=[...new Set(Array.from(document.querySelectorAll('button,a')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<30&&/Adicionar|Nova|competenc|Import|Criar/i.test(t)))];
        const body=(document.body.innerText||'').replace(/\n{2,}/g,'\n');const i=body.search(/compet[eê]ncia/i);
        return {btns, snippet:i>=0?body.slice(i,i+400):body.slice(0,300)};
    }""")
    print("LISTA COMPETENCIAS btns:", lc["btns"])
    print("snippet:", lc["snippet"])
    ctx.close(); browser.close()
print("OK")
