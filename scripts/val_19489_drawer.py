import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "funcao_dup_19489"
c = tw.cfg("MIGR")


def painel_txt(page):
    return page.evaluate(
        "()=>{let b='';document.querySelectorAll('.chakra-modal__content,[role=dialog],.chakra-slide,aside').forEach(m=>{"
        "if(m.offsetParent){const t=(m.innerText||'').trim();if(t.length>b.length)b=t;}});return b;}"
    )


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/organization_chart_roles", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4500)
    tw.dispensar_nps(page)

    # editar 1a função
    page.locator('[data-icon="edit"]').first.click(force=True)
    page.wait_for_timeout(3500)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "02-funcao-editar")
    print("após editar url:", page.url)
    # achar aba/seção 'pessoas atribuídas' / 'executores'
    abas = page.evaluate(
        "()=>Array.from(document.querySelectorAll('[role=tab],button,a,h2,h3'))"
        ".map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>/pessoa|executor|atribu|vincul|adicionar/i.test(t)&&t.length<40)"
    )
    print("seções/abas relevantes:", sorted(set(abas)))

    # clicar em 'Pessoas atribuídas' ou 'Executores'
    for nome in ["Pessoas atribuídas", "Executores", "Pessoas"]:
        try:
            page.get_by_text(nome, exact=False).first.click(timeout=2500)
            page.wait_for_timeout(1500)
            print("cliquei seção:", nome)
            break
        except Exception:
            continue
    tw.snap(page, PASTA, "03-pessoas-atribuidas")

    # clicar Adicionar (abre drawer de pessoas)
    page.get_by_role("button", name=re.compile("Adicionar", re.I)).first.click()
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "04-drawer-adicionar", full=True)

    # listar todas as pessoas do drawer e detectar duplicatas
    pessoas = page.evaluate(r"""()=>{
        const root=[...document.querySelectorAll('.chakra-modal__content,[role=dialog],.chakra-slide,aside')].find(m=>m.offsetParent);
        if(!root) return {erro:'sem drawer'};
        const emails=(root.innerText||'').match(/[\w.\-]+@[\w.\-]+/g)||[];
        return {emails};
    }""")
    print("\n=== PESSOAS NO DRAWER ===")
    if pessoas.get("erro"):
        print("ERRO:", pessoas["erro"])
    else:
        em = pessoas["emails"]
        from collections import Counter
        cnt = Counter(em)
        print("total emails:", len(em), "| únicos:", len(cnt))
        dups = {k: v for k, v in cnt.items() if v > 1}
        print("DUPLICADOS:", dups if dups else "NENHUM")
    ctx.close(); browser.close()
