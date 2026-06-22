"""19002 — abrir o editor da atividade (no nao-salvo) no curso 807494.
Tecnica: add atividade -> hover na li.dd-item -> dd-edit click(force) -> se no-op,
dispatch mousedown+mouseup (jQuery nestable costuma ligar no mousedown)."""
import re, json
import _twygo as tw

c = tw.cfg("")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"
EID = "807494"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{BASE}/e/{EID}/contents", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(6000); tw.dispensar_nps(page)

    # adicionar atividade (cria 'Novo')
    page.evaluate("()=>{const el=[...document.querySelectorAll('a,button,div,span')].find(e=>/Adicionar atividade/i.test(e.innerText||'')&&e.offsetParent);if(el)el.click();}")
    page.wait_for_timeout(2000)
    row = page.locator("li.dd-item").first
    print("li.dd-item count:", page.locator("li.dd-item").count())
    edit = row.locator(".dd-edit").first

    url0 = page.url
    opened = False
    # 1) hover + force click
    try:
        row.hover(timeout=3000)
        edit.click(timeout=3000, force=True)
        page.wait_for_timeout(2500)
        opened = page.url != url0 or page.locator("select, .modal, [role=dialog]").filter(visible=True).count() > 0
        print("apos force click -> url:", page.url, "opened:", opened)
    except Exception as e:
        print("force click falhou:", e)
    # 2) dispatch mousedown+mouseup+click
    if not opened:
        try:
            edit.dispatch_event("mousedown"); page.wait_for_timeout(200)
            edit.dispatch_event("mouseup"); edit.dispatch_event("click")
            page.wait_for_timeout(2500)
            opened = page.url != url0 or page.locator("select, .modal, [role=dialog]").filter(visible=True).count() > 0
            print("apos dispatch -> url:", page.url, "opened:", opened)
        except Exception as e:
            print("dispatch falhou:", e)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "B8-editor-aberto")
    info = page.evaluate(
        r"""() => {
            const vis = el => el.offsetParent !== null;
            const selects=[...document.querySelectorAll('select')].filter(vis).map(s=>({name:s.name||s.id, opts:[...s.options].map(o=>o.text.trim()).slice(0,14)}));
            const labels=[...document.querySelectorAll('label,h2,h3,legend,.tab,.nav-link,a')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<35).slice(0,35);
            const inputs=[...document.querySelectorAll('input,textarea')].filter(vis).map(i=>({name:i.name,type:i.type,ph:i.placeholder})).slice(0,20);
            return {url:location.href, selects, labels, inputs};
        }""")
    print(json.dumps(info, ensure_ascii=False, indent=2))
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
