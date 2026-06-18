"""RECON v3 18468 — clicar no BOTAO (role) Importacao Inteligente, esperar, e
detectar o chat overlay procurando textos da evidencia ('Agente de importacao',
'Importe seus dados'). Dump amplo pra achar onde a resposta da IA renderiza.
"""
import re
import _twygo as tw

c = tw.cfg("MIGR")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "18468_recon"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{BASE}/o/{ORG}/question_lists", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)

    n_files_antes = page.locator("input[type=file]").count()
    btn = page.get_by_role("button", name=re.compile(r"Importa.{0,4}o Inteligente", re.I)).first
    print(f"[btn] visivel={btn.is_visible()} enabled={btn.is_enabled()}")
    btn.scroll_into_view_if_needed()
    btn.click(timeout=6000, force=True)
    # esperar o chat carregar (pode demorar)
    aberto = False
    for s in range(12):
        page.wait_for_timeout(1000)
        body = page.evaluate("()=>document.body.innerText||''")
        if re.search(r"Agente de importa|Importe seus dados|Escreva uma mensagem", body, re.I):
            aberto = True
            print(f"[chat aberto] apos ~{s+1}s")
            break
    print(f"[aberto?] {aberto}")
    tw.snap(page, PASTA, "20-pos-click-botao")

    files = page.evaluate(
        "()=>Array.from(document.querySelectorAll('input[type=file]')).map(i=>({accept:i.accept,name:i.name,id:i.id,vis:i.offsetParent!==null}))")
    print(f"[file inputs] (antes={n_files_antes}) {files}")

    texts = page.evaluate(
        "()=>Array.from(document.querySelectorAll('textarea,input[type=text]')).filter(e=>e.offsetParent!==null).map(e=>({tag:e.tagName,ph:e.placeholder}))")
    print(f"[campos texto visiveis] {texts}")

    # achar elemento com 'Escreva uma mensagem' e seu ancestral grande (o chat)
    info = page.evaluate(
        r"""()=>{
            const all=Array.from(document.querySelectorAll('*'));
            const hit=all.find(e=>/Escreva uma mensagem/i.test(e.getAttribute&&e.getAttribute('placeholder')||'')||/Agente de importa/i.test(e.innerText||''&&e.children.length<3));
            const marca=all.find(e=>/Agente de importa/i.test((e.innerText||''))&&e.children.length<4);
            return {achouCampo:!!hit, marcaAgente: marca?(marca.innerText||'').slice(0,60):null};
        }""")
    print(f"[deteccao] {info}")

    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
