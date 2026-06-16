# -*- coding: utf-8 -*-
"""20033 reapply — reaplica o filtro salvo 'qa20033flow' (Meus filtros) e verifica
se restaura colunas (Impacto/Cobertura ocultas) + valor (Capacitar sucessor=1 linha).
Dumpa o conteudo do drawer a cada passo p/ garantir que NAO e falso positivo."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20033_filtro"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
NOME = "qa20033flow"
log = lambda *a: print(*a, flush=True)

def drawer_txt(pg):
    return pg.evaluate(r"""()=>[...document.querySelectorAll('*')]
      .filter(e=>{const r=e.getBoundingClientRect();return r.left>980&&r.width>0&&r.height>0&&e.children.length===0;})
      .map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<40)
      .filter((t,i,a)=>a.indexOf(t)===i)""")

def click_txt(pg, alvo, xmin=980):
    box = pg.evaluate(r"""(arg)=>{const [alvo,xmin]=arg;
      const els=[...document.querySelectorAll('a,button,div,span,p,h2,h3,h4,label')]
        .filter(e=>{const t=(e.innerText||'').trim();return t===alvo;})
        .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=xmin;});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();
      return {x:r.left+r.width/2,y:r.top+r.height/2};}""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(600); return True

def estado(pg):
    return pg.evaluate(r"""()=>{const ths=[...document.querySelectorAll('thead th,[role=columnheader]')]
      .filter(e=>{const r=e.getBoundingClientRect();return r.left<950&&r.width>0;})
      .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean);
      return {cols:ths, rows:document.querySelectorAll('tbody tr').length};}""")

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        url = base+f"/o/{c['org_id']}/succession_initiatives"
        pg.goto(url, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        # garante baseline limpo: se filtro ativo, recarrega ja foi feito. Mostra estado atual.
        log("ESTADO inicial:", estado(pg))
        pg.get_by_role("button", name=re.compile(r"Filtro", re.I)).first.click(timeout=5000); pg.wait_for_timeout(1500)
        tw.dispensar_nps(pg)
        log("drawer apos abrir:", drawer_txt(pg))
        # expandir Meus filtros
        click_txt(pg, "Meus filtros"); pg.wait_for_timeout(1000)
        log("drawer apos 'Meus filtros':", drawer_txt(pg))
        tw.snap(pg, PASTA, "re-01-meus-filtros-exp", full=True)
        # clicar no filtro salvo
        ok = click_txt(pg, NOME); log("clicou no filtro salvo:", ok); pg.wait_for_timeout(1000)
        log("drawer apos selecionar filtro:", drawer_txt(pg))
        tw.snap(pg, PASTA, "re-02-selecionado", full=True)
        # aplicar
        click_txt(pg, "Aplicar"); pg.wait_for_timeout(2500)
        st = estado(pg); log("ESTADO reaplicado:", st)
        tw.snap(pg, PASTA, "re-03-reaplicado", full=True)
        log("\nEsperado p/ fix OK: cols SEM 'Impacto (%)' e SEM 'Cobertura (%)', rows=1 (Capacitar sucessor)")
        impacto = any("Impacto" in x for x in st["cols"])
        log(f"Impacto visivel={impacto} | rows={st['rows']} (1=valor restaurado, 15=valor perdido)")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-500:])
        try: tw.snap(pg, PASTA, "re-ERRO", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
