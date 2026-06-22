"""20224: explorar abas Cronograma e Quem participa da campanha."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/174/campaigns/new", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "16-add-campanha-identificacao", full=True)

    page.locator('[data-test-id="campaign-form-tab-schedule"]').click(); page.wait_for_timeout(1800)
    tw.snap(page, PASTA, "16b-cronograma", full=True)
    cron = page.evaluate(r"""()=>{const d=Array.from(document.querySelectorAll('input[type=date]')).length;const labs=[...new Set(Array.from(document.querySelectorAll('label')).map(l=>(l.innerText||'').trim()).filter(Boolean))].slice(0,15);return {nDate:d,labs};}""")
    print("CRONOGRAMA:", cron)

    page.locator('[data-test-id="campaign-form-tab-participants"]').click(); page.wait_for_timeout(1800)
    tw.snap(page, PASTA, "16c-quem-participa", full=True)
    part = page.evaluate(r"""()=>{
        const phs=[...new Set(Array.from(document.querySelectorAll('input,[role=combobox]')).map(e=>e.placeholder||e.getAttribute('aria-label')||'').filter(Boolean))];
        const btns=[...new Set(Array.from(document.querySelectorAll('button')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<30))];
        const tids=Array.from(document.querySelectorAll('[data-test-id]')).map(e=>e.getAttribute('data-test-id')).filter(t=>/participant|audience|user|add|search/i.test(t));
        const txt=(document.body.innerText||'').replace(/\n{2,}/g,'\n');const i=txt.search(/participa|colaborador|Adicionar/i);
        return {phs:phs.slice(0,15), btns:btns.slice(0,20), tids:[...new Set(tids)].slice(0,20), snippet:i>=0?txt.slice(i,i+400):''};
    }""")
    print("QUEM PARTICIPA inputs:", part["phs"])
    print("QUEM PARTICIPA btns:", part["btns"])
    print("QUEM PARTICIPA tids:", part["tids"])
    print("snippet:", part["snippet"])
    ctx.close(); browser.close()
print("OK")
