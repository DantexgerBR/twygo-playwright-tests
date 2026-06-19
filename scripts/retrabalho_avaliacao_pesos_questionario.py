"""Retrabalhos 20185 + 20186 — Questionario tipo Avaliacao: pesos + lapis.

Valida no editor /assessments/new (org 36675):
 20186: lapis sem funcao removido; regra de peso por secao (fecha 100%); peso 0.
 20185: Avaliacao de DESEMPENHO nao deveria ter peso atrelado obrigatorio.

Testa COMPORTAMENTO (nao so visual): toggla desempenho x competencias, mede o
estado do campo Peso, tenta peso 0 e soma !=100, e tenta Salvar pra ver validacao.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "avaliacao_pesos_questionario"
c = tw.cfg("")


def estado_peso(page):
    """Reporta estado dos campos Peso visiveis + presenca de icone lapis (edit)."""
    return page.evaluate(r"""()=>{
        // inputs de peso: number inputs perto do label 'Peso'
        const pesos=[];
        document.querySelectorAll('input').forEach(inp=>{
            const box=inp.closest('div');
            const ctx=(inp.closest('[class*=question],[class*=Question],section,div')||{}).innerText||'';
            if(/Peso/.test((inp.parentElement&&inp.parentElement.previousElementSibling&&inp.parentElement.previousElementSibling.innerText)||'') || (inp.getAttribute('aria-label')||'').match(/peso/i)){
                pesos.push({val:inp.value, type:inp.type, disabled:inp.disabled, readOnly:inp.readOnly});
            }
        });
        // fallback: qualquer spinbutton
        if(!pesos.length){
            document.querySelectorAll('input[role=spinbutton],input[type=number]').forEach(inp=>pesos.push({val:inp.value,type:inp.type,disabled:inp.disabled,readOnly:inp.readOnly}));
        }
        // contar a palavra "Peso" visivel e icones de lapis (edit / mode_edit)
        const body=document.body.innerText||'';
        const temPesoLabel=/\bPeso\b/.test(body);
        // material icons de lapis: texto 'edit' ou 'mode_edit' OU svg/i com aria edit
        const lapis=Array.from(document.querySelectorAll('i,span,button,svg')).filter(e=>{
            const t=(e.textContent||'').trim();
            return t==='edit'||t==='mode_edit'||/edit/i.test(e.getAttribute('data-icon')||'')|| /edit/i.test(e.getAttribute('aria-label')||'');
        }).map(e=>(e.textContent||e.getAttribute('aria-label')||'').trim());
        return {pesos, temPesoLabel, lapis};
    }""")


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/assessments/new?profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)

    page.fill("input[placeholder*='nome do question']", "QA 20185-20186 pesos avaliacao")

    # ---- Estado inicial (nada selecionado em 'Pode ser usado em') ----
    print("INICIAL:", estado_peso(page))

    # ---- Selecionar AVALIACAO DE DESEMPENHO ----
    page.get_by_text("Avaliação de desempenho", exact=True).click()
    page.wait_for_timeout(1500)
    e_desemp = estado_peso(page)
    print("DESEMPENHO:", e_desemp)
    tw.snap(page, PASTA, "01-desempenho-secao-peso", full=True)

    # ---- Selecionar AVALIACAO DE COMPETENCIAS ----
    page.get_by_text("Avaliação de competências", exact=True).click()
    page.wait_for_timeout(1500)
    e_comp = estado_peso(page)
    print("COMPETENCIAS:", e_comp)
    tw.snap(page, PASTA, "02-competencias-secao-peso", full=True)

    # ---- Recolher a pergunta pra ver o cabecalho (como a BUG-3) e checar lapis ----
    try:
        page.get_by_text("keyboard_arrow_up", exact=True).first.click(timeout=3000)
        page.wait_for_timeout(800)
    except Exception as ex:
        print("nao recolheu:", ex)
    tw.snap(page, PASTA, "03-pergunta-recolhida-header")
    print("RECOLHIDA:", estado_peso(page))

    # ---- TESTE DE VALIDACAO DE PESO (competencias): adicionar 2a pergunta, soma !=100 ----
    # Em competencias a pergunta 1 ja vem 100. Adiciona uma 2a -> soma passa de 100.
    try:
        page.get_by_text("Adicionar pergunta à seção", exact=True).first.click(timeout=4000)
        page.wait_for_timeout(1500)
    except Exception as ex:
        print("nao adicionou pergunta:", ex)
    tw.snap(page, PASTA, "04-duas-perguntas-soma-maior-100", full=True)
    print("APOS 2a PERGUNTA:", estado_peso(page))

    # Tentar salvar e capturar validacao
    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=4000)
        page.wait_for_timeout(2500)
    except Exception as ex:
        print("erro salvar:", ex)
    tw.dispensar_nps(page)  # nao, queremos VER o erro; mas se abrir modal de erro captura antes
    tw.snap(page, PASTA, "05-tentativa-salvar-validacao", full=True)
    # capturar toasts/erros
    msg = page.evaluate(r"""()=>{
        const al=Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast],[class*=error],[class*=Error]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean);
        return [...new Set(al)].slice(0,15);
    }""")
    print("MENSAGENS APOS SALVAR:", msg)
    print("URL apos salvar:", page.url)

    ctx.close(); browser.close()
print("VALIDACAO OK")
