"""19002 — adicionar atividade + Salvar (persiste id) + abrir editor da atividade.
Descobre o data-id e tenta editor via dd-edit (hover+force) e via URL direta."""
import re, json
import _twygo as tw

c = tw.cfg("")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"
EID = "807494"


def lista_ids(page):
    return page.evaluate("()=>Array.from(document.querySelectorAll('li.dd-item[data-id]')).map(li=>li.getAttribute('data-id'))")


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{BASE}/e/{EID}/contents", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(6000); tw.dispensar_nps(page)
    print("ids antes:", lista_ids(page))

    # adicionar
    page.evaluate("()=>{const el=[...document.querySelectorAll('a,button,div,span')].find(e=>/Adicionar atividade/i.test(e.innerText||'')&&e.offsetParent);if(el)el.click();}")
    page.wait_for_timeout(2000)
    # salvar
    page.evaluate("()=>{const el=[...document.querySelectorAll('a,button,div,span')].find(e=>/^\\s*Salvar\\s*$/i.test(e.innerText||'')&&e.offsetParent);if(el)el.click();}")
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print("URL apos salvar:", page.url)
    page.goto(f"{BASE}/e/{EID}/contents", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(6000); tw.dispensar_nps(page)
    ids = lista_ids(page)
    print("ids depois:", ids)
    tw.snap(page, PASTA, "B6-apos-salvar-lista")

    if ids:
        cid = ids[-1]
        print("editando atividade id:", cid)
        # hover na linha e clicar dd-edit (force)
        row = page.locator(f'li.dd-item[data-id="{cid}"]').first
        try:
            row.hover(timeout=3000)
        except Exception: pass
        try:
            row.locator(".dd-edit").first.click(timeout=4000, force=True)
            page.wait_for_timeout(3500)
        except Exception as e:
            print("dd-edit force falhou:", e)
        print("URL apos dd-edit:", page.url)
        # se nao navegou, tentar campo 'Digite o id para editar' + Ir
        if "/contents" in page.url and "edit" not in page.url and not re.search(r"/contents/\d+", page.url):
            try:
                inp = page.get_by_placeholder(re.compile("Digite o id", re.I)).first
                inp.fill(cid);
                page.evaluate("()=>{const el=[...document.querySelectorAll('a,button')].find(e=>/^\\s*Ir\\s*$/i.test(e.innerText||'')&&e.offsetParent);if(el)el.click();}")
                page.wait_for_timeout(3500)
            except Exception as e:
                print("Ir falhou:", e)
        print("URL final:", page.url)
        tw.snap(page, PASTA, "B7-editor-atividade")
        campos = page.evaluate(
            r"""() => {
                const vis = el => el.offsetParent !== null;
                const selects = [...document.querySelectorAll('select')].filter(vis).map(s=>({name:s.name||s.id, opts:[...s.options].map(o=>o.text.trim()).slice(0,12)}));
                const labels = [...document.querySelectorAll('label,h2,h3,legend,.tab,.nav-link')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<40).slice(0,30);
                return {url:location.href, selects, labels};
            }""")
        print(json.dumps(campos, ensure_ascii=False, indent=2))
        # persistir
        IDS = PASTA / "_ids.json"
        data = json.loads(IDS.read_text(encoding="utf-8")) if IDS.exists() else {}
        data["atividade_id"] = cid
        IDS.write_text(json.dumps(data, indent=2), encoding="utf-8")
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
