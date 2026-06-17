# -*- coding: utf-8 -*-
"""20108 build passo 4 — cria ciclo completo com selecao de modelo ROBUSTA (retry +
verificacao). Identificacao + Avaliacoes(Desempenho+modelo) + Etapas(Auto-avaliacao+
Resultado) -> Salvar e programar."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
NOME = "QA20108 Avaliacao Teste"
log = lambda *a: print(*a, flush=True)

def click_tab(pg, nome):
    for _ in range(4):
        loc = pg.get_by_role("tab", name=re.compile(nome, re.I))
        if loc.count():
            try: loc.first.click(timeout=2500, force=True); pg.wait_for_timeout(1000); return True
            except Exception: pass
        pg.wait_for_timeout(700)
    return False

def click_txt(pg, alvo, xmin=260):
    box = pg.evaluate(r"""(a)=>{const[al,xm]=a;const els=[...document.querySelectorAll('label,span,p,div,button')]
      .filter(e=>{const t=(e.innerText||'').replace(/\s+/g,' ').trim();return t===al})
      .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=xm});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();
      return{x:r.left+10,y:r.top+r.height/2}}""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(500); return True

def modelo_selecionado(pg):
    return pg.evaluate(r"""()=>/QA20108 Modelo Desempenho/.test(document.body.innerText) && !!document.querySelector('[class*=select__single-value],[class*=select__control]') && document.body.innerText.includes('QA20108 Modelo Desempenho')""")

def selecionar_modelo(pg):
    for tentativa in range(3):
        # garante Desempenho marcado
        st = pg.evaluate(r"""()=>{const card=[...document.querySelectorAll('*')].find(e=>/Avaliação de Desempenho/.test(e.innerText||'')&&e.querySelector&&e.querySelector('input[type=checkbox]')&&e.getBoundingClientRect().height<140&&e.getBoundingClientRect().height>40);if(!card)return null;const cb=card.querySelector('input[type=checkbox]');const r=card.getBoundingClientRect();return{checked:cb.checked,x:r.left+30,y:r.top+30};}""")
        if st and not st["checked"]: pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(900)
        # abre o drawer: clica o "Selecionar modelo" por texto (mouse) ou coordenada fixa
        box = pg.evaluate(r"""()=>{const e=[...document.querySelectorAll('*')].find(x=>(x.innerText||'').trim()==='Selecionar modelo'&&x.getBoundingClientRect().left>260&&x.children.length<=2);
          if(e){const r=e.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};}return null;}""")
        if box: pg.mouse.click(box["x"], box["y"])
        else: pg.mouse.click(548, 402)
        pg.wait_for_timeout(1500)
        try:
            pg.get_by_placeholder(re.compile("Buscar modelo", re.I)).first.wait_for(timeout=4000)
            pg.get_by_placeholder(re.compile("Buscar modelo", re.I)).first.fill("QA20108"); pg.wait_for_timeout(1500)
        except Exception:
            log(f"  tentativa {tentativa}: drawer nao abriu"); continue
        res = pg.get_by_text(re.compile("QA20108 Modelo Desempenho", re.I))
        if res.count():
            res.first.click(timeout=4000, force=True); pg.wait_for_timeout(1200)
            if modelo_selecionado(pg): log(f"  modelo OK (tentativa {tentativa})"); return True
        log(f"  tentativa {tentativa}: res={res.count()} sel={modelo_selecionado(pg)}")
    return False

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:42])) if r.request.method in ("POST","PUT") and "/api/" in r.url and "cycle" in r.url.lower() else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.locator("input[name=name]").fill(NOME); pg.locator("input[name=planned_start_date]").fill("2026-06-17"); pg.locator("input[name=planned_end_date]").fill("2026-09-15")
        click_tab(pg, "Avalia")
        log("selecionar_modelo:", selecionar_modelo(pg))
        tw.snap(pg, PASTA, "step4-01-modelo", full=True)
        click_tab(pg, "Etapas")
        click_txt(pg, "Auto-avaliação"); click_txt(pg, "Cálculo automático ponderado")
        net.clear()
        pg.get_by_role("button", name=re.compile("Salvar e programar", re.I)).first.click(timeout=4000); pg.wait_for_timeout(4000)
        toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,4)""")
        log("net:", net[-4:]); log("toast:", [*dict.fromkeys(toast)]); log("url:", pg.url[-50:])
        ok = any(s in (200,201) for _,s,_ in net) or ("/cycles" in pg.url and "/new" not in pg.url)
        log("CICLO CRIADO:", ok)
        tw.snap(pg, PASTA, "step4-02-salvo", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "step4-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
