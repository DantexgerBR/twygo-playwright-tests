"""RECON 18468 — achar 'Nova conversa' no menu hamburguer (☰) do chat de importacao
e testar enviar SO o anexo (sem prompt) pra elicitar o preview em TABELA da evidencia.
"""
import re
import _twygo as tw

c = tw.cfg("MIGR")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "18468_recon"
DOC = tw.ROOT / "evidencias" / "18468" / "quiz_grande.docx"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{BASE}/o/{ORG}/question_lists", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    page.get_by_role("button", name=re.compile(r"Importa.{0,4}o Inteligente", re.I)).first.click(force=True)
    page.wait_for_timeout(3000)

    # abrir o menu hamburguer (icone 'menu' no topo esquerdo do chat)
    try:
        page.get_by_text("menu", exact=True).first.click(timeout=4000)
        page.wait_for_timeout(1500)
        tw.snap(page, PASTA, "40-menu-hamburguer")
        itens = page.evaluate(
            "()=>Array.from(document.querySelectorAll('button,a,[role=menuitem],li')).filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<40).slice(0,40)")
        print(f"[itens menu] {itens}")
        # tentar clicar em 'Nova'/'Novo'/'Limpar'
        for txt in ["Nova conversa", "Novo chat", "Nova", "Limpar", "Nova importa"]:
            b = page.get_by_text(re.compile(txt, re.I))
            if b.count() and b.first.is_visible():
                print(f"[nova conversa] achei '{txt}'"); b.first.click(timeout=3000); break
        page.wait_for_timeout(2000)
        tw.snap(page, PASTA, "41-pos-nova-conversa")
    except Exception as e:
        print(f"[menu] erro: {e}")

    # testar: anexar SO o arquivo, sem texto, e enviar
    with page.expect_file_chooser(timeout=8000) as fc:
        page.get_by_text("attach_file").first.click(timeout=5000)
    fc.value.set_files(str(DOC))
    page.wait_for_timeout(3000)
    send = page.locator("#thread-composer-send-btn")
    habilitou = False
    for _ in range(40):
        if send.count() and send.is_enabled():
            habilitou = True; break
        page.wait_for_timeout(500)
    print(f"[send sem texto] habilitou={habilitou}")
    tw.snap(page, PASTA, "42-anexo-sem-texto")

    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
