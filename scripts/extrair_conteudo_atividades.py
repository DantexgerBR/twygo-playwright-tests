# -*- coding: utf-8 -*-
"""Extrai o conteúdo gerado das atividades de um curso (default SQL 807992):
pega os ids top-level no estúdio e abre o form de cada atividade lendo o texto
real (título + contenteditable/slides). Salva um dump .txt pra avaliação."""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

CURSO = os.environ.get("CURSO", "807992")
SLUG = os.environ.get("SLUG", "sql")
PASTA = tw.ROOT / "evidencias" / f"qualidade_ia_{SLUG}"
DUMP = PASTA / "conteudo_extraido.txt"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
    page.goto(url_studio, wait_until="domcontentloaded", timeout=45000)
    tw.dispensar_nps(page)
    page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
    page.wait_for_timeout(3000)

    # ids top-level (test-id que termina em número) + tipo (via texto do card)
    ativs = page.evaluate(
        r"""()=>{
            const out=[];
            document.querySelectorAll('[data-test-id]').forEach(e=>{
                const m=(e.getAttribute('data-test-id')||'').match(/^creation-studio-activity-card-(\d+)$/);
                if(m){const t=(e.innerText||'').replace(/\s+/g,' ').trim();
                       out.push({id:m[1], txt:t.slice(0,80)});}
            });
            return out;
        }"""
    )
    print(f"[studio] {len(ativs)} atividades top-level:")
    for a in ativs:
        print(f"  - {a['id']}: {a['txt']}")

    linhas = [f"=== CURSO {SLUG} ({CURSO}) ===\n"]
    for a in ativs:
        aid = a["id"]
        # descobrir o type pela URL do form (tenta abrir genérico)
        for typ in ["page", "lesson", "external", "pdf", "text"]:
            url = f"{c['base_url']}/o/{c['org_id']}/studio/activities/{aid}/edit?type={typ}&eventId={CURSO}"
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3500)
            tw.dispensar_nps(page)
            # se carregou um form de atividade (tem título), aceita
            if page.locator('input[name="title"]:visible, [contenteditable="true"]:visible').count():
                break
        titulo = ""
        try:
            titulo = page.locator('input[name="title"]:visible').first.input_value()
        except Exception:
            pass
        # conteúdo: todos os contenteditable + headings/parágrafos do editor
        conteudo = page.evaluate(
            """()=>{
                const eds=[...document.querySelectorAll('[contenteditable="true"]')].filter(e=>e.offsetParent!==null);
                const edTxt=eds.map(e=>(e.innerText||'').trim()).filter(Boolean).join('\\n---SLIDE---\\n');
                return edTxt;
            }"""
        )
        print(f"\n[ativ {aid}] titulo={titulo!r} | conteudo={len(conteudo)} ch")
        print(f"   amostra: {conteudo[:200]!r}")
        tw.snap(page, PASTA, f"50-ativ-{aid}", full=True)
        linhas.append(f"\n----- ATIVIDADE {aid} | título: {titulo} -----\n{conteudo}\n")

    DUMP.parent.mkdir(parents=True, exist_ok=True)
    DUMP.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\n[dump] salvo em {DUMP}")
    ctx.close(); browser.close()
