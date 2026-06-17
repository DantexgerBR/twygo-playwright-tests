import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "emoji_toast_18539"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/events?tab=events", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)

    # kebab da 1a linha
    page.locator('[data-icon="more_vert"]').first.click(force=True)
    page.wait_for_timeout(1200)
    tw.snap(page, PASTA, "03-kebab")
    # clicar Editar
    page.get_by_role("menuitem", name=re.compile("Editar", re.I)).first.click()
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "04-identificacao")
    print("url:", page.url)

    # campo Nome (input com valor atual)
    nome = page.locator("input#name, input[name='name'], input[name*='title'], input[name*='nome']").first
    if not nome.count():
        # fallback: primeiro input de texto visível com valor
        nome = page.locator("input[type=text]:visible").first
    print("valor atual nome:", nome.input_value())
    nome.click()
    nome.fill("Curso Padrão 😀🎉")
    page.wait_for_timeout(800)
    tw.snap(page, PASTA, "05-nome-com-emoji")

    # salvar
    page.get_by_role("button", name=re.compile(r"Salvar|Salvar e fechar|Concluir", re.I)).first.click()
    page.wait_for_timeout(3500)
    tw.snap(page, PASTA, "06-apos-salvar")
    # capturar toast
    toast = page.evaluate(
        "()=>{const sels=['.chakra-toast','[role=alert]','[role=status]','.chakra-alert','.Toastify__toast'];"
        "for(const s of sels){const els=document.querySelectorAll(s);for(const e of els){if(e.offsetParent!==null&&(e.innerText||'').trim())return e.innerText.trim();}}return '(sem toast)';}"
    )
    print("TOAST:", toast)
    ctx.close(); browser.close()
