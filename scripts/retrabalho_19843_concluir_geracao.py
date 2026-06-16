# -*- coding: utf-8 -*-
"""19843 [P1] D18 — botão "Concluir geração com IA" deve gerar VÁRIAS atividades
(todos os artefatos pendentes via waves, auto-aceite). PR #10592.
Clica o botão e observa quantas atividades entram em geração."""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19843_concluir_geracao"
tid = lambda v: f'[data-test-id="{v}"]'
c = tw.cfg("NOVOEST")
CURSO = "807533"
URL = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

# conta indícios de geração em andamento na lista (badges/textos)
JS_GERANDO = (
    "()=>{const t=document.body.innerText;"
    "const m=t.match(/gerando|na fila|aguardando gera|em gera|processando/gi);"
    "return m?m.length:0;}"
)
JS_PENDENTES = "()=>{const m=document.body.innerText.match(/pendente/gi);return m?m.length:0;}"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1500, height=950)
    tw.login(page, c)
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=25000)
        page.wait_for_timeout(3000)
        pend0 = page.evaluate(JS_PENDENTES); ger0 = page.evaluate(JS_GERANDO)
        print(f"[antes] pendentes~{pend0} gerando~{ger0}")
        tw.snap(page, PASTA, "01-antes")

        # botão "Concluir geração com IA"
        btn = page.get_by_role("button", name=re.compile(r"Concluir gera[çc][ãa]o com IA", re.I)).first
        print(f"[btn] encontrado={btn.count()} habilitado={btn.is_enabled() if btn.count() else '-'}")
        if not btn.count() or not btn.is_enabled():
            # pode precisar abrir uma atividade primeiro pra revelar o botão global
            page.wait_for_timeout(1500)
        btn.scroll_into_view_if_needed(); btn.click(timeout=8000)
        page.wait_for_timeout(2000)
        tw.snap(page, PASTA, "02-pos-clique")
        # capturar o texto do diálogo de confirmação (prova do dispatch geral)
        try:
            dlg = page.evaluate("()=>{const m=document.body.innerText.match(/Gerar\\s+\\d+\\s+artefatos?\\s+de\\s+\\d+\\s+atividades?[^\\n]*/i);return m?m[0]:null;}")
            print(f"[dialogo] {dlg}")
        except Exception: pass
        # confirmar: botão "Concluir geração" (NÃO o externo "...com IA")
        try:
            page.get_by_role("button", name=re.compile(r"^Concluir gera[çc][ãa]o$", re.I)).first.click(timeout=5000)
            page.wait_for_timeout(2500); tw.dispensar_nps(page)
        except Exception as e:
            print(f"[confirmar] {e}")
        tw.snap(page, PASTA, "03-pos-confirmar")

        # observar dispatch por ~150s: gerando sobe e/ou pendentes cai
        picos = []; pends = [pend0]; fim = time.time() + 150; i = 0
        while time.time() < fim:
            page.wait_for_timeout(12000)
            # reabrir a lista pra refletir estado atual
            try: page.goto(URL, wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(page); page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=12000); page.wait_for_timeout(1500)
            except Exception: pass
            g = page.evaluate(JS_GERANDO); pend = page.evaluate(JS_PENDENTES)
            picos.append(g); pends.append(pend)
            print(f"   [obs {i}] gerando~{g} pendentes~{pend}")
            if i in (2, 5, 9): tw.snap(page, PASTA, f"obs-{i}")
            i += 1
        tw.snap(page, PASTA, "09-final", full=True)
        pico = max(picos) if picos else 0
        caiu = pend0 - min(pends)
        print(f"\n=> pico 'gerando' simultâneas={pico} | pendentes {pend0}->{min(pends)} (caiu {caiu})")
        ok = pico >= 2 or caiu >= 2
        print(f"=> 19843 {'PASSOU (geração geral de várias atividades)' if ok else 'checar screenshots'}")
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "99-erro")
    finally:
        ctx.close(); browser.close()
