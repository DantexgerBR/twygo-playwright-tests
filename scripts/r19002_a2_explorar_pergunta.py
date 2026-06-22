"""19002 — recon do form 'Adicionar pergunta' do questionario 73254."""
import re
import _twygo as tw

c = tw.cfg("")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"
QID = "73254"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{BASE}/o/{ORG}/question_lists/{QID}/edit", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    page.get_by_role("tab", name=re.compile("Pergunta", re.I)).first.click(timeout=5000)
    page.wait_for_timeout(1500)
    page.get_by_role("button", name=re.compile("Adicionar", re.I)).first.click(timeout=5000)
    page.wait_for_timeout(2500); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "A4-form-pergunta")
    print("URL:", page.url)
    # dump campos do form
    campos = page.evaluate(
        r"""() => {
            const vis = el => el.offsetParent !== null;
            const inputs = [...document.querySelectorAll('input,textarea,select,[contenteditable=true],[role=combobox]')]
                .filter(vis).map(e => ({tag:e.tagName, type:e.type||'', name:e.name||'', ph:e.placeholder||'', role:e.getAttribute('role')||''}));
            const labels = [...document.querySelectorAll('label,h2,h3,legend')].filter(vis)
                .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<60).slice(0,20);
            const radios = [...document.querySelectorAll('input[type=radio]')].filter(vis)
                .map(e=>{const l=e.closest('label,div');return l?(l.innerText||'').trim().slice(0,40):''}).filter(Boolean);
            const botoes = [...document.querySelectorAll('button')].filter(vis).map(b=>(b.innerText||'').trim()).filter(t=>t&&t.length<30).slice(0,20);
            return {inputs, labels, radios, botoes};
        }""")
    import json
    print(json.dumps(campos, ensure_ascii=False, indent=2))
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
