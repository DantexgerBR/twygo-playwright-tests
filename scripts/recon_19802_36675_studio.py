# -*- coding: utf-8 -*-
"""Recon 19802 — o 36675 tem o Studio/assistente de IA? (pra gerar com modelo
multi-corpo template 70/71). Checa listagem nova + new_with_ai."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19802_variacao"
c = tw.cfg()  # 36675
with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    try:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
                  wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page); page.wait_for_timeout(4000)
        corpo = page.evaluate("()=>document.body.innerText")
        tem_criar_ia = bool(re.search(r"Criar curso com IA", corpo, re.I))
        tem_lista_nova = bool(re.search(r"Lista de conte[uú]dos|Tipo de experi[êe]ncia", corpo, re.I))
        print(f"[36675] 'Criar curso com IA'={tem_criar_ia} | listagem nova={tem_lista_nova}")
        tw.snap(page, PASTA, "36675-listagem")
        # tentar o assistente de IA direto
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new_with_ai",
                  wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page); page.wait_for_timeout(4000)
        corpo2 = page.evaluate("()=>document.body.innerText")
        tem_assistente = bool(re.search(r"Assistente de cria|tema|p[úu]blico", corpo2, re.I))
        tem_404 = bool(re.search(r"404|não encontrad|not found", corpo2[:300], re.I))
        print(f"[36675] new_with_ai: assistente={tem_assistente} 404={tem_404} url={page.url}")
        tw.snap(page, PASTA, "36675-new-with-ai")
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "36675-erro")
    finally:
        ctx.close(); browser.close()
