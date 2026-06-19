"""19363 D12: Julia (colaboradora) - aceitar consentimento, achar dashboard + Filtro."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "filtros_dashboards_19363"
c = tw.cfg("")
cj = dict(c); cj["email"] = "julia@sophia.tech.com.br"; cj["senha"] = "123456"


def aceitar_consentimento(page):
    try:
        b = page.get_by_role("button", name=re.compile(r"^Aceitar$", re.I)).first
        if b.count() and b.is_visible():
            b.click(timeout=3000); page.wait_for_timeout(1500); print("   [consentimento aceito]")
            return True
    except Exception:
        pass
    return False


def checar_filtro(page, tag, slug):
    aceitar_consentimento(page); tw.dispensar_nps(page)
    page.wait_for_timeout(800)
    btn = page.get_by_role("button", name=re.compile("Filtro", re.I))
    tem = btn.count() > 0 and btn.first.is_visible()
    print(f"  [{tag}] url={page.url} | Filtro visivel? {tem}")
    tw.snap(page, PASTA, f"13-julia-{slug}")
    if tem:
        try:
            btn.first.click(timeout=4000); page.wait_for_timeout(1500)
            tw.snap(page, PASTA, f"14-julia-{slug}-filtro-aberto", full=True)
            # tentar abrir Novo/Opcoes e ler colunas
            try:
                page.get_by_text("Novo", exact=True).first.click(timeout=3000); page.wait_for_timeout(1000)
                page.get_by_role("button", name=re.compile("Op[cç][õo]es de filtro", re.I)).first.click(timeout=3000)
                page.wait_for_timeout(1200)
                cols = page.evaluate(r"""()=>{const dlg=Array.from(document.querySelectorAll('[role=dialog],.chakra-modal__content,[class*=drawer],[class*=Drawer]')).filter(d=>d.offsetParent!==null);const s=dlg.length?dlg[dlg.length-1]:document.body;return [...new Set(Array.from(s.querySelectorAll('label,[role=option],[role=menuitem]')).map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<30))].slice(0,20);}""")
                print(f"      colunas filtro [{tag}]:", cols)
                tw.snap(page, PASTA, f"15-julia-{slug}-colunas")
            except Exception as ex:
                print("      (nao abriu Novo/Opcoes):", str(ex)[:80])
        except Exception as ex:
            print("    erro abrir filtro:", str(ex)[:80])


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, cj, admin=False)
    page.wait_for_timeout(3000)
    aceitar_consentimento(page); tw.dispensar_nps(page)
    print("URL Julia home:", page.url)
    tw.snap(page, PASTA, "12-julia-home")

    for path, slug in [("development", "development"),
                        ("organization_chart_competencies", "competencias"),
                        ("cycles", "cycles")]:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/{path}", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)
        checar_filtro(page, path, slug)

    ctx.close(); browser.close()
print("OK")
