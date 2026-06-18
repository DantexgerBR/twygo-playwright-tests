"""Validação card 19423 [Widgets] - campo Descrição da aba Identificação de Painéis.

Dois comportamentos:
 1) Foco em QUALQUER ponto do campo (clicar área vazia abaixo da 1a linha foca o editor).
 2) Scrollbar condicional: só aparece quando o texto ultrapassa a altura do campo.
Validar em EDIÇÃO e em ADIÇÃO de painel.

Recurso: Configurações > Menu > aba "Painéis" > editar(lápis)/Adicionar > aba Identificação.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "paineis_descricao_19423"
EVID = tw.ROOT / "evidencias" / SLUG
c = tw.cfg("GOATWY")

# Seletor do editor de Descrição (Slate). É o contenteditable=true dentro do .slate-editor.
ED_SEL = ".slate-editor[contenteditable='true'], .slate-editor [contenteditable='true']"


def ir_aba_paineis(page):
    page.goto(f"{c['base_url']}/o/{c['org_id']}/use_modes", wait_until="domcontentloaded")
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    page.get_by_text("Painéis", exact=True).first.click()
    page.wait_for_timeout(3000); tw.dispensar_nps(page)


def localizar_editor(page):
    """Retorna o handle do contenteditable do campo Descrição (procura o que está sob o label 'Descrição')."""
    h = page.evaluate_handle(
        r"""()=>{
        // pega o editor slate cujo container fica logo após um label 'Descrição'
        const eds=Array.from(document.querySelectorAll(".slate-editor[contenteditable='true'], .slate-editor [contenteditable='true']"));
        if(eds.length===0) return null;
        // heurística: o editor de Descrição é o último visível (o de mensagem/recaptcha não é slate)
        return eds[eds.length-1];
    }"""
    )
    return h


def medir(page, ed_handle):
    """scrollHeight/clientHeight/overflow-y + activeElement."""
    return page.evaluate(
        r"""(ed)=>{
        const cs=getComputedStyle(ed);
        // o overflow real pode estar no wrapper rolável; busca o ancestral com overflow auto/scroll
        let scroller=ed; let cur=ed;
        for(let i=0;i<5 && cur;i++){const c=getComputedStyle(cur);if(/(auto|scroll)/.test(c.overflowY)){scroller=cur;break;}cur=cur.parentElement;}
        const sc=getComputedStyle(scroller);
        const active=document.activeElement;
        const focado = active===ed || ed.contains(active) || (active && active.closest && active.closest('.slate-editor'));
        return {
            scrollHeight: scroller.scrollHeight,
            clientHeight: scroller.clientHeight,
            temScroll: scroller.scrollHeight > scroller.clientHeight + 1,
            overflowY: sc.overflowY,
            edOverflowY: cs.overflowY,
            focado: !!focado,
            activeTag: active ? active.tagName + '.' + (active.className||'').slice(0,40) : 'none',
        };
    }""",
        ed_handle,
    )


def testar_campo(page, contexto):
    """Roda os 2 testes no campo Descrição já visível. Retorna dict de resultados."""
    res = {"contexto": contexto}
    ed = localizar_editor(page)
    if not ed.evaluate("e=>!!e"):
        res["erro"] = "editor de Descrição não encontrado"
        return res

    # limpar o campo (selecionar tudo e apagar) p/ estado "pouco/vazio"
    ed.evaluate("e=>e.focus()")
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.wait_for_timeout(400)
    # tira o foco do editor sem clicar em nada interativo (blur via JS)
    ed.evaluate("e=>e.blur()")
    page.evaluate("()=>{if(document.activeElement)document.activeElement.blur();}")
    page.wait_for_timeout(300)

    # --- TESTE 2a: scrollbar com campo vazio/pouco texto ---
    m_vazio = medir(page, ed)
    res["vazio_temScroll"] = m_vazio["temScroll"]
    res["vazio_overflowY"] = m_vazio["overflowY"]
    res["vazio_sh_ch"] = f"{m_vazio['scrollHeight']}/{m_vazio['clientHeight']}"

    # --- TESTE 1: foco clicando na parte BAIXA/VAZIA do campo ---
    box = ed.bounding_box()
    if box:
        # clica perto do rodapé do editor (área vazia abaixo da 1a linha)
        px = box["x"] + box["width"] * 0.5
        py = box["y"] + box["height"] - 12
        page.mouse.click(px, py)
        page.wait_for_timeout(500)
    m_foco = medir(page, ed)
    res["foco_apos_click_baixo"] = m_foco["focado"]
    res["foco_activeTag"] = m_foco["activeTag"]

    # --- TESTE 2b: scrollbar com MUITO texto ---
    ed.evaluate("e=>e.focus()")
    page.keyboard.type("Linha de teste de scroll. " )
    for _ in range(40):
        page.keyboard.type("Texto longo para forcar o estouro de altura do campo de descricao. ")
        page.keyboard.press("Enter")
    page.wait_for_timeout(600)
    m_cheio = medir(page, ed)
    res["cheio_temScroll"] = m_cheio["temScroll"]
    res["cheio_overflowY"] = m_cheio["overflowY"]
    res["cheio_sh_ch"] = f"{m_cheio['scrollHeight']}/{m_cheio['clientHeight']}"
    return res


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    EVID.mkdir(parents=True, exist_ok=True)

    print("\n########## CONTEXTO 1: EDIÇÃO ##########")
    ir_aba_paineis(page)
    page.locator("td", has_text="edit").first.locator("text=edit").first.click()
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print("URL edição:", page.url)
    r_edit = testar_campo(page, "EDICAO")
    tw.snap(page, EVID, "10_edicao_campo_cheio", full=True)
    print(r_edit)

    print("\n########## CONTEXTO 2: ADIÇÃO ##########")
    ir_aba_paineis(page)
    page.get_by_role("link", name="Adicionar").first.click()
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print("URL adição:", page.url)
    tw.snap(page, EVID, "20_adicao_aberta", full=True)
    r_add = testar_campo(page, "ADICAO")
    tw.snap(page, EVID, "21_adicao_campo_cheio", full=True)
    print(r_add)

    print("\n\n================ RESUMO ================")
    for r in (r_edit, r_add):
        print(f"\n[{r['contexto']}]")
        if r.get("erro"):
            print("  ERRO:", r["erro"]); continue
        print(f"  Foco ao clicar na area BAIXA/vazia: {'OK (focou)' if r['foco_apos_click_baixo'] else 'FALHOU (nao focou)'}  active={r['foco_activeTag']}")
        print(f"  Scroll com campo vazio:  temScroll={r['vazio_temScroll']}  overflowY={r['vazio_overflowY']}  sh/ch={r['vazio_sh_ch']}  -> {'OK (sem scroll)' if not r['vazio_temScroll'] else 'FALHOU (scroll indevido)'}")
        print(f"  Scroll com muito texto:  temScroll={r['cheio_temScroll']}  overflowY={r['cheio_overflowY']}  sh/ch={r['cheio_sh_ch']}  -> {'OK (scroll aparece)' if r['cheio_temScroll'] else 'verificar'}")

    ctx.close(); browser.close()
print("\nFIM validação 19423")
