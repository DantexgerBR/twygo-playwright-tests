# -*- coding: utf-8 -*-
"""19948 v2 — fix: marcar os CARDS de 'Quem responde a avaliação' (checkbox, não
os radios de método). Cria ciclo Programado c/ 9-box e abre Sessões de calibração."""
import re, sys, datetime, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
net500, calib = [], []
def on_resp(r):
    try:
        u = r.url
        if re.search(r"calibrat|calibra", u, re.I): calib.append((r.status, u))
        if r.status >= 500: net500.append((r.status, u))
    except Exception: pass
hoje = datetime.date(2026, 6, 16); fim = hoje + datetime.timedelta(days=90)
log = lambda *a: print(*a, flush=True)

def aba(page, nome):
    ok = page.evaluate("""(n)=>{const e=[...document.querySelectorAll('[role=tab],button,a,div')]
      .find(x=>new RegExp('^'+n,'i').test((x.innerText||'').trim()));if(e){e.click();return true}return false}""", nome)
    page.wait_for_timeout(1500); return ok

def marca_checkbox_card(page, titulo):
    """marca o CARD (input[type=checkbox]) cujo texto começa com 'titulo'."""
    return page.evaluate("""(t)=>{
      const all=[...document.querySelectorAll('label,div,button')];
      const card=all.find(e=>{const tx=(e.innerText||'').trim();
        return tx.startsWith(t) && tx.length<90 && e.querySelector('input[type=checkbox]');});
      if(!card) return 'nao';
      const cb=card.querySelector('input[type=checkbox]');
      if(cb&&cb.checked) return 'ja';
      (card.querySelector('.chakra-checkbox__control')||card.querySelector('input[type=checkbox]')||card).click();
      return 'ok';}""", titulo)

def marca_radio(page, regex):
    return page.evaluate("""(re)=>{
      const labs=[...document.querySelectorAll('label,div,button')].filter(e=>e.querySelector('input[type=radio]'));
      const l=labs.find(x=>new RegExp(re,'i').test((x.innerText||'').replace(/\\s+/g,' ')));
      if(!l) return 'nao';
      const rb=l.querySelector('input[type=radio]');
      if(rb&&rb.checked) return 'ja';
      (l.querySelector('.chakra-radio__control')||rb||l).click();
      return 'ok';}""", regex)

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True)
    page.on("response", on_resp)
    tw.login(page, c)
    cyc=None; programado=False
    try:
        page.goto(base + f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page); page.wait_for_timeout(3000)
        page.get_by_role("button", name=re.compile(r"Novo ciclo", re.I)).first.click(timeout=6000); page.wait_for_timeout(2500)
        # Identificação
        aba(page, "Identificação")
        page.locator('input[name="name"]').first.fill("QA19948 Ciclo Calibracao")
        page.locator('input[name="planned_start_date"]').first.fill(hoje.isoformat())
        page.locator('input[name="planned_end_date"]').first.fill(fim.isoformat())
        # Avaliações: PDI
        aba(page, "Avaliações"); page.wait_for_timeout(800)
        log("[aval] PDI:", marca_checkbox_card(page, "PDI"))
        tw.snap(page, PASTA, "v2-02-aval", full=True)
        # Etapas: marcar cards de coleta + método consenso+RH
        aba(page, "Etapas"); page.wait_for_timeout(1000)
        log("[etapas] Auto-avaliação:", marca_checkbox_card(page, "Auto-avaliação"))
        log("[etapas] Avaliação do líder:", marca_checkbox_card(page, "Avaliação do líder"))
        page.wait_for_timeout(800)
        mr = marca_radio(page, r"Reuni.o de consenso.*RH")
        if mr == "nao": mr = marca_radio(page, r"consenso.*\+\s*RH")
        log("[etapas] método consenso+RH:", mr)
        page.wait_for_timeout(1000)
        tw.snap(page, PASTA, "v2-03-etapas", full=True)
        # Config: 9-box
        aba(page, "Configura"); page.wait_for_timeout(800)
        log("[config] 9-box:", marca_checkbox_card(page, "Incluir etapa de calibração 9-box"))
        # Salvar e programar
        b = page.get_by_role("button", name=re.compile(r"Salvar e programar", re.I)).first
        log("[salvar] botão enabled?", b.is_enabled() if b.count() else "nao-achou")
        if b.count(): b.click(timeout=6000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
        corpo = page.evaluate("()=>document.body.innerText")
        toast = re.search(r"Preencha os campos obrigat[óo]rios:[^\n]+|sucesso|criado|programad", corpo, re.I)
        log("[salvar] toast/feedback:", toast.group(0) if toast else "—")
        tw.snap(page, PASTA, "v2-05-pos-salvar", full=True)
        m = re.search(r"/cycles/(\d+)", page.url); cyc = m.group(1) if m else None

        # lista + kebab Gerenciar campanhas
        page.goto(base + f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page); page.wait_for_timeout(3000)
        body = page.evaluate("()=>document.body.innerText")
        programado = ("QA19948" in body)
        kebs = page.get_by_text("more_vert", exact=True)
        log(f"[lista] QA19948 presente? {programado} | kebabs={kebs.count()}")
        tw.snap(page, PASTA, "v2-06-lista", full=True)
        if kebs.count():
            page.evaluate("""()=>{const rows=[...document.querySelectorAll('tr,[class*=row],li,div')].filter(r=>/QA19948/.test(r.innerText||''));
              for(const r of rows){const k=[...r.querySelectorAll('*')].find(e=>(e.innerText||'').trim()==='more_vert');if(k){k.click();return}}
              const a=[...document.querySelectorAll('*')].find(e=>(e.innerText||'').trim()==='more_vert');if(a)a.click();}""")
            page.wait_for_timeout(1500); tw.snap(page, PASTA, "v2-07-kebab")
            gc = page.get_by_text(re.compile(r"Gerenciar campanh|Ver campanh", re.I)).first
            log("[kebab] Gerenciar campanhas achou:", gc.count())
            if gc.count():
                gc.click(timeout=6000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
                log("[campanhas] url:", page.url); tw.snap(page, PASTA, "v2-08-campanhas", full=True)
                ab = page.get_by_text(re.compile(r"Sess[õo]es de calibra", re.I)).first
                log("[aba calibracao] achou:", ab.count())
                if ab.count():
                    ab.click(timeout=6000); page.wait_for_timeout(6000); tw.dispensar_nps(page)
                    tw.snap(page, PASTA, "v2-09-sessoes-calibracao", full=True)
                    corpo2 = page.evaluate("()=>document.body.innerText")
                    erro_tela = bool(re.search(r"erro interno|500|algo deu errado|tente novamente|n[ãa]o foi poss[íi]vel", corpo2, re.I))
                    log("[calibracao] tela de erro visível?", erro_tela)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-700:])
        try: tw.snap(page, PASTA, "v2-erro", full=True)
        except Exception: pass
    finally:
        log("\n== calib calls =="); [log(f"  {s} {u}") for s,u in calib[-12:]]
        log("== 500s =="); [log(f"  {s} {u}") for s,u in net500[-12:]]
        teve500 = any("calibra" in u.lower() and s>=500 for s,u in net500) or any(s>=500 for s,_ in calib)
        log(f"\n=> 19948 v2: ciclo={cyc} | QA19948_na_lista={programado} | calib_calls={len(calib)} | 500_calib={teve500}")
        ctx.close(); browser.close()
