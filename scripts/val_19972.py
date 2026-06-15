# -*- coding: utf-8 -*-
"""19972 [P1] — Geração de token de autenticação a cada conversa do copiloto.
Abre o copiloto, envia 2 mensagens e captura as requisições de rede para ver se
uma chamada de token/auth dispara A CADA mensagem (bug) ou é reaproveitada."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoC"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
PADRAO = re.compile(r"token|auth|jwt|session|/login|refresh|sign[_-]?in|oauth|credential", re.I)

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio",
              wait_until="domcontentloaded", timeout=45000)
    tw.dispensar_nps(page)
    page.wait_for_timeout(4000)

    # abrir copiloto (FAB toggle ou Ctrl+J)
    try:
        fab = page.locator(tid("copilot-drawer-toggle")).first
        if fab.count(): fab.click(timeout=5000)
        else: page.keyboard.press("Control+j")
    except Exception:
        page.keyboard.press("Control+j")
    page.wait_for_timeout(4000)
    drawer = page.locator(tid("copilot-drawer")).first
    print(f"[copiloto] drawer visível? {drawer.count() and drawer.is_visible()}")
    tw.snap(page, PASTA, "19972-copiloto-aberto")

    # captura de requisições
    reqs = []
    page.on("request", lambda r: reqs.append((r.method, r.url.split('?')[0])))

    def enviar(msg):
        # input do copiloto: placeholder "Escreva uma mensagem..."
        campo = page.get_by_placeholder(re.compile(r"Escreva uma mensagem", re.I)).first
        campo.click(timeout=5000); campo.fill(msg); page.wait_for_timeout(500)
        campo.press("Enter")

    # mensagem 1
    marca1 = len(reqs)
    enviar("Olá, tudo bem?")
    page.wait_for_timeout(15000)
    reqs1 = reqs[marca1:]
    tok1 = [u for (m, u) in reqs1 if PADRAO.search(u)]
    print(f"\n[msg 1] requisições={len(reqs1)} | token/auth: {sorted(set(tok1))}")

    # mensagem 2
    marca2 = len(reqs)
    enviar("Me dê uma dica rápida.")
    page.wait_for_timeout(15000)
    reqs2 = reqs[marca2:]
    tok2 = [u for (m, u) in reqs2 if PADRAO.search(u)]
    print(f"[msg 2] requisições={len(reqs2)} | token/auth: {sorted(set(tok2))}")

    tw.snap(page, PASTA, "19972-pos-mensagens")
    # bug = a mesma chamada de token/auth aparece NAS DUAS mensagens (uma por conversa)
    repetidos = sorted(set(tok1) & set(tok2))
    print(f"\n[análise] endpoints token/auth repetidos nas 2 mensagens: {repetidos}")
    veredito = "FALHOU (token gerado a cada mensagem)" if repetidos else "PASSOU (sem geração de token por mensagem)"
    print(f"=> 19972: {veredito}")
    print(f"[debug] amostra de todos os hosts/paths únicos com 'ai'/'agent'/'copilot':")
    interess = sorted(set(u for (m, u) in reqs if re.search(r"ai|agent|copilot|knowledge|chat|conversa", u, re.I)))
    for u in interess[:25]:
        print(f"   {u}")
    ctx.close(); browser.close()
