"""19363: tela do LIDER (adriana@twygo.com) - confirmar filtro global."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "filtros_dashboards_19363"
c = tw.cfg("")
ca = dict(c); ca["email"] = "adriana@twygo.com"; ca["senha"] = "123456"


def aceitar(page):
    try:
        b = page.get_by_role("button", name=re.compile(r"^Aceitar$", re.I)).first
        if b.count() and b.is_visible():
            b.click(timeout=3000); page.wait_for_timeout(1200); print("   [consentimento aceito]")
    except Exception:
        pass


def checar(page, tag, slug):
    aceitar(page); tw.dispensar_nps(page); page.wait_for_timeout(800)
    btn = page.get_by_role("button", name=re.compile("Filtro", re.I))
    tem = btn.count() > 0 and btn.first.is_visible()
    body = page.evaluate("()=>document.body.innerText.slice(0,80)")
    perm = "sem permiss" not in body.lower() and "não tem permiss" not in body.lower()
    print(f"  [{tag}] url={page.url} | acesso={perm} | Filtro visivel? {tem}")
    tw.snap(page, PASTA, f"16-adriana-{slug}")
    if tem:
        btn.first.click(timeout=4000); page.wait_for_timeout(1500)
        tw.snap(page, PASTA, f"17-adriana-{slug}-filtro-aberto", full=True)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, ca, admin=False)
    page.wait_for_timeout(3000); aceitar(page); tw.dispensar_nps(page)
    print("URL Adriana home:", page.url)
    tw.snap(page, PASTA, "16-adriana-home")
    # menu dela
    links = page.evaluate(r"""()=>{const o=[];const s=new Set();document.querySelectorAll('a[href]').forEach(a=>{const t=(a.innerText||'').replace(/\s+/g,' ').trim();const h=a.getAttribute('href');if(t&&!s.has(h)){s.add(h);o.push(t+' -> '+h);}});return o;}""")
    print("MENU ADRIANA:")
    for l in links: print("  ", l)

    for path, slug in [("development", "development"),
                        ("organization_chart_competencies", "competencias"),
                        ("cycles", "cycles")]:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/{path}", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)
        checar(page, path, slug)

    ctx.close(); browser.close()
print("OK")
