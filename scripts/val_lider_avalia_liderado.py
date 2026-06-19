"""33085519 lider->liderado: Adriana recebe e avalia o desempenho do liderado (Dante)."""
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
    page.goto(f"{c['base_url']}/o/{c['org_id']}/development", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); aceitar(page); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "08-adriana-avaliacoes-a-preencher", full=True)
    linhas = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&!/Não há dados|^Ciclo\s+Liderado/.test(t))""")
    print("LISTAGEM ADRIANA:", linhas)

    # abrir a avaliacao do liderado (linha com Dante / lider-liderado)
    abriu = False
    try:
        page.locator("tr,[role=row]").filter(has_text=re.compile("lider-liderado|33085519|Dante", re.I)).first.get_by_role("button", name=re.compile("Responder", re.I)).click(timeout=5000)
        abriu = True
    except Exception:
        try:
            page.get_by_role("button", name=re.compile("Responder", re.I)).first.click(timeout=5000); abriu = True
        except Exception as ex:
            print("sem Responder:", str(ex)[:80])
    page.wait_for_timeout(4000); aceitar(page)
    print("URL player:", page.url, "| abriu:", abriu)
    tw.snap(page, PASTA, "09-adriana-responder-liderado", full=False)
    # header: quem esta sendo avaliado
    hdr = page.evaluate(r"""()=>{
        const t=(document.body.innerText||'').replace(/\s+/g,' ');
        const i=t.search(/Responder avalia/i);
        return t.slice(i, i+160);
    }""")
    print("HEADER:", hdr)
    # botoes
    btns = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('button')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/Salvar|Finalizar|rascunho/i.test(t)))]""")
    print("BOTOES:", btns)

    # responder + salvar rascunho
    try:
        page.get_by_text("Opção 1", exact=False).first.click(timeout=4000); page.wait_for_timeout(700)
        page.get_by_role("button", name=re.compile("Salvar rascunho", re.I)).first.click(timeout=4000)
        page.wait_for_timeout(2500)
        print("salvar rascunho toast:", page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,4)"""))
    except Exception as ex:
        print("erro responder/salvar:", str(ex)[:100])
    tw.snap(page, PASTA, "10-adriana-pos-salvar", full=True)
    ctx.close(); browser.close()
print("OK")
