# -*- coding: utf-8 -*-
"""Recon 19972 — abrir o chat do copiloto e mandar 1 mensagem; mapear input/envio."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19972_token"
tid = lambda v: f'[data-test-id="{v}"]'
c = tw.cfg("NOVOEST")
CURSO = "807533"
URL = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
        page.wait_for_timeout(2500)
        # abrir chat
        page.get_by_role("button", name=re.compile(r"open chat|chat|copilot|assistente", re.I)).first.click(timeout=6000)
        page.wait_for_timeout(3000)
        tw.snap(page, PASTA, "r-01-chat-aberto")
        # inputs visíveis
        inputs = page.evaluate(r"""()=>[...document.querySelectorAll('textarea,input[type=text],[contenteditable=true]')]
          .filter(e=>e.offsetParent!==null).map((e,i)=>({i,tag:e.tagName,ph:e.getAttribute('placeholder')||'',ce:e.getAttribute('contenteditable')||''}))""")
        print("[chat] inputs:", inputs)
        corpo = page.evaluate("()=>document.body.innerText")
        print("[chat] menciona copiloto/assistente?", bool(re.search(r"copilot|assistente|pergunte|como posso", corpo, re.I)))
        # tentar digitar e enviar 1 mensagem no input de chat (o que tiver placeholder de mensagem)
        alvo = None
        for sel in ['textarea', '[contenteditable=true]', 'input[type=text]']:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                try:
                    ph = (el.get_attribute("placeholder") or "")
                    if el.is_visible() and (re.search(r"mensagem|pergunt|digite|escreva|ajud", ph, re.I) or sel=='[contenteditable=true]'):
                        alvo = el; break
                except Exception: pass
            if alvo: break
        if not alvo:
            # fallback: último textarea visível
            ta = page.locator("textarea")
            for i in range(ta.count()-1, -1, -1):
                if ta.nth(i).is_visible(): alvo = ta.nth(i); break
        print(f"[chat] alvo de input encontrado? {alvo is not None}")
        if alvo:
            alvo.click(); alvo.fill("Olá, o que você consegue fazer?")
            page.wait_for_timeout(500)
            alvo.press("Enter")
            page.wait_for_timeout(8000)
            tw.snap(page, PASTA, "r-02-pos-mensagem", full=True)
            print("[chat] mensagem enviada")
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "r-99-erro")
    finally:
        ctx.close(); browser.close()
