"""Retrabalho 20181 (P0) — Certificado externo nao aparece na listagem apos toast.

Teste ao vivo: cria um conteudo externo (Registros) com nome unico, confirma o toast
de sucesso, volta a listagem e procura o item. Esperado: o item aparece.
Login: usuariodev@testes.com (o devtestes@teste.com do card esta INVALIDO no stage).
"""
import re
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "cert_externo_20181"
c = tw.cfg("GOATWY")
TOKEN = "QA20181-" + datetime.now().strftime("%d%H%M%S")  # nome unico do conteudo


def pick_pessoa(page):
    """Pessoas* : abre o drawer 'Vincular pessoas', marca a 1a pessoa e clica Vincular."""
    page.get_by_text("Adicionar pessoas", exact=False).first.click()
    page.wait_for_timeout(1500)
    # marca a 1a pessoa da lista (span clicavel do checkbox Chakra)
    page.locator(".chakra-checkbox__control").first.click()
    page.wait_for_timeout(600)
    page.get_by_role("button", name=re.compile(r"^Vincular$", re.I)).first.click()
    page.wait_for_timeout(1200)


def rs_pick(page, placeholder, texto, enter=True):
    """react-select localizado pelo placeholder: clica no __control (ancestral),
    digita `texto`, e (se enter) seleciona a opcao em foco com Enter."""
    ph = page.get_by_text(placeholder, exact=False).first
    ctl = ph.locator("xpath=ancestor::*[contains(@class,'__control')][1]")
    ctl.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    ctl.click(force=True)
    page.wait_for_timeout(700)
    if texto:
        page.keyboard.type(texto, delay=40)
        page.wait_for_timeout(1600)
    if enter:
        page.keyboard.press("Enter")
        page.wait_for_timeout(900)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, slow_mo=400, height=1100)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/records?tab=records-tab",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    print("token:", TOKEN)

    page.get_by_role("button", name="Adicionar").first.click(timeout=8000)
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)

    # --- Preenche obrigatorios ---
    pick_pessoa(page)                                             # Pessoas*
    tw.snap(page, PASTA, "03a-pessoas")
    rs_pick(page, "Selecione ou crie um provedor", "QA Provider") # Provedor* (cria/seleciona)
    rs_pick(page, "Digite o nome do conteúdo", TOKEN)             # Conteudo* (nome unico, cria)
    rs_pick(page, "Digite ou selecione o tipo da experiência", "Treinamento")  # Tipo*
    rs_pick(page, "Selecione as categorias", "")                  # Categorias* (abre e pega 1a)

    page.fill("#workload_seconds", "01:00:00")                    # Carga horaria*
    page.fill("#endDate", "2026-06-30")                           # Data de termino*
    page.wait_for_timeout(500)
    tw.snap(page, PASTA, "03-form-preenchido")

    # --- Salvar ---
    page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=8000)
    page.wait_for_timeout(2500)
    # captura toast
    toast = page.evaluate(
        """()=>{const els=Array.from(document.querySelectorAll('[class*=toast],[role=alert],[class*=Toast],[class*=chakra-alert]'));
            return els.map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(Boolean);}"""
    )
    print("[toast]:", toast)
    tw.snap(page, PASTA, "04-pos-salvar-toast")

    # --- Volta a listagem e procura o TOKEN ---
    page.goto(f"{c['base_url']}/o/{c['org_id']}/records?tab=records-tab",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    # busca pelo token
    try:
        busca = page.get_by_placeholder(re.compile("Pesquise", re.I)).first
        busca.click(); page.keyboard.type(TOKEN, delay=30)
        page.keyboard.press("Enter"); page.wait_for_timeout(3000)
    except Exception as e:
        print("   busca falhou:", e)
    tw.snap(page, PASTA, "05-listagem-busca")

    # checa LINHAS/cards que contem o token (nao o body inteiro — a caixa de busca tb tem o token)
    linhas_com_token = page.evaluate(
        r"""(t)=>Array.from(document.querySelectorAll('tbody tr,[role=row],[class*=card],li'))
            .filter(e=>(e.innerText||'').includes(t))
            .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,140))""",
        TOKEN,
    )
    print(f"[RESULTADO] linhas com o token na listagem: {len(linhas_com_token)}")
    for l in linhas_com_token:
        print("  ", l)
    ctx.close()
    browser.close()
print("OK")
