"""19002 — recon: adicionar atividade no curso 807494, abrir editor (lapis) e ver
campos (tipo Questionario, seletor de questionario, tentativas)."""
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

    # adicionar atividade (cria 'Novo N')
    page.evaluate("()=>{const el=[...document.querySelectorAll('a,button,div,span')].find(e=>/Adicionar atividade/i.test(e.innerText||'')&&e.offsetParent);if(el)el.click();}")
    page.wait_for_timeout(2500)

    # clicar no lapis (editar) do primeiro item da lista
    # icones costumam ter classe com 'edit'/'pencil' ou ser <a> dentro do <li>
    info_icons = page.evaluate(
        r"""() => {
            const li = document.querySelector('.dd-item, li[data-id], #content_list li, .list_content li, tbody tr');
            if (!li) return {found:false};
            const els = [...li.querySelectorAll('a,button,i,span,svg')].map(e=>({cls:(e.className||'').toString().slice(0,40), title:e.title||'', txt:(e.innerText||'').slice(0,15)})).filter(x=>x.cls||x.title||x.txt);
            return {found:true, html: li.outerHTML.slice(0,400), els};
        }""")
    print(json.dumps(info_icons, ensure_ascii=False, indent=2))

    # clicar no botao Editar (div.dd-edit)
    try:
        page.locator(".dd-item .dd-edit").first.click(timeout=5000)
        clicou = True
    except Exception as e:
        print("click .dd-edit falhou:", e)
        clicou = page.evaluate("()=>{const d=document.querySelector('.dd-item .dd-edit');if(d){d.click();return true;}return false;}")
    print("clicou editar:", clicou)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    print("URL:", page.url)
    tw.snap(page, PASTA, "B5-editor-atividade")
    campos = page.evaluate(
        r"""() => {
            const vis = el => el.offsetParent !== null;
            const selects = [...document.querySelectorAll('select')].filter(vis).map(s=>({name:s.name||s.id, opts:[...s.options].map(o=>o.text.trim()).slice(0,12)}));
            const labels = [...document.querySelectorAll('label,h2,h3,legend')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<50).slice(0,25);
            const inputs = [...document.querySelectorAll('input')].filter(vis).map(i=>({name:i.name,type:i.type,ph:i.placeholder})).slice(0,20);
            return {selects, labels, inputs};
        }""")
    print(json.dumps(campos, ensure_ascii=False, indent=2))
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
