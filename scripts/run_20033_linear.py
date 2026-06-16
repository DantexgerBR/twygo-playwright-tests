# -*- coding: utf-8 -*-
"""20033 LINEAR (definitivo) — valor Capacitar sucessor + oculta Impacto, salva na
lista, Aplica (A), Limpa, reabre (com retry), reaplica salvo (B). click_txt(mouse)
em tudo + toggle JS. Compara A vs B. Chat escondido."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20033_filtro"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
NOME = "qa20033lin"
log = lambda *a: print(*a, flush=True)
HIDE = r"""()=>{document.querySelectorAll('iframe,[class*=intercom],[id*=intercom],[class*=launcher],[class*=octadesk],[class*=chat-widget]').forEach(e=>{try{e.style.display='none'}catch(_){}})}"""

def hide(pg):
    try: pg.evaluate(HIDE)
    except: pass

def click_txt(pg, alvo, xmin=950, plus=False):
    box = pg.evaluate(r"""(a)=>{const[al,xm,plus]=a;const els=[...document.querySelectorAll('a,button,div,span,p,h2,h3,h4,label')]
      .filter(e=>{const t=(e.innerText||'').trim();return t===al||(plus&&(t==='+ '+al||t==='+'+al))})
      .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=xm});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();
      return{x:r.left+r.width/2,y:r.top+r.height/2}}""", [alvo, xmin, plus])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(500); return True

def set_coluna(pg, label, want):
    st = pg.evaluate(r"""(label)=>{const labs=[...document.querySelectorAll('label')].filter(e=>{const r=e.getBoundingClientRect();
      return r.left>950&&(e.innerText||'').trim()===label});if(!labs.length)return{found:false};
      const l=labs[0];l.scrollIntoView({block:'center'});const cb=l.querySelector('input[type=checkbox]');
      const r=l.getBoundingClientRect();return{found:true,checked:cb?cb.checked:false,x:r.left+18,y:r.top+r.height/2}}""", label)
    if not st.get("found"): log(f"   coluna '{label}' NAO achada"); return
    if st["checked"] != want: pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(400); log(f"   '{label}' {st['checked']}->{want}")

def toggle_salvar_lista(pg):
    st = pg.evaluate(r"""()=>{const txts=[...document.querySelectorAll('*')].filter(e=>e.children.length<=2&&(e.innerText||'').trim()==='Salvar na lista de filtros'&&e.getBoundingClientRect().left>950);
      if(!txts.length)return{found:false};let row=txts[0];for(let i=0;i<4&&row;i++){const sw=row.querySelector('[role=switch],input[type=checkbox],.chakra-switch');if(sw){const cb=sw.matches('input')?sw:sw.querySelector('input');const checked=cb?cb.checked:(sw.getAttribute('aria-checked')==='true'||sw.getAttribute('data-checked')!==null);const r=(sw.querySelector('.chakra-switch__track')||sw).getBoundingClientRect();return{found:true,checked,x:r.left+r.width/2,y:r.top+r.height/2}}row=row.parentElement}return{found:false}}""")
    if not st.get("found"): log("   switch NAO achado"); return None
    if not st["checked"]: pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(500)
    return True

def estado(pg):
    return pg.evaluate(r"""()=>{const ths=[...document.querySelectorAll('thead th,[role=columnheader]')]
      .filter(e=>{const r=e.getBoundingClientRect();return r.left<950&&r.width>0}).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean);
      return{cols:ths,rows:document.querySelectorAll('tbody tr').length}}""")

def abrir_filtro(pg):
    for _ in range(4):
        try:
            btn = pg.get_by_role("button", name=re.compile(r"^Filtro$", re.I))
            if btn.count(): btn.first.click(timeout=4000)
            elif not click_txt(pg, "Filtro"): pg.wait_for_timeout(1000); continue
            pg.get_by_text(re.compile("Lista de filtros")).first.wait_for(timeout=5000); hide(pg); pg.wait_for_timeout(600); return True
        except Exception: pg.wait_for_timeout(1200)
    return False

def limpar(pg):
    lf = pg.get_by_role("button", name=re.compile("Limpar filtro", re.I))
    if lf.count(): lf.first.click(); pg.wait_for_timeout(1800)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        url = base+f"/o/{c['org_id']}/succession_initiatives"
        pg.goto(url, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500); hide(pg)
        limpar(pg); log("DEFAULT:", estado(pg))

        assert abrir_filtro(pg), "nao abriu Filtro (build)"
        click_txt(pg, "Novo", plus=True); pg.wait_for_timeout(1800); hide(pg)
        pg.mouse.click(1220, 228); pg.wait_for_timeout(900)
        click_txt(pg, "Capacitar sucessor"); pg.wait_for_timeout(700)
        click_txt(pg, "Colunas para exibir"); pg.wait_for_timeout(600)
        set_coluna(pg, "Impacto (%)", False)
        click_txt(pg, "Salvar filtro"); pg.wait_for_timeout(600)
        toggle_salvar_lista(pg)
        pg.locator("input[type=text]").filter(visible=True).last.fill(NOME, timeout=4000); pg.wait_for_timeout(400)
        tw.snap(pg, PASTA, "lin-01-builder", full=True)
        click_txt(pg, "Aplicar"); pg.wait_for_timeout(2800)
        A = estado(pg); log("ESTADO A:", A); tw.snap(pg, PASTA, "lin-02-A", full=True)

        limpar(pg); hide(pg); log("apos limpar:", estado(pg))

        assert abrir_filtro(pg), "nao reabriu Filtro (reapply)"
        click_txt(pg, "Meus filtros"); pg.wait_for_timeout(1200)
        d = pg.locator(".chakra-modal__content,[role=dialog]").last
        txt = d.inner_text(); presente = NOME in txt
        log("Meus filtros seg:", txt[txt.find("Meus filtros"):].replace("\n"," | ")[:160])
        log("SALVO PRESENTE:", presente); tw.snap(pg, PASTA, "lin-03-meusfiltros", full=True)
        if presente:
            click_txt(pg, NOME); pg.wait_for_timeout(1000)
            click_txt(pg, "Aplicar"); pg.wait_for_timeout(2800)
            B = estado(pg); log("ESTADO B:", B); tw.snap(pg, PASTA, "lin-04-B", full=True)
            log("\nA.cols:", A["cols"], "rows", A["rows"])
            log("B.cols:", B["cols"], "rows", B["rows"])
            log("CONSISTENTE:", A["cols"] == B["cols"] and A["rows"] == B["rows"])
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "lin-ERRO", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
