# -*- coding: utf-8 -*-
"""Confirma se a Aula 9296251 (curso SQL 807992) tem slides ou está vazia.
Reabre o sub-tab Conteúdo com espera longa, conta as 'partes da aula' e relê
o estado de pendentes no estúdio. Anti-falso-positivo: só conclui com evidência."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qualidade_ia_sql"
CURSO = "807992"
AULA = "9296251"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=1000)
    tw.login(page, c)

    # estado no estúdio
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio",
              wait_until="domcontentloaded", timeout=45000)
    tw.dispensar_nps(page)
    page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
    page.wait_for_timeout(3000)
    estado = page.evaluate(
        r"""()=>[...document.querySelectorAll('[data-test-id]')]
            .filter(e=>/^creation-studio-activity-card-\d+$/.test(e.getAttribute('data-test-id')||''))
            .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim())"""
    )
    print("[estúdio] estado das atividades:")
    for e in estado:
        print(f"  - {e}")

    # abrir a aula, sub-tab Conteúdo, espera longa
    page.goto(f"{c['base_url']}/o/{c['org_id']}/studio/activities/{AULA}/edit?type=lesson&eventId={CURSO}",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
    page.wait_for_timeout(12000)  # espera longa pra slides carregarem
    tw.dispensar_nps(page)

    # contar partes da aula (cada parte costuma ser um item clicável na coluna esquerda)
    info = page.evaluate(
        """()=>{
            const esq=[...document.querySelectorAll('*')].find(e=>/Partes da aula/i.test(e.textContent||'') && e.children.length<30);
            // heurística: itens de parte costumam ter miniatura/numeração
            const partes=[...document.querySelectorAll('[class*=part i],[class*=slide i],[data-test-id*=part],[data-test-id*=slide]')]
                .filter(e=>e.offsetParent!==null).length;
            const temAdicionar=/Adicionar parte/i.test(document.body.innerText);
            const roteiro=[...document.querySelectorAll('textarea')].map(t=>(t.value||'').trim()).filter(Boolean);
            return {partesHeur:partes, temAdicionar, roteiros:roteiro.slice(0,3)};
        }"""
    )
    print(f"\n[aula {AULA}] heurística partes={info['partesHeur']} | tem 'Adicionar parte'={info['temAdicionar']}")
    print(f"[aula {AULA}] roteiros não-vazios: {info['roteiros']}")
    tw.snap(page, PASTA, "61-aula-conteudo-espera-longa", full=True)
    ctx.close(); browser.close()
