# -*- coding: utf-8 -*-
"""20108 build — campanha completa no ciclo 166. Abre 'Vincular pessoas', busca uma
pessoa, seleciona, Vincular, Criar campanha."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
CID = "166"
log = lambda *a: print(*a, flush=True)

def click_tab(pg, nome):
    for _ in range(4):
        loc = pg.get_by_role("tab", name=re.compile(nome, re.I))
        if loc.count():
            try: loc.first.click(timeout=2500, force=True); pg.wait_for_timeout(900); return True
            except Exception: pass
        pg.wait_for_timeout(700)
    return False

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:45])) if r.request.method in ("POST","PUT") and "/api/" in r.url and "campaign" in r.url.lower() else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/{CID}/campaigns/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.locator("input[name=name]").fill("QA20108 Campanha")
        click_tab(pg, "Cronograma")
        for nm, val in [("start_date","2026-06-17"),("end_date","2026-09-15"),("self_start_date","2026-06-17"),("self_end_date","2026-09-15")]:
            f = pg.locator(f"input[name={nm}]")
            if f.count(): f.fill(val)
        click_tab(pg, "Quem participa"); pg.wait_for_timeout(800)
        pg.get_by_text("Definir participantes", exact=True).last.click(timeout=4000); pg.wait_for_timeout(1500)
        # drawer Vincular pessoas -> buscar
        srch = pg.get_by_placeholder(re.compile("Pesquise por nome ou e-mail", re.I))
        srch.first.wait_for(timeout=5000)
        pg.wait_for_timeout(4000)  # deixa carregar a lista inicial
        srch.first.fill("a"); pg.wait_for_timeout(6000)  # busca carrega devagar
        # lista de pessoas (checkboxes no drawer)
        pessoas = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]');if(!drw)return[];
          return [...drw.querySelectorAll('label,li,[class*=item],tr')].filter(e=>e.querySelector&&e.querySelector('input[type=checkbox]')&&(e.innerText||'').trim()).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).slice(0,8);}""")
        log("pessoas no drawer:", [*dict.fromkeys(pessoas)][:6])
        # marca o 1o checkbox de pessoa
        chk = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]');if(!drw)return null;
          const cbs=[...drw.querySelectorAll('input[type=checkbox]')].filter(e=>{const r=e.getBoundingClientRect();return r.top>340&&r.width>0;});
          if(!cbs.length)return null;const e=cbs[0];const lab=e.closest('label')||e.parentElement;const r=(lab||e).getBoundingClientRect();return{x:r.left+14,y:r.top+r.height/2};}""")
        if chk: pg.mouse.click(chk["x"], chk["y"]); pg.wait_for_timeout(800); log("marquei 1a pessoa")
        tw.snap(pg, PASTA, "camp3-pessoa", full=True)
        # Vincular
        vinc = pg.get_by_role("button", name=re.compile("^Vincular$", re.I))
        if vinc.count(): vinc.first.click(timeout=4000); pg.wait_for_timeout(1500); log("cliquei Vincular")
        tw.snap(pg, PASTA, "camp3-vinculado", full=True)
        # Criar campanha
        net.clear()
        cc = pg.get_by_role("button", name=re.compile("Criar campanha", re.I))
        if cc.count(): cc.first.click(timeout=4000); pg.wait_for_timeout(3500)
        toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,4)""")
        log("net:", net[-4:]); log("toast:", [*dict.fromkeys(toast)]); log("url:", pg.url[-45:])
        ok = any(s in (200,201) for _,s,_ in net)
        log("CAMPANHA CRIADA:", ok)
        tw.snap(pg, PASTA, "camp3-criada", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "camp3-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
