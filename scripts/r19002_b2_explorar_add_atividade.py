"""19002 — recon: clicar 'Adicionar atividade' no curso 807494 e ver o form/tipos."""
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

    print("iframes:", [f.url for f in page.frames])
    # 'Adicionar atividade' pode ser <a>/<div> (markup legado) — clicar por texto
    clicou = False
    for loc in [page.get_by_text("Adicionar atividade", exact=True),
                page.locator("a,button,div,span").filter(has_text=re.compile("Adicionar atividade", re.I))]:
        try:
            loc.first.click(timeout=5000); clicou = True; print("[ok] cliquei Adicionar atividade"); break
        except Exception as e:
            print(f"[tentativa] {e.__class__.__name__}")
    if not clicou:
        # via JS: achar elemento com o texto e clicar
        page.evaluate("()=>{const el=[...document.querySelectorAll('a,button,div,span')].find(e=>/Adicionar atividade/i.test(e.innerText||'')&&e.offsetParent);if(el)el.click();}")
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    print("URL:", page.url)
    tw.snap(page, PASTA, "B4-add-atividade")
    # dump de selects/opcoes de tipo e campos
    info = page.evaluate(
        r"""() => {
            const vis = el => el.offsetParent !== null;
            const selects = [...document.querySelectorAll('select')].filter(vis).map(s=>({name:s.name||s.id, opts:[...s.options].map(o=>o.text.trim()).slice(0,15)}));
            const labels = [...document.querySelectorAll('label,h2,h3,legend,.modal-title')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<50).slice(0,25);
            const tiles = [...document.querySelectorAll('[class*=tipo],[class*=type],[class*=kind],.card,.option,a,button')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/question|prova|quiz|v[ií]deo|texto|arquivo|scorm|link|p[aá]gina|imagem/i.test(t)).slice(0,20);
            const inputs = [...document.querySelectorAll('input')].filter(vis).map(i=>({name:i.name,type:i.type,ph:i.placeholder})).slice(0,15);
            return {selects, labels, tiles, inputs};
        }""")
    print(json.dumps(info, ensure_ascii=False, indent=2))
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
