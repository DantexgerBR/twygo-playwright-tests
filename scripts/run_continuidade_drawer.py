# -*- coding: utf-8 -*-
"""19983 (cor do select Estratégia = #222834) e 19851 (selects Função/Iniciativa
populam) no drawer Adicionar de /o/37048/succession_actions. Admin. Headless.
19851 é específico do papel Líder — admin só dá baseline."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_continuidade_sucessao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)
URL = base + f"/o/{c['org_id']}/succession_actions"

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(URL, wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        tw.snap(pg, PASTA, "01-lista-acoes")
        # abrir drawer Adicionar
        pg.get_by_role("button", name=re.compile(r"Adicionar", re.I)).first.click(timeout=6000)
        pg.wait_for_timeout(3000)
        tw.snap(pg, PASTA, "02-drawer", full=True)
        # 19983: cor dos textos dos selects no drawer (foco no de Estratégia)
        cores = pg.evaluate(r"""()=>{
          const labels=['Função vinculada','Estratégia','Iniciativa','Respons','Situação'];
          const out=[];
          for(const lb of labels){
            const lab=[...document.querySelectorAll('label,div,span,p')].find(e=>new RegExp(lb,'i').test((e.innerText||'').trim().slice(0,40)));
            if(!lab) continue;
            // o controle do select perto do label
            const cont=lab.closest('div')?.parentElement||lab.parentElement;
            const ctrl=cont&&(cont.querySelector('[class*=select__control],[class*=control],[role=combobox],select,[class*=placeholder],[class*=singleValue]'));
            const el=ctrl||cont;
            if(el){const cs=getComputedStyle(el.querySelector('[class*=placeholder],[class*=singleValue],[class*=__input]')||el);out.push({campo:lb,color:cs.color});}
          }
          return out;}""")
        log("[19983] cores dos selects:", cores)
        # opções de Função vinculada e Iniciativa (19851 — baseline admin)
        def opts_do_select(label):
            return pg.evaluate(r"""(lb)=>{
              const lab=[...document.querySelectorAll('label,div,span,p')].find(e=>new RegExp('^'+lb,'i').test((e.innerText||'').trim()));
              if(!lab) return 'sem-label';
              const cont=lab.closest('div')?.parentElement||lab.parentElement;
              const ctrl=cont&&cont.querySelector('[class*=select__control],[role=combobox],select');
              if(!ctrl) return 'sem-control';
              ctrl.click(); return 'aberto';
            }""", label)
        # abrir Função vinculada e contar opções
        log("[19851] abrir Função vinculada:", opts_do_select("Função vinculada"))
        pg.wait_for_timeout(1200)
        nopt = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=option],[role=option],li')].filter(e=>e.offsetParent!==null && (e.innerText||'').trim()).length""")
        funcs = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=option],[role=option]')].map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,8)""")
        log(f"[19851] Função vinculada: {nopt} opções visíveis | amostra={funcs}")
        tw.snap(pg, PASTA, "03-funcao-vinculada", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:]);
        try: tw.snap(pg, PASTA, "99-erro", full=True)
        except Exception: pass
    finally:
        ctx.close(); b.close()
