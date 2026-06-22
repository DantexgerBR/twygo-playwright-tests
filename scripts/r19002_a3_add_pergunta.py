"""19002 — ETAPA A3: adicionar 1 pergunta (Formato Texto) ao questionario 73254."""
import re
import _twygo as tw

c = tw.cfg("")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"
QID = "73254"
PERGUNTA = "Descreva o que voce aprendeu neste conteudo."

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{BASE}/o/{ORG}/question_lists/{QID}/questions/new", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)

    # Formato = Texto (resposta livre, sem alternativas)
    page.select_option('select[name=kind]', value="text")
    page.wait_for_timeout(1200)
    # Pergunta (titulo)
    page.fill('input[name=title]', PERGUNTA)
    tw.snap(page, PASTA, "A5-pergunta-texto-preenchida")

    # Salvar
    page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=5000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    print(f"[apos salvar pergunta] url={page.url}")
    tw.snap(page, PASTA, "A6-apos-salvar-pergunta")

    # voltar pra lista de perguntas p/ confirmar
    page.goto(f"{BASE}/o/{ORG}/question_lists/{QID}/edit", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2500); tw.dispensar_nps(page)
    page.get_by_role("tab", name=re.compile("Pergunta", re.I)).first.click(timeout=5000)
    page.wait_for_timeout(1500)
    linhas = page.evaluate(
        "()=>Array.from(document.querySelectorAll('tbody tr')).map(r=>(r.innerText||'').replace(/\\s+/g,' ').trim()).filter(Boolean)")
    print(f"[perguntas no questionario] {linhas}")
    tw.snap(page, PASTA, "A7-perguntas-lista")
    page.wait_for_timeout(800)
    ctx.close(); browser.close()
