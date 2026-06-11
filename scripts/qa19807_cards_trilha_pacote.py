# -*- coding: utf-8 -*-
"""Card 19807 [P1] — validar fix R1: cards "Trilha" e "Pacote" da página
"O que você quer criar?" devem abrir os fluxos corretos ("Nova trilha"/"Novo
pacote"), não mais o form "Novo curso". PR twyg-app#10599 (kind numérico).

Org 37061 (novoestudio principal). Também re-checa o card "Curso" (regressão).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa19807_cards_trilha_pacote"
c = tw.cfg("NOVOEST")


def titulo_form(page):
    """Captura o título visível do formulário + breadcrumb."""
    return page.evaluate(
        """()=>{
            const pega=(sel)=>{const e=[...document.querySelectorAll(sel)]
                .find(x=>x.offsetParent!==null && (x.innerText||'').trim());
                return e?(e.innerText||'').replace(/\\s+/g,' ').trim():''};
            return {h:(pega('h1')||pega('h2')||pega('h3')),
                    bc:pega('[class*=breadcrumb], nav[aria-label*=read], .chakra-breadcrumb')};
        }"""
    )


def testar_card(page, nome, snap_prefix):
    page.goto(f"{c['base_url']}/o/{c['org_id']}/studio", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    card = page.get_by_text(nome, exact=True).first
    card.scroll_into_view_if_needed()
    card.click(timeout=8000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    info = titulo_form(page)
    print(f"[{nome}] url={page.url}")
    print(f"[{nome}] título={info['h']!r} breadcrumb={info['bc']!r}")
    tw.snap(page, PASTA, snap_prefix)
    return {"card": nome, "url": page.url, **info}


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    page.goto(f"{c['base_url']}/o/{c['org_id']}/studio", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "01-pagina-cards")

    resultados = [
        testar_card(page, "Trilha", "02-destino-trilha"),
        testar_card(page, "Pacote", "03-destino-pacote"),
        testar_card(page, "Curso", "04-destino-curso"),
    ]

    print("\n=== RESUMO ===")
    esperado = {"Trilha": "trilha", "Pacote": "pacote", "Curso": "curso"}
    for r in resultados:
        alvo = esperado[r["card"]]
        texto = f"{r['h']} {r['bc']}".lower()
        ok = alvo in texto and ("novo curso" not in texto or alvo == "curso")
        print(f"  {r['card']:8s} → {'✔ fluxo correto' if ok else '✖ DESVIO'} | título={r['h']!r} | url={r['url']}")
    ctx.close(); browser.close()
