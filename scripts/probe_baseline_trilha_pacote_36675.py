"""Probe BASELINE — fluxo atual de criação de Trilha/Pacote na org principal (36675).

Contexto: QA 1.1 do projeto Novo Estúdio (Artia 19705). TC7/TC8 da AT esperam que
os cards Trilha/Pacote "mantenham o fluxo atual". Na org 37061 (flag creation_studio
ON) os cards levam a /contents/new?kind=learning_path|package que renderiza um form
com título "Novo curso". Antes de cravar ❌, este probe estabelece o baseline: o que
o fluxo ATUAL (org sem a flag) renderiza nessas mesmas rotas e no botão "Adicionar".

Saída: evidencias/novo_estudio_baseline_trilha_pacote/*.png + log no stdout.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "novo_estudio_baseline_trilha_pacote"


def descrever_form(page, rotulo):
    """Captura título da página, H1/headings visíveis e URL atual."""
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)
    headings = page.locator("h1, h2, .page-title, [class*='title']").all_inner_texts()
    headings = [h.strip() for h in headings if h.strip()][:6]
    print(f"   [{rotulo}] url        = {page.url}")
    print(f"   [{rotulo}] tab title  = {page.title()!r}")
    print(f"   [{rotulo}] headings   = {headings}")


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True, slow_mo=150)
    c = tw.cfg("")
    print(f"== Baseline na org {c['org_id']} ({c['base_url']}) ==")
    tw.login(page, c)
    tw.snap(page, PASTA, "01-listagem-conteudos")

    # 1) O que o botão "Adicionar" faz no fluxo atual?
    print("\n-- Botão 'Adicionar' na listagem de Conteúdos --")
    btn = page.get_by_role("button", name="Adicionar").first
    link = page.get_by_role("link", name="Adicionar").first
    alvo = btn if btn.count() else link
    if alvo.count():
        alvo.click()
        page.wait_for_timeout(2000)
        # Se abriu menu/dropdown, lista as opções; se navegou, mostra a URL
        itens = page.locator("[role=menu] [role=menuitem], .dropdown-menu a").all_inner_texts()
        itens = [i.strip() for i in itens if i.strip()]
        print(f"   opções do menu (se houver): {itens}")
        print(f"   url após click: {page.url}")
        tw.snap(page, PASTA, "02-apos-adicionar")
    else:
        print("   botão 'Adicionar' não encontrado!")

    # 2) Rotas diretas — o que o fluxo atual renderiza para cada kind?
    for kind, slug in [("course", "03-kind-course"),
                       ("learning_path", "04-kind-learning-path"),
                       ("package", "05-kind-package")]:
        print(f"\n-- /contents/new?kind={kind} --")
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new?kind={kind}",
                  wait_until="domcontentloaded", timeout=30000)
        descrever_form(page, kind)
        tw.snap(page, PASTA, slug)

    ctx.close()
    browser.close()

print("\n[ok] baseline capturado em", PASTA)
