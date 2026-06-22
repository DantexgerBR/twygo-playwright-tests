"""19002 — abrir editor da atividade via HOVER REAL do mouse (CSS :hover revela o
dd-edit 0x0) + clique por coordenada. Curso 807494."""
import json
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

    page.evaluate("()=>{const el=[...document.querySelectorAll('a,button,div,span')].find(e=>/Adicionar atividade/i.test(e.innerText||'')&&e.offsetParent);if(el)el.click();}")
    page.wait_for_timeout(2000)

    row = page.locator("li.dd-item").first
    box = row.bounding_box()
    print("row box:", box)
    if box:
        # hover real no meio da linha -> CSS revela botoes da direita
        page.mouse.move(box["x"] + box["width"] - 60, box["y"] + box["height"]/2)
        page.wait_for_timeout(800)
        # medir dd-edit agora (deve ter tamanho)
        ddbox = page.evaluate(r"""()=>{const d=document.querySelector('li.dd-item .dd-edit');if(!d)return null;const r=d.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};}""")
        print("dd-edit box pos-hover:", ddbox)
        if ddbox and ddbox["w"] > 0:
            page.mouse.move(ddbox["x"] + ddbox["w"]/2, ddbox["y"] + ddbox["h"]/2)
            page.wait_for_timeout(300)
            page.mouse.click(ddbox["x"] + ddbox["w"]/2, ddbox["y"] + ddbox["h"]/2)
            page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    print("URL:", page.url)
    tw.snap(page, PASTA, "B9-editor-mouse")
    info = page.evaluate(
        r"""() => {
            const vis = el => el.offsetParent !== null;
            const selects=[...document.querySelectorAll('select')].filter(vis).map(s=>({name:s.name||s.id, opts:[...s.options].map(o=>o.text.trim()).slice(0,14)}));
            const labels=[...document.querySelectorAll('label,h2,h3,legend,.tab,.nav-link,a')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<35).slice(0,40);
            const inputs=[...document.querySelectorAll('input,textarea')].filter(vis).map(i=>({name:i.name,type:i.type,ph:i.placeholder})).slice(0,20);
            return {url:location.href, modal: !!document.querySelector('.modal:not([style*="display: none"]),[role=dialog]'), selects, labels, inputs};
        }""")
    print(json.dumps(info, ensure_ascii=False, indent=2))
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
