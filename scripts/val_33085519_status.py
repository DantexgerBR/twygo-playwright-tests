"""33085519: checar status da avaliacao apos finalizar (Julia)."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "desempenho_seguir_33085519"
c = tw.cfg("")
cj = dict(c); cj["email"] = "julia@sophia.tech.com.br"; cj["senha"] = "123456"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, cj, admin=False)
    page.wait_for_timeout(2500)
    try:
        b = page.get_by_role("button", name=re.compile(r"^Aceitar$", re.I)).first
        if b.count() and b.is_visible(): b.click(); page.wait_for_timeout(1000)
    except Exception: pass
    page.goto(f"{c['base_url']}/o/{c['org_id']}/development", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(4500); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "05-listagem-pos-finalizar", full=True)
    linhas = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&/QA 20224|Conclu|iniciar|andamento|Desempenho/i.test(t))""")
    print("LISTAGEM POS-FINALIZAR:", linhas)
    ctx.close(); browser.close()
print("OK")
