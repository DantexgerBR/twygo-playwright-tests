# -*- coding: utf-8 -*-
"""20033 — valida consistência "Aplicar e Salvar" do filtro (PR #10712), 37048/Parâmetros.
Monta filtro (valor + oculta 2 colunas) -> salva na lista -> Aplica (estado A) ->
recarrega (limpa) -> reabre drawer -> Meus filtros -> reaplica salvo (estado B).
Compara ordem/visibilidade de colunas + nº de linhas. Iguais => consistente (fix OK)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20033_filtro"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
NOME_FILTRO = "qa20033flow"
log = lambda *a: print(*a, flush=True)

def click_txt_drawer(pg, alvo, xmin=950):
    box = pg.evaluate(r"""(arg)=>{const [alvo,xmin]=arg;
      const els=[...document.querySelectorAll('a,button,div,span,p,h2,h3,h4,label')]
        .filter(e=>{const t=(e.innerText||'').trim();return t===alvo||t==='+ '+alvo||t==='+'+alvo;})
        .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=xmin;});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();
      return {x:r.left+r.width/2,y:r.top+r.height/2};}""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(400); return True

def set_coluna(pg, label, want_checked):
    """marca/desmarca checkbox de 'Colunas para exibir' pelo texto do label."""
    st = pg.evaluate(r"""(label)=>{
      const labs=[...document.querySelectorAll('label')].filter(e=>{const r=e.getBoundingClientRect();
        return r.left>950 && (e.innerText||'').trim()===label;});
      if(!labs.length) return {found:false};
      const l=labs[0]; l.scrollIntoView({block:'center'});
      const cb=l.querySelector('input[type=checkbox]')||l.previousElementSibling?.querySelector?.('input[type=checkbox]');
      const checked = cb? cb.checked : (l.getAttribute('data-checked')!==null);
      const r=l.getBoundingClientRect();
      return {found:true, checked, x:r.left+18, y:r.top+r.height/2};}""", label)
    if not st.get("found"): log(f"   [coluna '{label}' NAO achada]"); return
    if st["checked"] != want_checked:
        pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(300)
        log(f"   coluna '{label}': {st['checked']}->{want_checked}")
    else:
        log(f"   coluna '{label}': ja {want_checked}")

def estado_tabela(pg):
    return pg.evaluate(r"""()=>{
      const ths=[...document.querySelectorAll('thead th,[role=columnheader]')]
        .filter(e=>{const r=e.getBoundingClientRect();return r.left<950&&r.width>0;})
        .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean);
      const rows=document.querySelectorAll('tbody tr').length;
      return {cols:ths, rows};}""")

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        url = base+f"/o/{c['org_id']}/succession_initiatives"
        pg.goto(url, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        base_st = estado_tabela(pg); log("DEFAULT:", base_st)

        # --- montar filtro ---
        pg.get_by_role("button", name=re.compile(r"Filtro", re.I)).first.click(timeout=5000); pg.wait_for_timeout(1200)
        click_txt_drawer(pg, "Novo"); pg.wait_for_timeout(1800)
        # valor Iniciativa
        pg.mouse.click(1220, 228); pg.wait_for_timeout(1000)
        if not click_txt_drawer(pg, "Capacitar sucessor"):
            log("   [valor 'Capacitar sucessor' nao clicado via drawer]")
        pg.wait_for_timeout(800)
        # colunas: ocultar Impacto e Cobertura
        click_txt_drawer(pg, "Colunas para exibir"); pg.wait_for_timeout(500)
        set_coluna(pg, "Impacto (%)", False)
        set_coluna(pg, "Cobertura (%)", False)
        # salvar na lista
        click_txt_drawer(pg, "Salvar filtro"); pg.wait_for_timeout(500)
        # ligar toggle "Salvar na lista de filtros"
        click_txt_drawer(pg, "Salvar na lista de filtros"); pg.wait_for_timeout(400)
        # nome
        nm = pg.locator("input[type=text]").filter(visible=True).last
        nm.fill(NOME_FILTRO, timeout=4000); pg.wait_for_timeout(400)
        tw.snap(pg, PASTA, "flow-01-builder-pronto", full=True)
        # aplicar
        click_txt_drawer(pg, "Aplicar"); pg.wait_for_timeout(2500)
        estado_A = estado_tabela(pg); log("ESTADO A (1a aplicacao):", estado_A)
        tw.snap(pg, PASTA, "flow-02-aplicado-A", full=True)

        # --- limpar (reload) ---
        pg.goto(url, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        limpo = estado_tabela(pg); log("APOS RELOAD (limpo):", limpo)

        # --- reaplicar salvo via Meus filtros ---
        pg.get_by_role("button", name=re.compile(r"Filtro", re.I)).first.click(timeout=5000); pg.wait_for_timeout(1200)
        click_txt_drawer(pg, "Meus filtros"); pg.wait_for_timeout(800)
        click_txt_drawer(pg, NOME_FILTRO); pg.wait_for_timeout(800)
        tw.snap(pg, PASTA, "flow-03-meus-filtros", full=True)
        click_txt_drawer(pg, "Aplicar"); pg.wait_for_timeout(2500)
        estado_B = estado_tabela(pg); log("ESTADO B (reaplicado):", estado_B)
        tw.snap(pg, PASTA, "flow-04-reaplicado-B", full=True)

        # --- veredito ---
        log("\n=== COMPARACAO ===")
        log("A.cols:", estado_A["cols"]); log("B.cols:", estado_B["cols"])
        log("A.rows:", estado_A["rows"], "B.rows:", estado_B["rows"])
        consistente = estado_A["cols"] == estado_B["cols"] and estado_A["rows"] == estado_B["rows"]
        log("CONSISTENTE (A==B):", consistente)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-500:])
        try: tw.snap(pg, PASTA, "flow-ERRO", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
