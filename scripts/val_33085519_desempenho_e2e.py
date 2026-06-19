"""33085519: provar que da pra SEGUIR a autoavaliacao de desempenho no 36675
(botoes presentes, responder, salvar rascunho, finalizar)."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "desempenho_seguir_33085519"
c = tw.cfg("")
cj = dict(c); cj["email"] = "julia@sophia.tech.com.br"; cj["senha"] = "123456"


def aceitar(page):
    try:
        b = page.get_by_role("button", name=re.compile(r"^Aceitar$", re.I)).first
        if b.count() and b.is_visible(): b.click(); page.wait_for_timeout(1000)
    except Exception: pass


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, cj, admin=False)
    page.wait_for_timeout(2500); aceitar(page)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/development", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); aceitar(page); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "01-listagem-avaliacoes")
    # confirmar listagem nao vazia
    linhas = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&!/Não há dados|Ciclo\s+Liderado/.test(t))""")
    print("LISTAGEM:", linhas)

    # abrir Responder
    page.get_by_role("button", name=re.compile("Responder", re.I)).first.click(timeout=6000)
    page.wait_for_timeout(3500); aceitar(page)
    print("URL player:", page.url)
    # botoes presentes?
    btns = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('button')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/Salvar|Finalizar|rascunho/i.test(t)))]""")
    print("BOTOES PLAYER:", btns)
    tw.snap(page, PASTA, "02-player-com-botoes")

    # responder: selecionar Opcao 1 (radio)
    try:
        page.get_by_text("Opção 1", exact=False).first.click(timeout=4000); page.wait_for_timeout(800)
        print("opcao 1 selecionada")
    except Exception as ex:
        print("erro opcao:", str(ex)[:80])

    # Salvar rascunho
    try:
        page.get_by_role("button", name=re.compile("Salvar rascunho", re.I)).first.click(timeout=4000)
        page.wait_for_timeout(2500)
        print("salvou rascunho; toast:", page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,4)"""))
    except Exception as ex:
        print("erro salvar rascunho:", str(ex)[:80])
    tw.snap(page, PASTA, "03-pos-salvar-rascunho")

    # Finalizar avaliacao
    try:
        page.get_by_role("button", name=re.compile("Finalizar avalia", re.I)).first.click(timeout=4000)
        page.wait_for_timeout(2000)
        # pode ter modal de confirmacao
        for nome in ["Finalizar", "Confirmar", "Sim"]:
            b = page.get_by_role("button", name=re.compile(f"^{nome}", re.I))
            if b.count() and b.first.is_visible() and b.first.is_enabled():
                b.first.click(); break
        page.wait_for_timeout(2500)
        print("finalizou; toast:", page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,4)"""))
        print("URL pos-finalizar:", page.url)
    except Exception as ex:
        print("erro finalizar:", str(ex)[:80])
    tw.snap(page, PASTA, "04-pos-finalizar", full=True)

    ctx.close(); browser.close()
print("OK")
