# -*- coding: utf-8 -*-
"""20108 build passo 1 — cria ciclo novo (Identificacao) + habilita 'Avaliacao de
Desempenho' (passo Avaliacoes) + seleciona modelo -> Salvar como rascunho. Verifica."""
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
        for loc in (pg.get_by_role("tab", name=re.compile(nome, re.I)), pg.get_by_text(nome, exact=True)):
            if loc.count():
                try: loc.first.click(timeout=2500, force=True); pg.wait_for_timeout(1200); return True
                except Exception: pass
        pg.wait_for_timeout(800)
    return False

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:45])) if r.request.method in ("POST","PUT","PATCH") and "/api/" in r.url and "cycle" in r.url.lower() else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        # Identificacao
        pg.locator("input[name=name]").fill(NOME, timeout=4000)
        pg.locator("input[name=planned_start_date]").fill("2026-06-17", timeout=4000)
        pg.locator("input[name=planned_end_date]").fill("2026-09-15", timeout=4000)
        pg.wait_for_timeout(500)
        log("identificacao preenchida")
        # Avaliacoes
        click_tab(pg, "Avalia")
        # marca Avaliacao de Desempenho (checkbox no card com esse texto)
        st = pg.evaluate(r"""()=>{const card=[...document.querySelectorAll('*')].find(e=>/Avaliação de Desempenho/.test(e.innerText||'')&&e.querySelector&&e.querySelector('input[type=checkbox]')&&e.getBoundingClientRect().height<140&&e.getBoundingClientRect().height>40);
          if(!card)return{found:false};const cb=card.querySelector('input[type=checkbox]');const r=cb.getBoundingClientRect();const lr=card.getBoundingClientRect();
          return{found:true,checked:cb.checked,x:lr.left+30,y:lr.top+30};}""")
        log("checkbox Desempenho:", st)
        if st.get("found") and not st["checked"]:
            pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(1200)
        tw.snap(pg, PASTA, "b1-01-avaliacoes", full=True)
        # apos marcar, pode aparecer um select de modelo
        sel = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>260};
          const combos=[...document.querySelectorAll('select,[class*=select__control],[role=combobox]')].filter(vis).map(e=>(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,40));
          const labels=[...document.querySelectorAll('label,p')].filter(vis).map(e=>(e.innerText||'').trim()).filter(t=>/modelo|selec/i.test(t)).slice(0,5);
          return {combos:[...new Set(combos)].slice(0,6), labels};}""")
        log("modelo combos:", sel["combos"], "| labels:", sel["labels"])
        # salvar rascunho
        sr = pg.get_by_role("button", name=re.compile("Salvar como rascunho|Salvar rascunho", re.I))
        if sr.count(): sr.first.click(timeout=4000); pg.wait_for_timeout(3000); log("clicou salvar rascunho")
        log("url:", pg.url[-45:], "| net:", net[-4:])
        tw.snap(pg, PASTA, "b1-02-pos-salvar", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "b1-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
