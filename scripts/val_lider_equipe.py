"""33085519 lider: a tarefa de avaliar o liderado aparece na visao Equipe da Adriana?"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "desempenho_seguir_33085519"
c = tw.cfg("")
ca = dict(c); ca["email"]="adriana@twygo.com"; ca["senha"]="123456"


def aceitar(page):
    try:
        b = page.get_by_role("button", name=re.compile(r"^Aceitar$", re.I)).first
        if b.count() and b.is_visible(): b.click(); page.wait_for_timeout(1000)
    except Exception: pass


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, ca, admin=False)
    page.wait_for_timeout(2500); aceitar(page)
    # menu Equipe
    page.goto(f"{c['base_url']}/team_leaders/4239211/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(3500); aceitar(page); tw.dispensar_nps(page)
    print("URL Equipe:", page.url)
    tw.snap(page, PASTA, "13-adriana-equipe-detalhe", full=True)
    # links/botoes relacionados a avaliar liderado
    info = page.evaluate(r"""()=>{
        const btns=[...new Set(Array.from(document.querySelectorAll('button,a')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<30&&/Avaliar|Responder|avalia|desempenho|Ver/i.test(t)))];
        const links=Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href')).filter(h=>/assess|avalia|performance|development/i.test(h||''));
        const body=(document.body.innerText||'').replace(/\n{2,}/g,'\n').slice(0,500);
        return {btns, links:[...new Set(links)].slice(0,10), body};
    }""")
    print("BTNS:", info["btns"])
    print("LINKS:", info["links"])
    print("BODY:", info["body"][:400])

    # tentar abrir o liderado Dante (clicar na linha) e ver opcoes
    try:
        page.locator("tr,[role=row]").filter(has_text=re.compile("dante.tavares", re.I)).first.click(timeout=4000)
        page.wait_for_timeout(3000); aceitar(page)
        print("URL apos clicar liderado:", page.url)
        tw.snap(page, PASTA, "14-liderado-detalhe", full=True)
        b2 = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('button,a')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<30&&/Avaliar|Responder|desempenho|avalia/i.test(t)))]""")
        print("BTNS liderado:", b2)
    except Exception as ex:
        print("erro abrir liderado:", str(ex)[:80])
    ctx.close(); browser.close()
print("OK")
