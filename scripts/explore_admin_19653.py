"""Explorar admin/RH da org 19653 — mapear 'Continuidade e sucessão' e
'Mapa de competências' (cards 19851 e 20048)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "explore_19653"
c = tw.cfg("MIGR")  # evertongambeta admin


def dump_links(page, titulo):
    print(f"\n===== {titulo} =====\nURL: {page.url}")
    hrefs = page.evaluate(
        "()=>Array.from(document.querySelectorAll('a[href]'))"
        ".map(a=>({t:(a.innerText||a.getAttribute('aria-label')||'').replace(/\\s+/g,' ').trim(),h:a.getAttribute('href')}))"
        ".filter(x=>x.t.length>0&&x.t.length<45)"
    )
    seen = set()
    for x in hrefs:
        k = x["t"] + x["h"]
        if k not in seen:
            seen.add(k)
            print(f"  {x['t']!r} -> {x['h']}")


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)  # admin switch
    print("Pós-login:", page.url)
    tw.snap(page, PASTA, "01-admin-home", full=True)
    dump_links(page, "ADMIN HOME")

    # procurar termos no DOM da home admin
    termos = page.evaluate(
        "()=>Array.from(document.querySelectorAll('a,button,[role=menuitem],span'))"
        ".map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim())"
        ".filter(t=>/continu|sucess|compet|iniciativa|fun(ç|c)(ã|a)o|avalia|9.?box|talent/i.test(t)&&t.length<60)"
    )
    print("\n--- TERMOS RELEVANTES (home) ---")
    for t in sorted(set(termos)):
        print("  •", t)

    ctx.close()
    browser.close()
