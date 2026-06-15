# -*- coding: utf-8 -*-
"""Recon do 'Assistente de criação' (org 37061) — entra no wizard e mapeia os
campos do briefing passo a passo, SEM disparar a geração (pra não poluir a org)."""
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
            const inputs=[...document.querySelectorAll('input,textarea,select,[role=slider],[role=radio],[role=switch]')].filter(vis)
              .map(e=>({tag:e.tagName,type:e.type||e.getAttribute('role'),name:e.name,ph:e.placeholder,
                        testid:e.getAttribute('data-test-id'),
                        label:(e.labels&&e.labels[0]?e.labels[0].innerText:'').replace(/\\s+/g,' ').slice(0,50)}));
            const botoes=[...document.querySelectorAll('button,[role=button]')].filter(vis)
              .map(e=>(e.innerText||e.getAttribute('aria-label')||'').replace(/\\s+/g,' ').trim()).filter(Boolean);
            const txt=document.body.innerText.replace(/\\s+/g,' ').slice(0,700);
            return {inputs,botoes:[...new Set(botoes)],txt};
        }"""
    )
    print(f"\n--- {rotulo} ---\n  TXT: {info['txt'][:400]}\n  INPUTS: {info['inputs']}\n  BOTOES: {info['botoes']}")
    return info


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new_with_ai",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)

    # clicar no card "Assistente de criação"
    card = page.get_by_text(re.compile(r"Assistente de cria", re.I)).first
    card.click(timeout=10000)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "02-assistente-passo1", full=True)
    dump(page, "ASSISTENTE - tela 1")
    print(f"\n[url] {page.url}")

    # percorrer até 6 passos preenchendo o mínimo, capturando cada tela
    for passo in range(2, 8):
        # preencher campos de texto vazios visíveis (tema)
        try:
            campos = page.locator("textarea:visible, input[type=text]:visible")
            for i in range(min(campos.count(), 3)):
                ci = campos.nth(i)
                if ci.is_visible() and not ci.input_value():
                    ci.fill("Fundamentos de SQL para iniciantes")
                    page.wait_for_timeout(500)
        except Exception:
            pass
        avancar = page.get_by_role("button", name=re.compile(r"Avançar|Próximo|Continuar|Gerar curso|Gerar|Concluir|Criar curso", re.I))
        vis = [i for i in range(avancar.count()) if avancar.nth(i).is_visible() and avancar.nth(i).is_enabled()]
        if not vis:
            print(f"[passo {passo}] sem botão de avançar habilitado")
            tw.snap(page, PASTA, f"0{passo}-assistente-passo{passo}-bloqueado", full=True)
            dump(page, f"ASSISTENTE - tela {passo} (avançar desabilitado)")
            break
        rotulo_btn = avancar.nth(vis[0]).inner_text().strip()
        if re.search(r"Gerar|Criar curso|Concluir", rotulo_btn, re.I):
            print(f"[passo {passo}] PRÓXIMO clique seria '{rotulo_btn}' = DISPARO. Parando antes de poluir a org.")
            tw.snap(page, PASTA, f"0{passo}-assistente-antes-disparo", full=True)
            dump(page, f"ASSISTENTE - tela final (botão de disparo: {rotulo_btn})")
            break
        print(f"[passo {passo}] clicando '{rotulo_btn}'")
        avancar.nth(vis[0]).click(timeout=8000)
        page.wait_for_timeout(4000)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, f"0{passo}-assistente-passo{passo}", full=True)
        dump(page, f"ASSISTENTE - tela {passo}")

    print(f"\n[recon] url final: {page.url}")
    ctx.close(); browser.close()
