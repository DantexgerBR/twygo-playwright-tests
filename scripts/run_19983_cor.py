# -*- coding: utf-8 -*-
"""19983 — cor exata dos textos do select 'Estratégia' no drawer Adicionar ação.
Esperado #222834 (rgb 34,40,52); bug era #858585 (rgb 133,133,133). 37048."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_continuidade_sucessao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

def hexc(rgb):
    m = re.findall(r"\d+", rgb or "")
    return "#%02X%02X%02X" % tuple(int(x) for x in m[:3]) if len(m) >= 3 else rgb

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base + f"/o/{c['org_id']}/succession_actions", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.get_by_role("button", name=re.compile(r"Adicionar", re.I)).first.click(timeout=6000); pg.wait_for_timeout(3000)
        # medir cor dos textos do controle de Estratégia (singleValue 'Evitar' + placeholder)
        cores = pg.evaluate(r"""()=>{
          const lab=[...document.querySelectorAll('label,p,span,div')].find(e=>/Estrat[ée]gia de resposta/i.test((e.innerText||'').trim().slice(0,40)));
          if(!lab) return {err:'sem label Estratégia'};
          // sobe até o container do form-group e pega o controle react-select logo abaixo
          let cont=lab.parentElement, ctrl=null;
          for(let k=0;k<4&&cont;k++){ctrl=cont.querySelector('[class*=-control],[class*=__control],[role=combobox]'); if(ctrl)break; cont=cont.parentElement;}
          if(!ctrl) return {err:'sem control'};
          const texts=[...ctrl.querySelectorAll('[class*=singleValue],[class*=single-value],[class*=placeholder],div,span')]
            .filter(e=>(e.innerText||'').trim()).slice(0,4)
            .map(e=>({txt:(e.innerText||'').trim().slice(0,20),color:getComputedStyle(e).color}));
          return {texts};}""")
        log("[19983] Estratégia control textos:", cores)
        if isinstance(cores, dict) and cores.get("texts"):
            for t in cores["texts"]:
                log(f"   '{t['txt']}' -> {t['color']} = {hexc(t['color'])}")
        # abrir o dropdown e medir as opções (Evitar/Mitigar/Transferir/Aceitar)
        try:
            pg.evaluate(r"""()=>{const lab=[...document.querySelectorAll('label,p,span,div')].find(e=>/Estrat[ée]gia de resposta/i.test((e.innerText||'').trim().slice(0,40)));
              let cont=lab.parentElement,ctrl=null;for(let k=0;k<4&&cont;k++){ctrl=cont.querySelector('[class*=-control],[class*=__control]');if(ctrl)break;cont=cont.parentElement;}if(ctrl)ctrl.click();}""")
            pg.wait_for_timeout(1000)
            opts = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=option]')].filter(e=>/Evitar|Mitigar|Transferir|Aceitar/.test(e.innerText||''))
              .map(e=>({txt:(e.innerText||'').trim(),color:getComputedStyle(e).color})).slice(0,6)""")
            log("[19983] opções do dropdown:")
            for o in opts: log(f"   '{o['txt']}' -> {o['color']} = {hexc(o['color'])}")
        except Exception as e: log("[dropdown]", e)
        tw.snap(pg, PASTA, "19983-cor", full=True)
    except Exception as e:
        log("ERRO:", e)
        try: tw.snap(pg, PASTA, "19983-erro", full=True)
        except Exception: pass
    finally:
        ctx.close(); b.close()
