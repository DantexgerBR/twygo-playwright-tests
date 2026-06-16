# -*- coding: utf-8 -*-
"""Recon 19972 — abrir o copiloto no Studio e mapear input/enviar do chat."""
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
        tw.snap(page, PASTA, "00-studio")
        # tentar abrir o copiloto: FAB roxo (sparkle) topo-direito ou bolha de chat
        # varrer botões com aria-label/ícone de copiloto/assistente/chat
        cand = page.evaluate(r"""()=>{
          const els=[...document.querySelectorAll('button,[role=button],a,div')];
          return els.filter(e=>{const s=((e.getAttribute&&(e.getAttribute('aria-label')||''))+' '+(e.title||'')+' '+(e.className||'')).toLowerCase();
            return /copilot|assistent|sparkle|auto_awesome|magic|chat|ia/.test(s) && e.offsetParent!==null;})
            .slice(0,10).map(e=>({tag:e.tagName,al:e.getAttribute&&e.getAttribute('aria-label'),cls:(e.className||'').toString().slice(0,50)}));
        }""")
        print("[recon] candidatos copiloto:", cand)
        # clicar no canto superior direito (FAB sparkle) por coordenada aproximada
        try:
            # botão roxo no topo direito visto nos screenshots (~x=1432,y=124 no viewport 1500) -> ajustar p/ 1440
            page.mouse.click(1410, 120)
            page.wait_for_timeout(2500)
        except Exception as e:
            print("click fab:", e)
        tw.snap(page, PASTA, "01-pos-click-fab")
        # procurar input de chat
        inputs = page.evaluate(r"""()=>[...document.querySelectorAll('textarea,input[type=text],[contenteditable=true]')]
          .filter(e=>e.offsetParent!==null).map(e=>({tag:e.tagName,ph:e.getAttribute('placeholder')||'',name:e.getAttribute('name')||''})).slice(0,10)""")
        print("[recon] inputs visíveis:", inputs)
        corpo = page.evaluate("()=>document.body.innerText")
        print("[recon] tem 'copiloto/assistente' no texto?", bool(re.search(r"copilot|assistente|pergunte|digite", corpo, re.I)))
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "99-erro")
    finally:
        ctx.close(); browser.close()
