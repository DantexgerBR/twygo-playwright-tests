import sys, re
from pathlib import Path
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "funcao_dup_19489"
c = tw.cfg("MIGR")


def ler_lista(page, tag):
    page.wait_for_timeout(2000)
    data = page.evaluate(r"""()=>{
        const m=[...document.querySelectorAll('.chakra-modal__content,[role=dialog],.chakra-drawer__content')].find(x=>x.offsetParent);
        if(!m) return {erro:'modal oculto'};
        // cada item de pessoa: procurar elementos com email
        const itens=[...m.querySelectorAll('li,tr,[role=option],[class*=item],label,div')]
          .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim())
          .filter(t=>/@/.test(t)&&t.length<120);
        const emails=(m.innerText||'').match(/[\w.\-]+@[\w.\-]+/g)||[];
        return {emails, itens:[...new Set(itens)].slice(0,80)};
    }""")
    if data.get("erro"):
        print(f"[{tag}] {data['erro']}"); return
    em=data["emails"]; cnt=Counter(em); dups={k:v for k,v in cnt.items() if v>1}
    print(f"[{tag}] emails={len(em)} unicos={len(cnt)} DUPLICADOS={dups if dups else 'NENHUM'}")
    return data


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/roles/1386/edit?tab=assigned-people", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    page.locator("#assigned-people-tab-add-button").click()
    page.wait_for_timeout(3000)
    tw.snap(page, PASTA, "07-drawer-aberto", full=True)
    d = ler_lista(page, "SEM FILTRO")
    if d:
        print("  itens (até 80):")
        for it in d["itens"]:
            print("   -", it[:100])
    ctx.close(); browser.close()
