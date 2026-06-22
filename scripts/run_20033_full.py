# -*- coding: utf-8 -*-
"""20033 FULL — fluxo confiavel: monta filtro (valor Capacitar sucessor + oculta
Impacto/Cobertura), liga 'Salvar na lista de filtros' (verifica switch ON), nomeia,
Aplica (estado A), reabre drawer, confirma que aparece em Meus filtros, seleciona e
Aplica de novo (estado B). Compara. Chat escondido, cliques drawer-scoped + force."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20033_filtro"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
NOME = "qa20033b"
log = lambda *a: print(*a, flush=True)
HIDE = r"""()=>{document.querySelectorAll('iframe,[class*=intercom],[id*=intercom],[class*=launcher],[class*=octadesk],[class*=chat-widget]').forEach(e=>{try{e.style.display='none'}catch(_){}})}"""

def click_txt(pg, alvo, xmin=950):
    box = pg.evaluate(r"""(a)=>{const[al,xm]=a;const els=[...document.querySelectorAll('a,button,div,span,p,h2,h3,h4,label')]
      .filter(e=>{const t=(e.innerText||'').trim();return t===al||t==='+ '+al||t==='+'+al})
      .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=xm});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();
      return{x:r.left+r.width/2,y:r.top+r.height/2}}""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(400); return True

def set_coluna(pg, label, want):
    st = pg.evaluate(r"""(label)=>{const labs=[...document.querySelectorAll('label')].filter(e=>{const r=e.getBoundingClientRect();
      return r.left>950&&(e.innerText||'').trim()===label});if(!labs.length)return{found:false};
      const l=labs[0];l.scrollIntoView({block:'center'});const cb=l.querySelector('input[type=checkbox]');
      const r=l.getBoundingClientRect();return{found:true,checked:cb?cb.checked:false,x:r.left+18,y:r.top+r.height/2}}""", label)
    if not st.get("found"): log(f"   coluna '{label}' NAO achada"); return
    if st["checked"] != want: pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(300); log(f"   coluna '{label}' {st['checked']}->{want}")

def toggle_salvar_lista(pg):
    """liga o switch 'Salvar na lista de filtros'. Retorna estado final (checked)."""
    st = pg.evaluate(r"""()=>{const txts=[...document.querySelectorAll('*')].filter(e=>e.children.length<=2&&(e.innerText||'').trim()==='Salvar na lista de filtros'&&e.getBoundingClientRect().left>950);
      if(!txts.length)return{found:false};let row=txts[0];for(let i=0;i<4&&row;i++){const sw=row.querySelector('[role=switch],input[type=checkbox],.chakra-switch');if(sw){const cb=sw.matches('input')?sw:sw.querySelector('input');const checked=cb?cb.checked:(sw.getAttribute('aria-checked')==='true'||sw.getAttribute('data-checked')!==null);const r=(sw.querySelector('.chakra-switch__track')||sw).getBoundingClientRect();return{found:true,checked,x:r.left+r.width/2,y:r.top+r.height/2}}row=row.parentElement}
      return{found:false}}""")
    if not st.get("found"): log("   switch 'Salvar na lista' NAO achado"); return None
    if not st["checked"]:
        pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(500)
    chk = pg.evaluate(r"""()=>{const txts=[...document.querySelectorAll('*')].filter(e=>e.children.length<=2&&(e.innerText||'').trim()==='Salvar na lista de filtros'&&e.getBoundingClientRect().left>950);if(!txts.length)return null;let row=txts[0];for(let i=0;i<4&&row;i++){const sw=row.querySelector('[role=switch],input[type=checkbox],.chakra-switch');if(sw){const cb=sw.matches('input')?sw:sw.querySelector('input');return cb?cb.checked:(sw.getAttribute('aria-checked')==='true'||sw.getAttribute('data-checked')!==null)}row=row.parentElement}return null}""")
    log("   switch 'Salvar na lista' checked=", chk); return chk

def estado(pg):
    return pg.evaluate(r"""()=>{const ths=[...document.querySelectorAll('thead th,[role=columnheader]')]
      .filter(e=>{const r=e.getBoundingClientRect();return r.left<950&&r.width>0}).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean);
      return{cols:ths,rows:document.querySelectorAll('tbody tr').length}}""")

def drawer(pg): return pg.locator(".chakra-modal__content,[role=dialog]").last

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        url = base+f"/o/{c['org_id']}/succession_initiatives"
        pg.goto(url, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500); pg.evaluate(HIDE)
        # limpa filtro ativo se houver
        lf = pg.get_by_role("button", name=re.compile("Limpar filtro", re.I))
        if lf.count(): lf.first.click(); pg.wait_for_timeout(1200)
        log("DEFAULT:", estado(pg))

        # montar
        pg.get_by_role("button", name=re.compile(r"^Filtro$", re.I)).first.click(timeout=5000)
        pg.get_by_text(re.compile("Lista de filtros")).first.wait_for(timeout=6000); pg.evaluate(HIDE)
        click_txt(pg, "Novo"); pg.wait_for_timeout(1800)
        pg.mouse.click(1220, 228); pg.wait_for_timeout(900)
        click_txt(pg, "Capacitar sucessor"); pg.wait_for_timeout(700)
        click_txt(pg, "Colunas para exibir"); pg.wait_for_timeout(500)
        set_coluna(pg, "Impacto (%)", False); set_coluna(pg, "Cobertura (%)", False)
        click_txt(pg, "Salvar filtro"); pg.wait_for_timeout(500)
        toggle_salvar_lista(pg)
        nm = pg.locator("input[type=text]").filter(visible=True).last; nm.fill(NOME, timeout=4000); pg.wait_for_timeout(300)
        tw.snap(pg, PASTA, "full-01-builder", full=True)
        click_txt(pg, "Aplicar"); pg.wait_for_timeout(2500)
        A = estado(pg); log("ESTADO A:", A); tw.snap(pg, PASTA, "full-02-A", full=True)

        # limpar
        lf = pg.get_by_role("button", name=re.compile("Limpar filtro", re.I))
        if lf.count(): lf.first.click(); pg.wait_for_timeout(1500)
        log("apos limpar:", estado(pg))

        # reabrir, conferir Meus filtros
        pg.get_by_role("button", name=re.compile(r"^Filtro$", re.I)).first.click(timeout=5000)
        pg.get_by_text(re.compile("Lista de filtros")).first.wait_for(timeout=6000); pg.evaluate(HIDE)
        d = drawer(pg)
        d.get_by_text("Meus filtros", exact=True).first.click(force=True); pg.wait_for_timeout(1200)
        txt = d.inner_text(); log("Meus filtros:", txt[txt.find("Meus filtros"):].replace("\n"," | ")[:200])
        tw.snap(pg, PASTA, "full-03-meusfiltros", full=True)
        salvo_presente = NOME in txt
        log("FILTRO SALVO PRESENTE EM MEUS FILTROS:", salvo_presente)

        if salvo_presente:
            d.get_by_text(NOME, exact=False).first.click(force=True); pg.wait_for_timeout(1000)
            d.get_by_role("button", name=re.compile("^Aplicar$", re.I)).first.click(force=True); pg.wait_for_timeout(2500)
            B = estado(pg); log("ESTADO B:", B); tw.snap(pg, PASTA, "full-04-B", full=True)
            log("\nA.cols:", A["cols"], "| A.rows:", A["rows"])
            log("B.cols:", B["cols"], "| B.rows:", B["rows"])
            log("CONSISTENTE:", A["cols"] == B["cols"] and A["rows"] == B["rows"])
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-500:])
        try: tw.snap(pg, PASTA, "full-ERRO", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
