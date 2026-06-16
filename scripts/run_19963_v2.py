# -*- coding: utf-8 -*-
"""19963 v2 — emoji 4-byte no nome de seção: POST /assessments deve salvar 2xx e
preservar o emoji (não 500). 37048, flag avaliacao_de_competencias ON. PR #10709."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19963_emoji_secao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
posts = []
def on_resp(r):
    try:
        if "twygoead.com/api/v1/" in r.url and re.search(r"/assessments(\?|$)", r.url) and r.request.method == "POST":
            body = ""
            if r.status >= 400:
                try: body = r.text()[:200]
                except Exception: pass
            posts.append((r.status, r.url, body))
    except Exception: pass
log = lambda *a: print(*a, flush=True)
EMOJI = "Conhecimento \U0001F9E0"  # 🧠

def cria(pg, qname, secname):
    pg.goto(base + f"/o/{c['org_id']}/assessments/new", wait_until="domcontentloaded", timeout=30000)
    tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
    pg.locator("#name").fill(qname)
    # usable_in: marcar competência (label clicável do checkbox)
    try: pg.evaluate("()=>{const e=document.querySelector('#usable_in-competency');if(e){(e.closest('label')||e).click();}}")
    except Exception: pass
    pg.locator('input[name="sections.0.name"]').fill(secname)
    try: pg.locator('input[name="sections.0.questions.0.title"]').fill("Pergunta teste 19963")
    except Exception as e: log("  [pergunta]", e)
    pg.wait_for_timeout(400)
    btn = pg.get_by_role("button", name=re.compile(r"^(Salvar|Criar question|Publicar|Concluir|Salvar question)", re.I)).first
    log("  salvar enabled?", btn.is_enabled() if btn.count() else "nao-achou")
    if btn.count(): btn.click(timeout=6000)
    pg.wait_for_timeout(5000); tw.dispensar_nps(pg)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); pg.on("response", on_resp); tw.login(pg, c)
    veredito = "?"
    try:
        # controle: acentos (2 bytes)
        posts.clear(); cria(pg, "QA19963 Controle", "Atitudes & Ações")
        ctrl = posts[-1] if posts else None
        log(f"[controle acentos] POST_status={ctrl[0] if ctrl else None} url_final={pg.url[-30:]}"); tw.snap(pg, PASTA, "v2-01-controle")
        # emoji (4 bytes)
        posts.clear(); cria(pg, "QA19963 Emoji", EMOJI)
        emj = posts[-1] if posts else None
        redir = "/assessments" in pg.url and "/new" not in pg.url
        toast = bool(re.search(r"Erro ao salvar question|erro ao processar", pg.evaluate("()=>document.body.innerText"), re.I))
        log(f"[emoji] POST_status={emj[0] if emj else None} body={emj[2] if emj else ''!r} redir={redir} toast_erro={toast}"); tw.snap(pg, PASTA, "v2-02-emoji", full=True)
        # round-trip: reabrir e checar emoji intacto
        intacto = None
        if emj and 200 <= emj[0] < 300:
            m = re.search(r"/assessments/(\d+)", pg.url); aid = m.group(1) if m else None
            if not aid:
                pg.goto(base+f"/o/{c['org_id']}/assessments", wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
                lnk = pg.locator('a[href*="/assessments/"]').first
                mm = re.search(r"/assessments/(\d+)", lnk.get_attribute("href") or "") if lnk.count() else None
                aid = mm.group(1) if mm else None
            if aid:
                pg.goto(base+f"/o/{c['org_id']}/assessments/{aid}/edit", wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
                v = pg.locator('input[name="sections.0.name"]').first
                txt = v.input_value() if v.count() else ""
                intacto = "\U0001F9E0" in (txt or "")
                log(f"[round-trip] assessment={aid} secao={txt!r} emoji_intacto={intacto}"); tw.snap(pg, PASTA, "v2-03-roundtrip", full=True)
        ctrl_ok = bool(ctrl and 200 <= ctrl[0] < 300)
        emoji_ok = bool(emj and 200 <= emj[0] < 300) and intacto is True
        veredito = ("FALHOU/ambiente (controle acentos não salvou 2xx)" if not ctrl_ok else
                    "PASSOU (emoji salvo 2xx e preservado)" if emoji_ok else
                    f"FALHOU (emoji POST_status={emj[0] if emj else None} intacto={intacto} toast={toast})")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:]); veredito=f"ERRO {e}"
        try: tw.snap(pg, PASTA, "v2-99-erro", full=True)
        except Exception: pass
    finally:
        log(f"\n=> 19963: {veredito}"); ctx.close(); b.close()
