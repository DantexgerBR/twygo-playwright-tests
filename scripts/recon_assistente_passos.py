# -*- coding: utf-8 -*-
"""Recon v3 — preenche o passo 1 do Assistente corretamente e percorre os passos
2..5 mapeando os campos, PARANDO antes do disparo de geração."""
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
              .map(e=>({type:e.type,name:e.name,ph:e.placeholder,checked:e.checked,
                        label:(e.labels&&e.labels[0]?e.labels[0].innerText:'').replace(/\\s+/g,' ').slice(0,40)}));
            const main=document.querySelector('main')||document.body;
            const txt=main.innerText.replace(/\\s+/g,' ').slice(0,500);
            const botoes=[...document.querySelectorAll('button')].filter(vis)
              .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(Boolean);
            return {inputs,txt,botoes:[...new Set(botoes)]};
        }"""
    )
    print(f"\n--- {rotulo} ---\n  TXT: {info['txt'][:300]}\n  INPUTS: {info['inputs']}\n  BOTOES: {info['botoes']}")
    return info


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new_with_ai",
              wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    page.get_by_text(re.compile(r"Assistente de cria", re.I)).first.click(timeout=10000)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)

    # ----- PASSO 1: preencher corretamente -----
    page.locator('input[name="theme"]').fill("Fundamentos de SQL")
    page.locator('input[name="targetAudience"]').fill("Iniciantes em banco de dados")
    n = page.locator('input[name="numberOfLessons"]')
    n.click(); n.fill(""); n.fill("3")
    # tipos: marcar Página e Aula
    for lbl in ["Página", "Aula"]:
        cb = page.get_by_text(lbl, exact=True).first
        try:
            cb.click(timeout=3000)
        except Exception:
            pass
    page.locator('textarea[name="objective"]').fill(
        "Capacitar iniciantes a escrever consultas SQL básicas (SELECT, WHERE, JOIN) e entender modelagem relacional."
    )
    page.wait_for_timeout(800)
    tw.snap(page, PASTA, "10-passo1-preenchido", full=True)
    dump(page, "PASSO 1 preenchido")

    # ----- percorrer passos 2..5 -----
    for passo in range(2, 7):
        prox = page.get_by_role("button", name=re.compile(r"^(Próximo|Avançar|Continuar)$", re.I)).first
        gerar = page.get_by_role("button", name=re.compile(r"Gerar curso|Gerar|Criar curso|Concluir", re.I))
        gerar_vis = [i for i in range(gerar.count()) if gerar.nth(i).is_visible() and gerar.nth(i).is_enabled()]
        if gerar_vis:
            print(f"\n[passo {passo}] BOTÃO DE DISPARO disponível: {gerar.nth(gerar_vis[0]).inner_text()!r} — PARANDO (não gero no recon)")
            tw.snap(page, PASTA, f"1{passo}-antes-do-disparo", full=True)
            dump(page, f"TELA FINAL (passo {passo})")
            break
        if not (prox.count() and prox.is_visible() and prox.is_enabled()):
            print(f"\n[passo {passo}] 'Próximo' indisponível — pode faltar campo obrigatório")
            tw.snap(page, PASTA, f"1{passo}-bloqueado", full=True)
            dump(page, f"PASSO {passo} (bloqueado)")
            break
        prox.click(timeout=8000)
        page.wait_for_timeout(4000)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, f"1{passo}-passo{passo}", full=True)
        dump(page, f"PASSO {passo}")

    print(f"\n[recon] url final: {page.url}")
    ctx.close(); browser.close()
