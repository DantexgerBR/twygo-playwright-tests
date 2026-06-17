import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "funcao_dup_19489"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/roles/1386/edit", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    page.get_by_text("Pessoas atribuídas", exact=False).first.click()
    page.wait_for_timeout(2000)

    btns = page.evaluate("()=>Array.from(document.querySelectorAll('button')).filter(b=>/Adicionar/i.test(b.innerText||'')&&b.offsetParent).map(b=>({t:b.innerText.trim(),id:b.id,cls:b.className.slice(0,30)}))")
    print("botões Adicionar visíveis:", btns)

    page.locator("button", has_text=re.compile("Adicionar", re.I)).first.click(force=True)
    page.wait_for_timeout(3500)
    diag = page.evaluate(r"""()=>{
        const all=[...document.querySelectorAll('.chakra-modal__content,[role=dialog],.chakra-drawer__content,[role=alertdialog],aside,.chakra-slide')];
        return all.map(m=>({vis: m.offsetParent!==null, len:(m.innerText||'').length, head:(m.innerText||'').slice(0,80).replace(/\s+/g,' ')}));
    }""")
    print("\nmodais/drawers no DOM:")
    for d in diag:
        print("  ", d)
    tw.snap(page, PASTA, "06-apos-adicionar")
    # também: a tela toda mudou de url?
    print("url:", page.url)
    ctx.close(); browser.close()
