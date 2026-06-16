# -*- coding: utf-8 -*-
"""19988 v5 — mira o editor PlateJS 'Informações adicionais' (por posição Y, abaixo
do label) e testa digitação DIRETA. 37048. PR #10713."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19988_info_adicionais"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)
TESTE = "teste19988direto"

# acha o contenteditable logo ABAIXO do label "Informações adicionais"
JS_FIND = r"""()=>{
  const labs=[...document.querySelectorAll('label,p,span,div,h3,h4')].filter(e=>/^Informa[çc][õo]es adicionais/i.test((e.innerText||'').trim()));
  if(!labs.length) return null;
  const ly=Math.max(...labs.map(l=>l.getBoundingClientRect().top));
  const ces=[...document.querySelectorAll('[contenteditable=true],[role=textbox]')]
    .map(e=>({e,top:e.getBoundingClientRect().top})).filter(x=>x.top>ly).sort((a,b)=>a.top-b.top);
  return ces.length?ces[0].e:null;}"""

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base + f"/o/{c['org_id']}/roles", wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.get_by_role("button", name=re.compile(r"Adicionar", re.I)).first.click(timeout=6000); pg.wait_for_timeout(2000)
        pg.locator("#name").fill("QA19988 Funcao Teste")
        pg.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=6000); pg.wait_for_timeout(3500); tw.dispensar_nps(pg)
        pg.evaluate(r"""()=>{const e=[...document.querySelectorAll('button,a,[role=tab],div,span')].filter(x=>(x.innerText||'').trim()==='Competências'&&x.offsetParent!==null&&x.getBoundingClientRect().top<320);if(e[0])e[0].click();}""")
        pg.wait_for_timeout(2500)
        gi = pg.get_by_role("button", name=re.compile(r"Gerar com IA", re.I))
        if gi.count(): gi.nth(gi.count()-1).click(timeout=6000)
        pg.wait_for_timeout(3000); tw.dispensar_nps(pg)
        # mirar o editor de Informações adicionais e digitar direto (sem toolbar)
        ed = pg.evaluate_handle(JS_FIND)
        if not ed:
            log("=> 19988: sem campo Informações adicionais"); raise SystemExit
        # scroll + click no centro do editor + type
        pg.evaluate("(e)=>{e.scrollIntoView({block:'center'});}", ed)
        box = ed.bounding_box() if hasattr(ed,'bounding_box') else None
        try:
            box = ed.as_element().bounding_box()
        except Exception: box=None
        if box:
            pg.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
        else:
            ed.as_element().click()
        pg.wait_for_timeout(400)
        pg.keyboard.type(TESTE, delay=40); pg.wait_for_timeout(900)
        val = pg.evaluate("(e)=>e.innerText||e.textContent||''", ed)
        entrou = "teste19988" in (val or "").replace(" ","").lower()
        log(f"[campo info-adicionais] valor após digitar direto: {val!r} | entrou={entrou}")
        tw.snap(pg, PASTA, "v5-pos-digitar", full=True)
        log(f"\n=> 19988: {'PASSOU (digitação direta funciona)' if entrou else 'FALHOU (campo não aceitou digitação direta — bug persiste)'}")
    except SystemExit: pass
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "v5-99-erro", full=True)
        except Exception: pass
    finally:
        ctx.close(); b.close()
