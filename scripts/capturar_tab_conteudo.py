# -*- coding: utf-8 -*-
"""Abre cada atividade do curso e captura o sub-tab 'Conteúdo' (slides/página real
gerada pela IA): screenshots full-page + extração de texto. Default SQL 807992."""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

CURSO = os.environ.get("CURSO", "807992")
SLUG = os.environ.get("SLUG", "sql")
PASTA = tw.ROOT / "evidencias" / f"qualidade_ia_{SLUG}"
DUMP = PASTA / "slides_extraidos.txt"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=1000)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio",
              wait_until="domcontentloaded", timeout=45000)
    tw.dispensar_nps(page)
    page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
    page.wait_for_timeout(3000)
    ativs = page.evaluate(
        r"""()=>{const out=[];document.querySelectorAll('[data-test-id]').forEach(e=>{
            const m=(e.getAttribute('data-test-id')||'').match(/^creation-studio-activity-card-(\d+)$/);
            if(m)out.push(m[1]);});return out;}"""
    )
    print(f"[studio] atividades: {ativs}")

    linhas = [f"=== CONTEÚDO/SLIDES — {SLUG} ({CURSO}) ===\n"]
    for aid in ativs:
        # abrir o form (tenta lesson e page)
        aberto = False
        for typ in ["lesson", "page"]:
            page.goto(f"{c['base_url']}/o/{c['org_id']}/studio/activities/{aid}/edit?type={typ}&eventId={CURSO}",
                      wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            tw.dispensar_nps(page)
            if page.get_by_role("tab", name=re.compile(r"^Conteúdo$", re.I)).count() or \
               page.get_by_text(re.compile(r"^Conteúdo$", re.I)).count():
                aberto = True; break
        titulo = ""
        try:
            titulo = page.locator('input[name="title"]:visible').first.input_value()
        except Exception:
            pass
        # clicar no sub-tab Conteúdo
        try:
            t = page.get_by_role("tab", name=re.compile(r"^Conteúdo$", re.I)).first
            if not t.count():
                t = page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first
            t.click(timeout=6000, force=True)
            page.wait_for_timeout(4000)
        except Exception as e:
            print(f"  [{aid}] não cliquei Conteúdo: {e}")
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, f"60-conteudo-{aid}", full=True)
        # extrair texto visível do conteúdo (slides/página)
        txt = page.evaluate(
            """()=>{
                const main=document.querySelector('main')||document.body;
                return (main.innerText||'').replace(/\\n{3,}/g,'\\n\\n').trim();
            }"""
        )
        print(f"\n[ativ {aid}] título={titulo!r} | conteúdo visível={len(txt)} ch")
        linhas.append(f"\n----- {aid} | {titulo} -----\n{txt[:4000]}\n")

    DUMP.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\n[dump] {DUMP}")
    ctx.close(); browser.close()
