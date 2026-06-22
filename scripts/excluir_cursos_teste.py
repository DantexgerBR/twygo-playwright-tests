# -*- coding: utf-8 -*-
"""Exclui os cursos de teste de qualidade-IA (807992..807996) da org 37061.
Modo recon (RECON=1): só mapeia o caminho de exclusão de 1 curso, sem excluir.
Modo real: exclui os ids passados em IDS (default os 5)."""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
RECON = os.environ.get("RECON") == "1"
IDS = [x for x in os.environ.get("IDS", "807992,807993,807994,807995,807996").split(",") if x]
PASTA = tw.ROOT / "evidencias" / "qualidade_ia_cleanup"


def excluir(page, cid):
    # abre a página de edição do curso e procura a ação de excluir
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit",
              wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, f"edit-{cid}")
    # botões/menus de exclusão visíveis
    acoes = page.evaluate(
        """()=>[...document.querySelectorAll('button,[role=button],[role=menuitem],a')]
            .filter(e=>e.offsetParent!==null)
            .map(e=>({t:(e.innerText||e.getAttribute('aria-label')||e.title||'').replace(/\\s+/g,' ').trim(),
                      testid:e.getAttribute('data-test-id')}))
            .filter(o=>/exclui|delet|remover|lixeira|trash/i.test(o.t)||/delet|trash|remove/i.test(o.testid||''))"""
    )
    print(f"  [{cid}] ações de exclusão: {acoes}")
    if RECON:
        return False
    # tentar clicar a 1a ação de excluir
    btn = page.get_by_role("button", name=re.compile(r"Excluir|Excluir curso|Remover", re.I)).first
    if not (btn.count() and btn.is_visible()):
        # talvez seja um ícone de lixeira (aria-label)
        btn = page.locator("button[aria-label*='xclui' i], button[aria-label*='emover' i], [data-test-id*='delete']").first
    if not (btn.count() and btn.is_visible()):
        print(f"  [{cid}] NÃO achei botão de exclusão na tela de edição")
        return False
    btn.click(timeout=6000)
    page.wait_for_timeout(1500)
    # confirmar no diálogo
    conf = page.get_by_role("button", name=re.compile(r"^(Excluir|Confirmar|Sim)", re.I))
    for i in range(conf.count()):
        if conf.nth(i).is_visible():
            conf.nth(i).click(timeout=6000); break
    page.wait_for_timeout(3000)
    tw.snap(page, PASTA, f"pos-excluir-{cid}")
    print(f"  [{cid}] exclusão acionada")
    return True


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    alvos = IDS[:1] if RECON else IDS
    print(f"{'RECON' if RECON else 'EXCLUSÃO'} — alvos: {alvos}")
    for cid in alvos:
        print(f"\n=== curso {cid} ===")
        try:
            excluir(page, cid)
        except Exception as e:
            print(f"  [{cid}] ERRO {e}")
    ctx.close(); browser.close()
