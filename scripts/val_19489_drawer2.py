import sys, re
from pathlib import Path
from collections import Counter
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
    # + Adicionar -> drawer
    page.get_by_role("button", name=re.compile(r"Adicionar", re.I)).first.click()
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "05-drawer-pessoas", full=True)

    # capturar linhas do drawer (modal). Cada pessoa: nome + email + área
    dados = page.evaluate(r"""()=>{
        const mods=[...document.querySelectorAll('.chakra-modal__content,[role=dialog],.chakra-drawer__content,aside')].filter(m=>m.offsetParent);
        const root=mods.sort((a,b)=>b.innerText.length-a.innerText.length)[0];
        if(!root) return {erro:'sem modal'};
        const txt=root.innerText||'';
        const emails=(txt).match(/[\w.\-]+@[\w.\-]+/g)||[];
        // tentar capturar linhas de tabela com nome/area
        const rows=[...root.querySelectorAll('tr,[role=row],li')].map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t.includes('@'));
        return {emails, rows: rows.slice(0,60), titulo: (root.querySelector('h1,h2,header')||{}).innerText||''};
    }""")
    print("titulo drawer:", dados.get("titulo"))
    if dados.get("erro"):
        print("ERRO:", dados["erro"])
    else:
        em = dados["emails"]
        cnt = Counter(em)
        dups = {k: v for k, v in cnt.items() if v > 1}
        print("total emails:", len(em), "| unicos:", len(cnt))
        print("DUPLICADOS:", dups if dups else "NENHUM")
        print("\n--- LINHAS (até 60) ---")
        for r in dados["rows"]:
            print("  |", r[:90])
    ctx.close(); browser.close()
