"""20224 prov passo 1: criar avaliacao modelo (Desempenho) p/ usar no ciclo."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")
NOME = "QA 20224 modelo desempenho"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/assessments/new?profile=admin", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    page.fill("input[placeholder*='nome do question']", NOME)
    page.get_by_text("Avaliação de desempenho", exact=True).click(); page.wait_for_timeout(800)
    # salvar (ja vem com 1 pergunta + 2 opcoes por padrao)
    page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click()
    page.wait_for_timeout(2500)
    print("URL pos-salvar:", page.url)
    toast = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,5)""")
    print("TOAST:", toast)
    tw.snap(page, PASTA, "07-modelo-criado")
    ctx.close(); browser.close()
print("OK")
