import sys, re
from pathlib import Path
from collections import defaultdict
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

    linhas = set()
    for i in range(45):
        cards = page.evaluate(r"""()=>{
            const blocks=[...document.querySelectorAll('div,li,label')].filter(e=>{
                const r=e.getBoundingClientRect(); if(r.left<840||r.width<200||r.width>700||r.height>90||r.height<30) return false;
                const em=(e.innerText||'').match(/[\w.\-]+@[\w.\-]+/g)||[];
                return em.length===1 && (e.innerText||'').length<160;
            });
            return blocks.map(b=>(b.innerText||'').replace(/\s+/g,' ').trim());
        }""")
        for t in cards:
            linhas.add(t)
        page.mouse.move(1160, 500)
        page.mouse.wheel(0, 1100)
        page.wait_for_timeout(550)

    por_email = defaultdict(set)
    for t in linhas:
        m = re.search(r"[\w.\-]+@[\w.\-]+", t)
        if m:
            por_email[m.group(0)].add(t)

    print("Linhas distintas:", len(linhas), "| emails distintos:", len(por_email))
    dup = {em: ls for em, ls in por_email.items() if len(ls) > 1}
    print("\n>>> EMAILS com 2+ linhas distintas (MESMA pessoa duplicada por área):", len(dup))
    for em, ls in list(dup.items())[:30]:
        print(f"  {em}:")
        for l in ls:
            print("     |", l[:95])
    if not dup:
        print("  NENHUM email duplicado — cada pessoa aparece 1x.")
    tw.snap(page, PASTA, "09-raw-fim")
    ctx.close(); browser.close()
