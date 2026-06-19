"""20224: status da campanha 189 + acao de iniciar/programar."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/174/campaigns", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "19-campanhas-lista", full=True)
    rows = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&!/Não há dados/.test(t))""")
    print("LINHAS CAMPANHAS:", rows)
    # abrir kebab/acoes da campanha
    btns = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('button,a,[role=menuitem]')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<30))]""")
    print("BTNS:", btns)
    # status do ciclo
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles?profile=admin", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000)
    crow = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/20224|autoavaliacao/i.test(t))""")
    print("CICLO 174 linha:", crow)
    tw.snap(page, PASTA, "19b-ciclo-lista")
    ctx.close(); browser.close()
print("OK")
