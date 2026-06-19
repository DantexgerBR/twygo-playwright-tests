"""33085519 lider->liderado: Julia eh liderada da Adriana? (Equipe da Adriana)."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "desempenho_seguir_33085519"
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
    # Equipe da Adriana (href correto, sem /o/36675)
    page.goto(f"{c['base_url']}/team_leaders/4239211/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    print("URL:", page.url)
    body = page.evaluate("()=>document.body.innerText.slice(0,80)")
    if "doesn't exist" in body:
        # tentar via clique no menu Equipe
        page.goto(f"{c['base_url']}/dashboard_students", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        try:
            page.get_by_text("Equipe", exact=True).first.click(timeout=4000); page.wait_for_timeout(3000)
            print("URL via menu:", page.url)
        except Exception as ex:
            print("erro menu equipe:", str(ex)[:80])
    tw.snap(page, PASTA, "06-equipe-adriana", full=True)
    membros = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row],[class*=card]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/@|Julia|Vanessa|Gabriel|Carla|Danilo/i.test(t)).slice(0,20)""")
    print("MEMBROS EQUIPE:", membros)
    ctx.close(); browser.close()
print("OK")
