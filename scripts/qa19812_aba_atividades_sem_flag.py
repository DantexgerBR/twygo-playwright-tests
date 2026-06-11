# -*- coding: utf-8 -*-
"""19812 [P2] — SEM a feature flag do Estúdio, a aba "Atividades" não pode aparecer
na criação de curso (PR 10601). Env testedemigracao (org 19653, sem flag).

Valida o momento do bug: form de criação (/contents/new?kind=course|0) — a aba
"Atividades" NÃO deve estar na lista de abas. Read-only (não salva nada).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa19812_aba_sem_flag"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    print(f"[ok] logado em {page.url}")

    abas_por_rota = {}
    for rota in ["contents/new?kind=course", "contents/new?kind=0"]:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/{rota}",
                  wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        tw.dispensar_nps(page)
        abas = page.evaluate(
            """()=>[...document.querySelectorAll("[role='tab'], .chakra-tabs__tab, [data-test-id^='tab-']")]
                .filter(e=>e.offsetParent!==null)
                .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(Boolean)"""
        )
        if not abas:
            abas = page.evaluate(
                """()=>{const cont=[...document.querySelectorAll('nav,ul,div')].find(e=>
                    /Identifica/.test(e.innerText||'') && /Acesso/.test(e.innerText||'') &&
                    e.querySelectorAll('a,button,div').length<60);
                  return cont?(cont.innerText||'').split('\\n').map(s=>s.trim()).filter(Boolean):[];}"""
            )
        abas_por_rota[rota] = abas
        print(f"[{rota}] abas visíveis: {abas}")
        tw.snap(page, PASTA, f"criacao-{re.sub(r'[^a-z0-9]+', '-', rota)}")

    print("\n=== RESUMO ===")
    for rota, abas in abas_por_rota.items():
        tem = any("atividade" in a.lower() for a in abas)
        print(f"  {rota}: aba 'Atividades' presente? {'✖ SIM (bug persiste)' if tem else '✔ NÃO (fix ok)'}")
    ctx.close(); browser.close()
