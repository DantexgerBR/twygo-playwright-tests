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

    # cada linha = 1 checkbox no painel direito. row text = ancestral c/ email.
    rows = set()
    for i in range(50):
        got = page.evaluate(r"""()=>{
            const out=[];
            document.querySelectorAll('input[type=checkbox]').forEach(cb=>{
                const r=cb.getBoundingClientRect(); if(r.left<840) return;
                let el=cb;
                for(let k=0;k<6;k++){ el=el.parentElement; if(!el) break;
                    if(/[\w.\-]+@[\w.\-]+/.test(el.innerText||'')) break; }
                if(!el) return;
                const t=(el.innerText||'').replace(/\s+/g,' ').trim();
                if(/@/.test(t)) out.push(t);
            });
            return out;
        }""")
        for t in got:
            rows.add(t)
        page.mouse.move(1160, 500)
        page.mouse.wheel(0, 1100)
        page.wait_for_timeout(550)

    por_email = defaultdict(set)
    for t in rows:
        m = re.search(r"[\w.\-]+@[\w.\-]+", t)
        if m:
            por_email[m.group(0)].add(t)
    print("Linhas(checkbox) distintas:", len(rows), "| emails:", len(por_email))
    dup = {e: s for e, s in por_email.items() if len(s) > 1}
    print(">>> EMAILS em 2+ linhas de checkbox (duplicacao real):", len(dup))
    for e, s in list(dup.items())[:30]:
        print(f"  {e}:")
        for l in s:
            print("    |", l[:95])
    if not dup:
        print("  NENHUM — cada pessoa tem 1 checkbox.")
    ctx.close(); browser.close()
