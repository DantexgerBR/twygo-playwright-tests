# -*- coding: utf-8 -*-
"""19948 — cria ciclo Programado c/ calibração 9-box no 37048 e abre 'Sessões de
calibração' (Gerenciar campanhas), capturando o 500. Resiliente: cada erro tem
workaround, não para. Headless."""
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
    """clica a aba do wizard pelo texto (resiliente)"""
    try:
        t = page.get_by_role("tab", name=re.compile(nome, re.I)).first
        if t.count(): t.click(timeout=4000); page.wait_for_timeout(1500); return True
    except Exception: pass
    ok = page.evaluate("""(n)=>{const e=[...document.querySelectorAll('[role=tab],button,a,div')]
      .find(x=>new RegExp('^'+n,'i').test((x.innerText||'').trim()));if(e){e.click();return true}return false}""", nome)
    page.wait_for_timeout(1500); return ok

def marcar(page, texto):
    """marca checkbox/radio Chakra clicando no label que contém o texto"""
    return page.evaluate("""(t)=>{
      const labs=[...document.querySelectorAll('label')];
      const l=labs.find(x=>new RegExp(t,'i').test(x.innerText||''));
      if(l){const inp=l.querySelector('input'); if(inp&&inp.checked) return 'ja';
            (l.querySelector('.chakra-checkbox__control,.chakra-radio__control')||l).click(); return 'ok';}
      return 'nao-achou';}""", texto)

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True)
    page.on("response", on_resp)
    tw.login(page, c)
    cyc = None; programado = False
    try:
        page.goto(base + f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page); page.wait_for_timeout(3000)
        page.get_by_role("button", name=re.compile(r"Novo ciclo", re.I)).first.click(timeout=6000)
        page.wait_for_timeout(2500)

        # ---- ABA IDENTIFICAÇÃO ----
        aba(page, "Identificação")
        try: page.locator('input[name="name"]').first.fill("QA19948 Ciclo Calibracao")
        except Exception as e: log("[ident nome]", e)
        for sel, val in (('input[name="planned_start_date"]', hoje.isoformat()),
                         ('input[name="planned_end_date"]', fim.isoformat())):
            try: page.locator(sel).first.fill(val)
            except Exception as e: log("[data]", sel, e)
        tw.snap(page, PASTA, "run-01-ident", full=True)

        # ---- ABA AVALIAÇÕES (marcar tipo; workaround p/ modelo obrigatório) ----
        aba(page, "Avaliações")
        page.wait_for_timeout(1000)
        marcado = None
        # tentar tipos do mais leve ao mais pesado
        for tipo in ("PDI", "Compet", "Desempenho"):
            r = marcar(page, tipo)
            log(f"[aval] marcar {tipo}: {r}")
            if r in ("ok", "ja"):
                marcado = tipo; page.wait_for_timeout(1500)
                # se exigiu modelo (FormularioPicker), tentar selecionar 1; se vazio, desmarca e tenta outro
                corpo = page.evaluate("()=>document.body.innerText")
                if re.search(r"Selecione um modelo|modelo de formul", corpo, re.I):
                    log(f"[aval] {tipo} exige modelo — tentando selecionar")
                    sel = False
                    try:
                        pick = page.get_by_text(re.compile(r"Selecion.*modelo|Escolher modelo|modelo de formul", re.I)).first
                        if pick.count(): pick.click(timeout=3000); page.wait_for_timeout(1200)
                        opt = page.locator("[role=option], li, .chakra-menu__menuitem").first
                        if opt.count(): opt.click(timeout=3000); sel = True; page.wait_for_timeout(1000)
                    except Exception as e: log("[modelo pick]", e)
                    if not sel:
                        log(f"[aval] sem modelo p/ {tipo} — desmarcando e tentando próximo")
                        marcar(page, tipo)  # toggle off
                        marcado = None; continue
                break
        log(f"[aval] tipo final marcado: {marcado}")
        tw.snap(page, PASTA, "run-02-avaliacoes", full=True)

        # ---- ABA ETAPAS (coleta + método consenso+RH = ativa 9-box) ----
        aba(page, "Etapas")
        page.wait_for_timeout(1000)
        for coleta in ("Autoavalia", "Auto", "Líder", "Lider"):
            r = marcar(page, coleta)
            if r == "ok": log(f"[etapas] coleta {coleta}: {r}")
        # método finalização: Reunião de consenso (líder + RH)
        rm = marcar(page, r"Reunião de consenso \(líder \+ RH\)")
        if rm == "nao-achou": rm = marcar(page, "consenso.*RH")
        log(f"[etapas] método consenso+RH: {rm}")
        tw.snap(page, PASTA, "run-03-etapas", full=True)

        # ---- ABA CONFIGURAÇÕES ADICIONAIS (garantir 9-box) ----
        aba(page, "Configura")
        page.wait_for_timeout(1000)
        cb = marcar(page, "calibração 9-box|9-box|calibra")
        log(f"[config] 9-box: {cb}")
        tw.snap(page, PASTA, "run-04-config", full=True)

        # ---- SALVAR E PROGRAMAR (workaround: se travar, completar + tentar rascunho) ----
        def salvar(label_re):
            b = page.get_by_role("button", name=re.compile(label_re, re.I)).first
            if b.count() and b.is_enabled():
                b.click(timeout=6000); page.wait_for_timeout(4000); tw.dispensar_nps(page); return True
            return False
        salvar(r"Salvar e programar")
        page.wait_for_timeout(2000)
        corpo = page.evaluate("()=>document.body.innerText")
        falta = re.search(r"Preencha os campos obrigat[óo]rios:[^\n]+", corpo, re.I)
        if falta:
            log("[salvar] bloqueio:", falta.group(0))
            tw.snap(page, PASTA, "run-05-bloqueio", full=True)
            # workaround: revisitar abas pendentes (! amarelo) e re-tentar
            for ab in ("Avaliações", "Etapas"):
                aba(page, ab); page.wait_for_timeout(800)
            salvar(r"Salvar e programar"); page.wait_for_timeout(2000)
        m = re.search(r"/cycles/(\d+)", page.url); cyc = m.group(1) if m else None
        # confirmar status na lista
        page.goto(base + f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page); page.wait_for_timeout(3000)
        tw.snap(page, PASTA, "run-06-lista", full=True)
        body = page.evaluate("()=>document.body.innerText")
        programado = bool(re.search(r"Programad|Em andamento", body, re.I)) and "QA19948" in body
        kebs = page.get_by_text("more_vert", exact=True)
        log(f"[lista] ciclo QA19948 presente? {'QA19948' in body} | programado/andamento? {programado} | kebabs={kebs.count()}")

        # ---- GERENCIAR CAMPANHAS -> SESSÕES DE CALIBRAÇÃO ----
        if kebs.count():
            # achar o kebab do nosso ciclo (linha que contém QA19948)
            clicou_kb = page.evaluate("""()=>{
              const rows=[...document.querySelectorAll('tr,[class*=row],li,div')].filter(r=>/QA19948/.test(r.innerText||''));
              for(const r of rows){const k=[...r.querySelectorAll('*')].find(e=>(e.innerText||'').trim()==='more_vert');
                if(k){k.click();return true}}
              const any=[...document.querySelectorAll('*')].find(e=>(e.innerText||'').trim()==='more_vert');
              if(any){any.click();return true} return false}""")
            page.wait_for_timeout(1500)
            tw.snap(page, PASTA, "run-07-kebab")
            gc = page.get_by_text(re.compile(r"Gerenciar campanh|Ver campanh", re.I)).first
            log(f"[kebab] clicou={clicou_kb} | gerenciar campanhas achou={gc.count()}")
            if gc.count():
                gc.click(timeout=6000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
                log("[campanhas] url:", page.url)
                tw.snap(page, PASTA, "run-08-campanhas", full=True)
                ab = page.get_by_text(re.compile(r"Sess[õo]es de calibra", re.I)).first
                log(f"[aba calibracao] achou={ab.count()}")
                if ab.count():
                    ab.click(timeout=6000); page.wait_for_timeout(6000); tw.dispensar_nps(page)
                    tw.snap(page, PASTA, "run-09-sessoes-calibracao", full=True)
                    corpo2 = page.evaluate("()=>document.body.innerText")
                    tela_erro = bool(re.search(r"erro|500|algo deu errado|tente novamente", corpo2, re.I))
                    log(f"[calibracao] tela de erro visível? {tela_erro}")
    except Exception as e:
        log("ERRO GERAL:", e); log(traceback.format_exc()[-800:])
        try: tw.snap(page, PASTA, "run-erro", full=True)
        except Exception: pass
    finally:
        log("\n== chamadas de calibração ==")
        for s, u in calib[-15:]: log(f"  {s} {u}")
        log("== 500s ==")
        for s, u in net500[-15:]: log(f"  {s} {u}")
        teve_500 = any(s >= 500 for s, _ in calib) or any("calibra" in u.lower() for s, u in net500 if s>=500)
        houve_calib = len(calib) > 0
        log(f"\n=> RESUMO 19948: ciclo={cyc} programado={programado} | chamadas_calib={houve_calib} | 500_calib={teve_500}")
        ctx.close(); browser.close()
