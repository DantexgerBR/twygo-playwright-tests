"""RECON DOM 18468 — mapear a estrutura das mensagens do chat de importacao
(classes/roles por turno) pra escopar a deteccao na ULTIMA mensagem do assistente.
Tambem tenta o hamburguer (botao, nao texto) e dumpa as opcoes.
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
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    page.get_by_role("button", name=re.compile(r"Importa.{0,4}o Inteligente", re.I)).first.click(force=True)
    page.wait_for_timeout(3500)

    # classes 'aui-' presentes (assistant-ui)
    auis = page.evaluate(
        "()=>{const s=new Set();document.querySelectorAll('[class*=aui-]').forEach(e=>String(e.className).split(/\\s+/).forEach(c=>{if(c.startsWith('aui-'))s.add(c);}));return [...s].slice(0,40);}")
    print(f"[classes aui-] {auis}")

    # candidatos a container de mensagem do assistente
    msgs = page.evaluate(
        r"""()=>{
            const sels=['[data-role=assistant]','.aui-assistant-message-root','.aui-assistant-message-content','[class*=assistant-message]','[class*=message-root]'];
            const out={};
            sels.forEach(s=>{out[s]=document.querySelectorAll(s).length;});
            return out;
        }""")
    print(f"[contagem seletores msg] {msgs}")

    # hamburguer: botao com icone 'menu'
    try:
        btns = page.locator("button").filter(has_text=re.compile(r"^menu$", re.I))
        print(f"[botao menu] count={btns.count()}")
        if btns.count():
            btns.first.click(timeout=4000); page.wait_for_timeout(1500)
            tw.snap(page, PASTA, "50-menu")
            itens = page.evaluate(
                "()=>Array.from(document.querySelectorAll('button,a,[role=menuitem],li')).filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<40).slice(0,40)")
            print(f"[itens menu] {itens}")
    except Exception as e:
        print(f"[menu] erro {e}")

    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
