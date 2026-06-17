import sys
from pathlib import Path
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "funcao_dup_19489"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/roles/1386/edit?tab=assigned-people", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    page.locator("#assigned-people-tab-add-button").click()
    page.wait_for_timeout(2500)

    # container scrollável do drawer (painel à direita, x>840)
    todos = {}  # email -> set(areas)
    ordem = []
    for i in range(40):
        cards = page.evaluate(r"""()=>{
            const out=[];
            document.querySelectorAll('*').forEach(e=>{
                const r=e.getBoundingClientRect();
                if(r.left<840) return;
                const t=(e.innerText||'');
                const m=t.match(/^([^\n]+)\n([\w.\-]+@[\w.\-]+)\s*(.*)$/);
            });
            // melhor: pegar cada bloco que contém exatamente 1 email
            const blocks=[...document.querySelectorAll('div,li,label')].filter(e=>{
                const r=e.getBoundingClientRect(); if(r.left<840||r.width<200) return false;
                const em=(e.innerText||'').match(/[\w.\-]+@[\w.\-]+/g)||[];
                return em.length===1;
            });
            blocks.forEach(b=>{
                const t=(b.innerText||'').replace(/\s+/g,' ').trim();
                const em=(t.match(/[\w.\-]+@[\w.\-]+/)||[''])[0];
                if(em) out.push({t, em});
            });
            return out;
        }""")
        for x in cards:
            if x["em"] not in todos:
                todos[x["em"]] = x["t"]
                ordem.append(x["em"])
        # scroll dentro do drawer
        page.mouse.move(1160, 500)
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(600)

    print("TOTAL pessoas únicas coletadas:", len(todos))
    # detectar duplicata: mesmo nome (antes do @) com emails diferentes OU mesmo email repetido
    # como dedupliquei por email, conto nomes repetidos com áreas diferentes
    from collections import defaultdict
    por_nome = defaultdict(list)
    for em, t in todos.items():
        nome = t.split(em)[0].strip()
        por_nome[nome].append((em, t))
    print("\nNOMES que aparecem com +1 entrada (possível duplicação por área):")
    achou = False
    for nome, lst in por_nome.items():
        if len(lst) > 1:
            achou = True
            print(f"  '{nome}': {len(lst)}x")
            for em, t in lst:
                print("     ->", t[:90])
    if not achou:
        print("  NENHUM nome duplicado (cada pessoa 1x)")
    tw.snap(page, PASTA, "08-fim-scan")
    ctx.close(); browser.close()
