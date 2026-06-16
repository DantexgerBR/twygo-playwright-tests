# -*- coding: utf-8 -*-
"""20033 cols — versao deterministica: filtro SO de visibilidade de colunas (sem
combobox de valor, que e flaky). Oculta Impacto/Cobertura, salva na lista, Aplica
(estado A), limpa, confirma em Meus filtros, reaplica (estado B). Compara colunas.
Tudo via locators escopados ao dialog chakra + force; chat escondido."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20033_filtro"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
NOME = "qa20033cols"
log = lambda *a: print(*a, flush=True)
HIDE = r"""()=>{document.querySelectorAll('iframe,[class*=intercom],[id*=intercom],[class*=launcher],[class*=octadesk],[class*=chat-widget]').forEach(e=>{try{e.style.display='none'}catch(_){}})}"""

def estado(pg):
    return pg.evaluate(r"""()=>{const ths=[...document.querySelectorAll('thead th,[role=columnheader]')]
      .filter(e=>{const r=e.getBoundingClientRect();return r.left<950&&r.width>0}).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean);
      return{cols:ths,rows:document.querySelectorAll('tbody tr').length}}""")
def drawer(pg): return pg.locator(".chakra-modal__content,[role=dialog]").last

def click_txt(pg, alvo, xmin=950):
    box = pg.evaluate(r"""(a)=>{const[al,xm]=a;const els=[...document.querySelectorAll('a,button,div,span,p,h2,h3,h4,label')]
      .filter(e=>{const t=(e.innerText||'').trim();return t===al})
      .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=xm});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();
      return{x:r.left+r.width/2,y:r.top+r.height/2}}""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(400); return True

def toggle_salvar_lista(pg):
    st = pg.evaluate(r"""()=>{const txts=[...document.querySelectorAll('*')].filter(e=>e.children.length<=2&&(e.innerText||'').trim()==='Salvar na lista de filtros'&&e.getBoundingClientRect().left>950);
      if(!txts.length)return{found:false};let row=txts[0];for(let i=0;i<4&&row;i++){const sw=row.querySelector('[role=switch],input[type=checkbox],.chakra-switch');if(sw){const cb=sw.matches('input')?sw:sw.querySelector('input');const checked=cb?cb.checked:(sw.getAttribute('aria-checked')==='true'||sw.getAttribute('data-checked')!==null);const r=(sw.querySelector('.chakra-switch__track')||sw).getBoundingClientRect();return{found:true,checked,x:r.left+r.width/2,y:r.top+r.height/2}}row=row.parentElement}return{found:false}}""")
    if not st.get("found"): log("   switch 'Salvar na lista' NAO achado"); return None
    if not st["checked"]: pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(500)
    chk = pg.evaluate(r"""()=>{const txts=[...document.querySelectorAll('*')].filter(e=>e.children.length<=2&&(e.innerText||'').trim()==='Salvar na lista de filtros'&&e.getBoundingClientRect().left>950);if(!txts.length)return null;let row=txts[0];for(let i=0;i<4&&row;i++){const sw=row.querySelector('[role=switch],input[type=checkbox],.chakra-switch');if(sw){const cb=sw.matches('input')?sw:sw.querySelector('input');return cb?cb.checked:(sw.getAttribute('aria-checked')==='true'||sw.getAttribute('data-checked')!==null)}row=row.parentElement}return null}""")
    log("   switch 'Salvar na lista' checked=", chk); return chk
def hide(pg):
    try: pg.evaluate(HIDE)
    except: pass

def abrir_filtro(pg):
    pg.get_by_role("button", name=re.compile(r"^Filtro$", re.I)).first.click(timeout=6000)
    pg.get_by_text(re.compile("Lista de filtros")).first.wait_for(timeout=6000); hide(pg); pg.wait_for_timeout(500)

def limpar(pg):
    lf = pg.get_by_role("button", name=re.compile("Limpar filtro", re.I))
    if lf.count(): lf.first.click(); pg.wait_for_timeout(1500)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        url = base+f"/o/{c['org_id']}/succession_initiatives"
        pg.goto(url, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500); hide(pg)
        limpar(pg); log("DEFAULT:", estado(pg))

        # montar filtro de colunas
        abrir_filtro(pg); d = drawer(pg)
        d.get_by_text(re.compile(r"^\+?\s*Novo$")).first.click(force=True); pg.wait_for_timeout(1500); hide(pg)
        d.get_by_text("Colunas para exibir", exact=True).first.click(force=True); pg.wait_for_timeout(800)
        for col in ("Impacto (%)",):
            cb = d.get_by_text(col, exact=True).locator("visible=true").first
            cb.click(force=True); pg.wait_for_timeout(500)
            log(f"   desmarcou {col}")
        # salvar na lista
        d.get_by_text("Salvar filtro", exact=True).first.click(force=True); pg.wait_for_timeout(700)
        toggle_salvar_lista(pg)
        nm = d.locator("input[type=text]").last; nm.fill(NOME, timeout=4000); pg.wait_for_timeout(300)
        tw.snap(pg, PASTA, "cols-01-builder", full=True)
        click_txt(pg, "Aplicar"); pg.wait_for_timeout(2500)
        A = estado(pg); log("ESTADO A:", A); tw.snap(pg, PASTA, "cols-02-A", full=True)

        # limpar
        limpar(pg); log("apos limpar:", estado(pg)); hide(pg)

        # reabrir, Meus filtros
        abrir_filtro(pg); d = drawer(pg)
        d.get_by_text("Meus filtros", exact=True).first.click(force=True); pg.wait_for_timeout(1200)
        txt = d.inner_text(); seg = txt[txt.find("Meus filtros"):].replace("\n"," | ")[:200]
        log("Meus filtros:", seg)
        presente = NOME in txt; log("SALVO PRESENTE:", presente)
        tw.snap(pg, PASTA, "cols-03-meusfiltros", full=True)

        if presente:
            d.get_by_text(NOME, exact=False).first.click(force=True); pg.wait_for_timeout(1000)
            click_txt(pg, "Aplicar"); pg.wait_for_timeout(2500)
            B = estado(pg); log("ESTADO B:", B); tw.snap(pg, PASTA, "cols-04-B", full=True)
            log("\nA.cols:", A["cols"]); log("B.cols:", B["cols"])
            log("COLUNAS CONSISTENTES (A==B):", A["cols"] == B["cols"])
        else:
            log(">> Filtro nao persistiu em Meus filtros (possivel bug de salvar OU automacao).")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-500:])
        try: tw.snap(pg, PASTA, "cols-ERRO", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
