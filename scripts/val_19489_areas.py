import sys, re
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "funcao_dup_19489"
c = tw.cfg("MIGR")


def emails_no_drawer(page):
    got = set()
    for _ in range(45):
        cur = page.evaluate(r"""()=>{
            const out=[];
            document.querySelectorAll('input[type=checkbox]').forEach(cb=>{
                const r=cb.getBoundingClientRect(); if(r.left<840) return;
                let el=cb; for(let k=0;k<6;k++){el=el.parentElement; if(!el)break;
                    if(/[\w.\-]+@[\w.\-]+/.test(el.innerText||''))break;}
                if(el){const m=(el.innerText||'').match(/[\w.\-]+@[\w.\-]+/); if(m) out.push(m[0]);}
            });
            return out;
        }""")
        before = len(got); got.update(cur)
        page.mouse.move(1160, 500); page.mouse.wheel(0, 1100); page.wait_for_timeout(450)
    return got


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/roles/1386/edit?tab=assigned-people", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    page.locator("#assigned-people-tab-add-button").click()
    page.wait_for_timeout(2500)

    # abrir 'Filtrar por área' e listar opções
    page.get_by_text("Filtrar por área", exact=False).first.click()
    page.wait_for_timeout(1200)
    tw.snap(page, PASTA, "10-areas-dropdown")
    areas = page.evaluate(
        "()=>Array.from(document.querySelectorAll('[role=option],option,li'))"
        ".map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<40&&!/por página|^\\d+$/.test(t))"
    )
    areas = sorted(set(areas))
    print("OPÇÕES DE ÁREA:", areas)
    page.keyboard.press("Escape"); page.wait_for_timeout(500)

    # para cada área, selecionar e coletar emails
    por_area = {}
    for a in areas[:12]:
        try:
            page.get_by_text("Filtrar por área", exact=False).first.click(); page.wait_for_timeout(800)
            page.get_by_role("option", name=a).first.click(timeout=2500)
            page.wait_for_timeout(1800)
            por_area[a] = emails_no_drawer(page)
            print(f"  área {a!r}: {len(por_area[a])} pessoas")
            # limpar seleção: reabrir e escolher vazio/todos se houver
        except Exception as e:
            print(f"  área {a!r}: falhou ({type(e).__name__})")

    # emails que aparecem em 2+ áreas = pessoas multi-área
    cont = defaultdict(list)
    for a, ems in por_area.items():
        for e in ems:
            cont[e].append(a)
    multi = {e: a for e, a in cont.items() if len(a) >= 2}
    print("\nPESSOAS EM 2+ ÁREAS (gatilho do bug):", len(multi))
    for e, a in list(multi.items())[:15]:
        print(f"   {e} -> {a}")
    ctx.close(); browser.close()
