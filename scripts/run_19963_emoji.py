# -*- coding: utf-8 -*-
"""19963 — emoji (4 bytes) em nome de seção de Avaliação: POST /assessments deve
salvar 2xx e preservar o emoji (não 500/encoding). Stage 37048. PR #10709. Headless."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19963_emoji_secao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
posts = []  # (status, url)
page = None
def on_resp(r):
    try:
        if re.search(r"/assessments\b", r.url) and r.request.method == "POST":
            posts.append((r.status, r.url))
    except Exception: pass
log = lambda *a: print(*a, flush=True)
EMOJI = "Conhecimento \U0001F9E0"  # 🧠 (4 bytes)
SEC = '[data-testid="questionnaire-section-0-name-input"], #questionnaire-section-0-name-input, [name="questionnaire-section-0-name-input"]'

def preenche_e_salva(page, qname, secname):
    page.goto(base + f"/o/{c['org_id']}/assessments/new", wait_until="domcontentloaded", timeout=30000)
    tw.dispensar_nps(page); page.wait_for_timeout(3000)
    # nome do questionário (primeiro input perto de "Nome do questionário", senão 1º text visível)
    qfield = page.locator('[data-testid*="questionnaire-name"], #questionnaire-name, input[name*="name" i]').first
    if not qfield.count(): qfield = page.locator('input[type=text]:visible').first
    qfield.fill(qname)
    # seção: se o campo não existe, tentar "Adicionar seção"
    sec = page.locator(SEC).first
    if not sec.count():
        try: page.get_by_role("button", name=re.compile(r"Adicionar se[çc][ãa]o|Nova se[çc][ãa]o", re.I)).first.click(timeout=3000); page.wait_for_timeout(1000)
        except Exception: pass
        sec = page.locator(SEC).first
    log("  campo seção existe?", sec.count())
    sec.fill(secname)
    page.wait_for_timeout(500)
    page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=6000)
    page.wait_for_timeout(5000); tw.dispensar_nps(page)

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True)
    page.on("response", on_resp)
    tw.login(page, c)
    veredito = "?"
    try:
        # 1) CONTROLE: acentos (2 bytes) — baseline que já funcionava
        posts.clear()
        preenche_e_salva(page, "QA19963 Controle Acentos", "Atitudes & Ações")
        ctrl = posts[-1] if posts else None
        log(f"[controle acentos] POST={ctrl} | url={page.url}")
        tw.snap(page, PASTA, "01-controle-acentos", full=True)

        # 2) EMOJI (4 bytes) — o caso do bug
        posts.clear()
        preenche_e_salva(page, "QA19963 Emoji Secao", EMOJI)
        emj = posts[-1] if posts else None
        redirecionou = "/assessments" in page.url and "/new" not in page.url
        corpo = page.evaluate("()=>document.body.innerText")
        toast_erro = bool(re.search(r"Erro ao salvar question|erro ao processar", corpo, re.I))
        log(f"[emoji] POST={emj} | redirecionou={redirecionou} | toast_erro={toast_erro}")
        tw.snap(page, PASTA, "02-emoji-pos-salvar", full=True)

        # 3) ROUND-TRIP: reabrir e checar o emoji intacto (só se salvou 2xx)
        intacto = None
        if emj and 200 <= emj[0] < 300:
            # achar o assessment recém-criado e reabrir; ler valor do campo de seção
            m = re.search(r"/assessments/(\d+)", page.url)
            aid = m.group(1) if m else None
            if not aid:
                # pegar o 1º da lista
                page.goto(base + f"/o/{c['org_id']}/assessments", wait_until="domcontentloaded", timeout=30000)
                tw.dispensar_nps(page); page.wait_for_timeout(2500)
                lnk = page.locator('a[href*="/assessments/"]').first
                href = lnk.get_attribute("href") if lnk.count() else ""
                mm = re.search(r"/assessments/(\d+)", href or ""); aid = mm.group(1) if mm else None
            if aid:
                page.goto(base + f"/o/{c['org_id']}/assessments/{aid}/edit", wait_until="domcontentloaded", timeout=30000)
                tw.dispensar_nps(page); page.wait_for_timeout(3000)
                val = page.locator(SEC).first
                txt = val.input_value() if val.count() else (page.evaluate("()=>document.body.innerText") or "")
                intacto = "\U0001F9E0" in (txt or "")
                log(f"[round-trip] assessment={aid} | valor seção tem 🧠? {intacto} | valor={txt!r}")
                tw.snap(page, PASTA, "03-roundtrip", full=True)

        ctrl_ok = bool(ctrl and 200 <= ctrl[0] < 300)
        emoji_ok = bool(emj and 200 <= emj[0] < 300) and (intacto is True)
        if not ctrl_ok:
            veredito = "FALHOU/ambiente (controle de acentos não salvou 2xx — env quebrado por outro motivo)"
        elif emoji_ok:
            veredito = "PASSOU (emoji salvo 2xx e preservado intacto)"
        else:
            veredito = f"FALHOU (emoji POST={emj} redir={redirecionou} toast_erro={toast_erro} intacto={intacto})"
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-600:])
        try: tw.snap(page, PASTA, "99-erro", full=True)
        except Exception: pass
        veredito = f"ERRO: {e}"
    finally:
        log(f"\n=> 19963: {veredito}")
        ctx.close(); browser.close()
# ponytail: cobri o caso 4-byte + controle de acentos + round-trip (o teste real de encoding).
# pulei variações emoji-isolado/emoji+acento — mesmo caminho de charset, baixo retorno; adicionar se o caso base for ambíguo.
