# -*- coding: utf-8 -*-
"""19948 — cria ciclo com calibração 9-box no 37048 e abre a aba 'Sessões de
calibração' (via Gerenciar campanhas), capturando 500 em performance_calibration_sessions.
Headless. PR não informado — foco: a aba abre sem 500 (comportamento esperado)."""
import re, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
quinhentos = []   # 500s
calib_calls = []  # chamadas de calibração (qualquer status)

def listen(r):
    try:
        u = r.url
        if "calibration" in u.lower() or "calibra" in u.lower():
            calib_calls.append((r.status, u))
        if r.status >= 500:
            quinhentos.append((r.status, u))
    except Exception: pass

hoje = datetime.date(2026, 6, 16)
fim = hoje + datetime.timedelta(days=60)

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True)
    page.on("response", listen)
    tw.login(page, c)
    try:
        page.goto(base + f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page); page.wait_for_timeout(3000)
        page.get_by_role("button", name=re.compile(r"Novo ciclo", re.I)).first.click(timeout=6000)
        page.wait_for_timeout(2500)

        # --- Identificação ---
        page.locator('input[name="name"]').first.fill("QA19948 Ciclo Calibracao")
        try:
            page.locator('input[name="planned_start_date"]').first.fill(hoje.isoformat())
            page.locator('input[name="planned_end_date"]').first.fill(fim.isoformat())
        except Exception as e: print("[datas]", e)
        tw.snap(page, PASTA, "val-01-identificacao", full=True)

        def avancar():
            for nm in ("Próximo", "Avançar", "Continuar"):
                b = page.get_by_role("button", name=re.compile(rf"^{nm}$", re.I)).first
                if b.count() and b.is_enabled():
                    b.click(timeout=5000); page.wait_for_timeout(2000); return True
            return False

        # clicar nas abas/etapas do wizard pra chegar em Etapas (calibração)
        for etapa in ("Avaliações", "Etapas"):
            try:
                t = page.get_by_text(re.compile(rf"^{etapa}$", re.I)).first
                if t.count(): t.click(timeout=4000); page.wait_for_timeout(2000)
            except Exception: pass
            avancar()
        tw.snap(page, PASTA, "val-02-etapas", full=True)

        # habilitar calibração 9-box: radio "Reunião de consenso (líder + RH)" ou checkbox
        try:
            r = page.get_by_text(re.compile(r"Reunião de consenso \(líder \+ RH\)", re.I)).first
            if r.count(): r.click(timeout=4000); page.wait_for_timeout(1500)
        except Exception as e: print("[radio RH]", e)
        try:
            cb = page.get_by_text(re.compile(r"Incluir etapa de calibração 9-box", re.I)).first
            if cb.count(): cb.click(timeout=4000); page.wait_for_timeout(1000)
        except Exception as e: print("[cb 9box]", e)
        tw.snap(page, PASTA, "val-03-calibracao-on", full=True)

        # salvar como rascunho
        salvo = False
        for nm in (r"Salvar e programar", r"Salvar como rascunho", r"Salvar"):
            b = page.get_by_role("button", name=re.compile(nm, re.I)).first
            if b.count() and b.is_enabled():
                b.click(timeout=6000); page.wait_for_timeout(4000); salvo = True
                print(f"[salvar] cliquei '{nm}'"); break
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, "val-04-pos-salvar", full=True)
        m = re.search(r"/cycles/(\d+)", page.url); cyc = m.group(1) if m else None
        print(f"[ciclo] salvo={salvo} cycle_id={cyc} url={page.url}")

        # --- ir pra lista, abrir kebab do ciclo -> Gerenciar campanhas ---
        page.goto(base + f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page); page.wait_for_timeout(3000)
        kb = page.get_by_text("more_vert", exact=True)
        print(f"[lista] kebabs={kb.count()}")
        if kb.count():
            kb.first.click(force=True); page.wait_for_timeout(1200)
            tw.snap(page, PASTA, "val-05-kebab")
            gc = page.get_by_role("menuitem", name=re.compile(r"Gerenciar campanh", re.I)).first
            if not gc.count(): gc = page.get_by_text(re.compile(r"Gerenciar campanh", re.I)).first
            if gc.count():
                gc.click(timeout=6000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
                print("[gerenciar] url:", page.url)
                tw.snap(page, PASTA, "val-06-gerenciar-campanhas", full=True)
                # abrir aba Sessões de calibração
                ab = page.get_by_text(re.compile(r"Sess[õo]es de calibra", re.I)).first
                print("[aba calibracao] achou?", ab.count())
                if ab.count():
                    ab.click(timeout=6000); page.wait_for_timeout(6000); tw.dispensar_nps(page)
                    tw.snap(page, PASTA, "val-07-sessoes-calibracao", full=True)
        # veredito
        print("\n== chamadas de calibração ==")
        for s, u in calib_calls[-15:]: print(f"  {s} {u}")
        print("== 500s ==")
        for s, u in quinhentos[-15:]: print(f"  {s} {u}")
        teve_500_calib = any(s >= 500 and ("calibra" in u.lower()) for s, u in quinhentos)
        abriu = any(("calibra" in u.lower() and s < 400) for s, u in calib_calls)
        print(f"\n=> 19948: 500 em calibração? {teve_500_calib} | chamadas calib ok? {abriu}")
    except Exception as e:
        print("ERRO:", e); tw.snap(page, PASTA, "val-erro", full=True)
    finally:
        ctx.close(); browser.close()
