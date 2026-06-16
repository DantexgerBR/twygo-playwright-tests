# -*- coding: utf-8 -*-
"""19948 — ciclo 139 (QA19948, Programado) já existe. Abre kebab -> campanhas ->
aba 'Sessões de calibração' e captura o 500. Headless."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
net500, calib = [], []
def on_resp(r):
    try:
        u=r.url
        if re.search(r"calibrat|calibra", u, re.I): calib.append((r.status,u))
        if r.status>=500: net500.append((r.status,u))
    except Exception: pass
log = lambda *a: print(*a, flush=True)
JS_MENU_VIS = ("()=>{const ms=[...document.querySelectorAll('[role=menu]')].filter(m=>{const s=getComputedStyle(m);"
               "return s.visibility==='visible'&&parseFloat(s.opacity)>0.5;});const m=ms[ms.length-1];"
               "return m?[...m.querySelectorAll('[role=menuitem],button,a,li')].map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(Boolean):[];}")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True)
    page.on("response", on_resp)
    tw.login(page, c)
    try:
        page.goto(base + f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page); page.wait_for_timeout(3500)
        # status do ciclo na lista
        linha = page.evaluate("""()=>{const r=[...document.querySelectorAll('tr,[class*=row],li,div')]
          .find(e=>/QA19948/.test(e.innerText||'') && (e.innerText||'').length<200);return r?(r.innerText||'').replace(/\\s+/g,' ').trim():null;}""")
        log("[lista] linha QA19948:", linha)
        # abrir kebab da linha QA19948
        page.evaluate("""()=>{const rows=[...document.querySelectorAll('tr,[class*=row],li')].filter(r=>/QA19948/.test(r.innerText||''));
          for(const r of rows){const k=[...r.querySelectorAll('*')].find(e=>(e.innerText||'').trim()==='more_vert');if(k){k.click();return}}}""")
        page.wait_for_timeout(1500)
        itens = page.evaluate(JS_MENU_VIS)
        log("[kebab] itens visíveis:", itens)
        tw.snap(page, PASTA, "ct-01-kebab")
        # clicar item de campanhas (visível)
        clicou = page.evaluate("""()=>{const ms=[...document.querySelectorAll('[role=menu]')].filter(m=>{const s=getComputedStyle(m);return s.visibility==='visible'&&parseFloat(s.opacity)>0.5;});
          const m=ms[ms.length-1];if(!m)return 'sem-menu';
          const it=[...m.querySelectorAll('[role=menuitem],button,a,li')].find(e=>/campanh/i.test(e.innerText||''));
          if(it){it.click();return it.innerText.trim();}return 'sem-item-campanha';}""")
        log("[kebab] cliquei:", clicou)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        log("[campanhas] url:", page.url)
        tw.snap(page, PASTA, "ct-02-campanhas", full=True)
        # abrir aba Sessões de calibração
        ab_txt = page.evaluate("""()=>[...document.querySelectorAll('[role=tab],button,a,div')]
          .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>/calibra/i.test(t)).slice(0,6)""")
        log("[campanhas] elementos c/ 'calibra':", ab_txt)
        ab = page.get_by_text(re.compile(r"Sess[õo]es de calibra", re.I))
        # clicar a aba visível
        clicou_ab = False
        for i in range(ab.count()):
            try:
                if ab.nth(i).is_visible():
                    ab.nth(i).click(timeout=5000); clicou_ab = True; break
            except Exception: pass
        if not clicou_ab:
            clicou_ab = page.evaluate("""()=>{const e=[...document.querySelectorAll('[role=tab],button,a,div,span')]
              .find(x=>/Sess[õo]es de calibra/i.test((x.innerText||'')) && x.offsetParent!==null);if(e){e.click();return true}return false}""")
        log("[aba calibracao] clicou?", clicou_ab)
        page.wait_for_timeout(6000); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "ct-03-sessoes-calibracao", full=True)
        corpo = page.evaluate("()=>document.body.innerText")
        erro_tela = bool(re.search(r"erro interno|erro 500|algo deu errado|tente novamente|n[ãa]o foi poss[íi]vel|Internal Server", corpo, re.I))
        log("[calibracao] tela de erro visível?", erro_tela)
        log("[calibracao] trecho corpo:", corpo[:200].replace("\n"," | "))
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-600:])
        try: tw.snap(page, PASTA, "ct-erro", full=True)
        except Exception: pass
    finally:
        log("\n== calib calls =="); [log(f"  {s} {u}") for s,u in calib[-15:]]
        log("== 500s (todos) =="); [log(f"  {s} {u}") for s,u in net500[-15:]]
        c500 = any("calibra" in u.lower() and s>=500 for s,u in net500) or any(s>=500 for s,_ in calib)
        log(f"\n=> 19948: calib_calls={len(calib)} | 500_em_calibracao={c500}")
        ctx.close(); browser.close()
