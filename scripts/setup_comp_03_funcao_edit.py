"""Setup: abrir edicao da funcao 'rh' e ver como atribuir usuarios (Julia)."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/roles?profile=admin", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    # clicar edit na linha "rh"
    row = page.locator("tr,[role=row]").filter(has_text=re.compile(r"\brh\b", re.I)).first
    try:
        row.get_by_text("edit", exact=True).first.click(timeout=5000)
    except Exception:
        # fallback: clicar no nome
        page.get_by_text("rh", exact=True).first.click(timeout=4000)
    page.wait_for_timeout(3500)
    print("URL edicao funcao:", page.url)
    tw.snap(page, PASTA, "31-funcao-rh-edit", full=True)
    info = page.evaluate(r"""()=>{
        const tabs=[...new Set(Array.from(document.querySelectorAll('[role=tab],button,a')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<30&&/Usu|Pessoa|Compet|Vincular|Adicionar|Membro|colabora/i.test(t)))];
        const phs=[...new Set(Array.from(document.querySelectorAll('input,[role=combobox]')).map(e=>e.placeholder||e.getAttribute('aria-label')||'').filter(Boolean))];
        const tids=Array.from(document.querySelectorAll('[data-test-id]')).map(e=>e.getAttribute('data-test-id')).filter(t=>/user|member|person|tab|role/i.test(t));
        return {tabs, phs:phs.slice(0,12), tids:[...new Set(tids)].slice(0,20)};
    }""")
    print("TABS/BTNS:", info["tabs"])
    print("INPUTS:", info["phs"])
    print("TIDS:", info["tids"])
    ctx.close(); browser.close()
print("OK")
