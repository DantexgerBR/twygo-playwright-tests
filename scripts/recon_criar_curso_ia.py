# -*- coding: utf-8 -*-
"""Recon do assistente "Criar curso com IA" (org 37061) — mapeia os passos/campos
do wizard pra depois automatizar a geração de cursos e avaliar a qualidade."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "recon_criar_curso_ia"
c = tw.cfg("NOVOEST")


def dump(page, rotulo):
    info = page.evaluate(
        """()=>{
            const vis=e=>e.offsetParent!==null;
            const inputs=[...document.querySelectorAll('input,textarea,select')].filter(vis)
              .map(e=>({tag:e.tagName,type:e.type,name:e.name,ph:e.placeholder,
                        testid:e.getAttribute('data-test-id'),label:(e.labels&&e.labels[0]?e.labels[0].innerText:'').slice(0,40)}));
            const botoes=[...document.querySelectorAll('button,[role=button]')].filter(vis)
              .map(e=>(e.innerText||e.getAttribute('aria-label')||'').replace(/\\s+/g,' ').trim()).filter(Boolean);
            const heads=[...document.querySelectorAll('h1,h2,h3,h4,legend,[role=heading]')].filter(vis)
              .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(Boolean).slice(0,15);
            return {inputs,botoes:[...new Set(botoes)],heads};
        }"""
    )
    print(f"\n--- {rotulo} ---\n  HEADS: {info['heads']}\n  INPUTS: {info['inputs']}\n  BOTOES: {info['botoes']}")
    return info


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "00-events")

    btn = page.get_by_role("button", name=re.compile("Criar curso com IA", re.I)).first
    if not btn.count():
        # fallback: qualquer elemento clicável com esse texto
        btn = page.get_by_text(re.compile("Criar curso com IA", re.I)).first
    print(f"[btn 'Criar curso com IA'] count={btn.count()} visivel={btn.is_visible() if btn.count() else False}")
    btn.click(timeout=10000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    # checar bloqueio por flag/créditos
    toast = page.get_by_text(re.compile("não foi habilitada|nao foi habilitada|crédit|sem saldo", re.I))
    if toast.count() and toast.first.is_visible():
        print(f"[BLOQUEIO] {toast.first.inner_text()!r}")
    tw.snap(page, PASTA, "01-wizard-passo1", full=True)
    dump(page, "PASSO 1")

    # tentar avançar pelos passos preenchendo o mínimo, capturando cada tela
    for passo in range(2, 7):
        # preencher o primeiro campo de texto vazio com um tema (sonda do fluxo)
        try:
            campo = page.locator("textarea:visible, input[type=text]:visible").first
            if campo.count() and not campo.input_value():
                campo.fill("Fundamentos de SQL para iniciantes")
                page.wait_for_timeout(800)
        except Exception:
            pass
        avancar = page.get_by_role("button", name=re.compile(r"Avançar|Próximo|Continuar|Gerar|Criar|Concluir", re.I))
        vis = [i for i in range(avancar.count()) if avancar.nth(i).is_visible() and avancar.nth(i).is_enabled()]
        if not vis:
            print(f"[passo {passo}] sem botão de avançar habilitado — fim do wizard ou requer mais dados")
            break
        rotulo_btn = avancar.nth(vis[0]).inner_text()
        print(f"[passo {passo}] clicando '{rotulo_btn}'")
        avancar.nth(vis[0]).click(timeout=8000)
        page.wait_for_timeout(3500)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, f"0{passo}-wizard-passo{passo}", full=True)
        dump(page, f"PASSO {passo}")
        if re.search(r"Gerar|Criar curso|Concluir", rotulo_btn, re.I):
            print("[recon] cheguei no disparo de geração — PARANDO antes de poluir a org")
            break

    print(f"\n[recon] url final: {page.url}")
    ctx.close(); browser.close()
