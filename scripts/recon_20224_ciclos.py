"""Recon 20224: Adriana tem liderado? (Equipe) + ciclo pode ser criado/programado?"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")
ca = dict(c); ca["email"]="adriana@twygo.com"; ca["senha"]="123456"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, ca, admin=False)
    page.wait_for_timeout(2500)
    try:
        b = page.get_by_role("button", name=re.compile(r"^Aceitar$", re.I)).first
        if b.count() and b.is_visible(): b.click(); page.wait_for_timeout(1000)
    except Exception: pass

    # Equipe da Adriana
    page.goto(f"{c['base_url']}/o/{c['org_id']}/team_leaders/4239211/users", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "02-adriana-equipe", full=True)
    body = page.evaluate(r"""()=>document.body.innerText.replace(/\n{2,}/g,'\n')""")
    i = body.find("Equipe")
    print("--- EQUIPE ADRIANA ---")
    print(body[i:i+700] if i>=0 else body[:700])
    liderados = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/@/.test(t)).slice(0,15)""")
    print("LIDERADOS (linhas c/ email):", liderados)

    ctx.close(); browser.close()
print("OK")
