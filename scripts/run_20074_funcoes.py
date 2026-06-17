# -*- coding: utf-8 -*-
"""20074 (correto) — tooltip com NOME COMPLETO ao hoverar nomes de funcao/area nas
tabelas 'Funcoes com maior risco' / 'Areas com maior risco' do Dashboard geral 19653.
Os nomes truncam; o fix mostra o nome completo em tooltip no hover."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20074_20096"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

NOMES = ["Líder de Equipe de Migração de Banco de Dados", "Gestor de Projetos de Migração de Dados",
         "Especialista em Governança de Dados", "rr", "QA", "Liderança"]

def portais(pg):
    return pg.evaluate(r"""()=>{const sel='[role=tooltip],[class*=tooltip i],[class*=Tooltip],.chakra-tooltip,[data-popper-placement],[id*=popover],[class*=popover i]';
      return [...document.querySelectorAll(sel)].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()).map(e=>(e.innerText||'').trim()).slice(0,4);}""")

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_dashboards", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(4000)
        achou = []
        for nome in NOMES:
            loc = pg.get_by_text(nome, exact=True).filter(visible=True)
            if not loc.count(): log(f"'{nome[:30]}' nao visivel"); continue
            try:
                loc.first.scroll_into_view_if_needed(timeout=3000); loc.first.hover(timeout=3000); pg.wait_for_timeout(1500)
                tip = portais(pg)
                # tambem checa title attr nativo
                titulo = loc.first.evaluate("e=>e.getAttribute('title')||e.closest('[title]')?.getAttribute('title')||e.parentElement?.getAttribute('title')||''")
                log(f"hover '{nome[:34]}' -> tooltip={tip} title_attr='{titulo}'")
                if tip or titulo: achou.append((nome, tip or titulo)); tw.snap(pg, PASTA, "tt-"+re.sub(r'\W+','_',nome.lower())[:18], full=True)
            except Exception as ex:
                log(f"hover '{nome[:20]}' erro: {str(ex)[:60]}")
        log(f"\n>> 20074 tooltips encontrados: {achou}")
        log(f">> 20074 VEREDITO: {'PASSOU (tooltip presente)' if achou else 'FALHOU (sem tooltip)'}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
