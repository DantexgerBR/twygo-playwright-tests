"""RECON 18468 — abrir Questionarios -> Importacao inteligente e mapear:
- texto do botao de importacao
- file input (accept) -> saber se aceita pdf/docx/txt
- estrutura do chat (onde a resposta da IA renderiza)
Org MIGR (testedemigracao, 19653) com flag analise_de_questionario_por_ia.
So navega + screenshots + dumps. Read-only.
"""
import _twygo as tw

c = tw.cfg("MIGR")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "18468_recon"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    print(f"[login] {page.url}")

    page.goto(f"{BASE}/o/{ORG}/question_lists", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print(f"[question_lists] {page.url}")
    tw.snap(page, PASTA, "01-lista")

    botoes = page.evaluate(
        "()=>Array.from(document.querySelectorAll('button,a')).map(b=>(b.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<45)")
    print(f"[botoes] {botoes}")

    # clicar no botao de importacao inteligente
    import re
    clicado = False
    for txt in ["Importa", "inteligente"]:
        b = page.get_by_role("button", name=re.compile(txt, re.I))
        if not b.count():
            b = page.get_by_text(re.compile(txt, re.I))
        if b.count() and b.first.is_visible():
            b.first.click(timeout=5000); clicado = True
            print(f"[click] '{txt}'"); break
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print(f"[apos click] {page.url}")
    tw.snap(page, PASTA, "02-pos-import")

    # file inputs e seus accept
    inputs = page.evaluate(
        "()=>Array.from(document.querySelectorAll('input[type=file]')).map(i=>({accept:i.accept,name:i.name,id:i.id,visivel:i.offsetParent!==null}))")
    print(f"[file inputs] {inputs}")

    # estrutura do chat / area de mensagens
    chat = page.evaluate(
        "()=>{const c=document.querySelector('[class*=thread],[class*=chat],[class*=message],[class*=assistant]');return c?{cls:(c.className||'').toString().slice(0,120),tag:c.tagName}:null;}")
    print(f"[chat container] {chat}")

    print(f"\n[FIM recon] {PASTA}")
    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
