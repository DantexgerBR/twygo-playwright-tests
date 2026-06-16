# -*- coding: utf-8 -*-
"""Recon 19802 — lista os modelos selecionáveis no 36675 (aba Modelo de um curso
novo) com nome + nº de páginas, pra identificar um com múltiplas variantes de corpo
(templates 70/71 = events 806746/806747 têm 2 body cada)."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19802_variacao"
c = tw.cfg()  # 36675
with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1500, height=950)
    tw.login(page, c)
    try:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new?kind=course",
                  wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        page.wait_for_timeout(5000)
        # ir pra aba Modelo
        page.evaluate("()=>{const t=[...document.querySelectorAll('[role=tab]')].find(e=>/^Modelo$/i.test((e.innerText||'').trim()));if(t)t.click();}")
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "36675-modelos", full=True)
        # dump dos cards de modelo (texto)
        cards = page.evaluate(r"""()=>{
          const txt=document.body.innerText;
          // pegar blocos que pareçam cards de modelo (nome + 'X aulas · Y pág')
          const m=[...txt.matchAll(/([^\n]{3,60})\n[^\n]*?(\d+)\s*aulas?[^\n]*?(\d+)\s*p[áa]g/gi)].map(x=>({nome:x[1].trim(),aulas:x[2],pag:x[3]}));
          return m.slice(0,20);
        }""")
        print("[36675] modelos (nome / aulas / pág):")
        for cd in cards: print("  ", cd)
        # também listar nomes via possíveis test-ids/headings
        nomes = page.evaluate(r"""()=>[...document.querySelectorAll('h3,h4,[class*=title],[class*=name]')]
          .map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<60).slice(0,30)""")
        print("[36675] headings:", nomes)
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "36675-modelos-erro")
    finally:
        ctx.close(); browser.close()
