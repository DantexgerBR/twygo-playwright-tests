"""19002 — ETAPA A: criar questionario (Prova, Analise por IA OFF) + abrir aba Perguntas.

So cria o questionario e nos mostra a aba 'Perguntas' (screenshot) p/ eu entender
como adicionar questao. Persiste o id do questionario em _ids.json.
Org 36675 (stage principal) — onde o dev subiu o branch do PR 10181.
"""
import json
import re
import _twygo as tw

c = tw.cfg("")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"
PASTA.mkdir(parents=True, exist_ok=True)
NOME_Q = "QA 19002 Analise IA"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    print(f"[login] {page.url}")

    page.goto(f"{BASE}/o/{ORG}/question_lists/new", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)

    # Nome — primeiro textbox VISIVEL (o form tem inputs ocultos de outros widgets)
    cand = page.get_by_role("textbox").filter(visible=True)
    n = cand.count()
    print(f"[nome] textboxes visiveis: {n}")
    if n == 0:  # fallback: chakra-input visivel
        cand = page.locator("input.chakra-input, textarea.chakra-input").filter(visible=True)
        print(f"[nome] fallback chakra-input visiveis: {cand.count()}")
    cand.first.click()
    cand.first.fill(NOME_Q, timeout=8000)
    print(f"[nome] preenchido: {NOME_Q}")
    # Tipo: Prova (radio)
    try:
        page.get_by_text(re.compile(r"^Prova$")).first.click(timeout=4000)
    except Exception:
        page.locator('input[type=radio]').first.check()
    page.wait_for_timeout(500)

    # garantir switch "Analise por IA" OFF (deve ja estar off por default)
    sw = page.locator('.chakra-switch, [role=switch]').first
    estado = page.evaluate("()=>{const s=document.querySelector('.chakra-switch input,[role=switch] input,[role=switch]');return s?(s.getAttribute('aria-checked')||s.checked):null;}")
    print(f"[switch Analise por IA] estado inicial = {estado} (esperado off/false)")
    tw.snap(page, PASTA, "A1-form-preenchido")

    # Salvar (procura botao Salvar/Criar/Avancar)
    salvou = False
    for txt in ["Salvar", "Criar", "Avançar", "Continuar", "Próximo", "Adicionar"]:
        b = page.get_by_role("button", name=re.compile(txt, re.I))
        if b.count() and b.first.is_visible():
            b.first.click(timeout=4000); salvou = True
            print(f"[salvar] clicou '{txt}'"); break
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    print(f"[apos salvar] url={page.url}")
    tw.snap(page, PASTA, "A2-apos-salvar")

    # capturar id do questionario da URL (se virou /question_lists/{id}/...)
    m = re.search(r"/question_lists/(\d+)", page.url)
    qid = m.group(1) if m else None
    print(f"[questionario id] {qid}")

    # tentar ir pra aba Perguntas
    try:
        page.get_by_role("tab", name=re.compile("Pergunta", re.I)).first.click(timeout=4000)
    except Exception:
        try:
            page.get_by_text(re.compile(r"^Perguntas$")).first.click(timeout=4000)
        except Exception:
            pass
    page.wait_for_timeout(2500); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "A3-aba-perguntas")
    botoes = page.evaluate(
        "()=>Array.from(document.querySelectorAll('button,a')).map(b=>(b.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<35).slice(0,30)")
    print(f"[aba perguntas] botoes: {botoes}")

    (PASTA / "_ids.json").write_text(json.dumps({"questionario_id": qid, "nome": NOME_Q, "url": page.url}, indent=2), encoding="utf-8")
    print(f"\n[FIM etapa A] ids salvos. veja {PASTA}")
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
