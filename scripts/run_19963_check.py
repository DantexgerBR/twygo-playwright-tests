# -*- coding: utf-8 -*-
"""19963 — check preciso do caso emoji: preenche, LÊ o valor do campo de seção,
salva, captura validação/erro inline + status do POST. Disambigua client-block vs fill-fail."""
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
            try: body = r.text()[:300] if r.status >= 400 else ""
            except Exception: pass
            posts.append((r.status, body))
    except Exception: pass
log = lambda *a: print(*a, flush=True)
EMOJI = "Conhecimento \U0001F9E0"

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); pg.on("response", on_resp); tw.login(pg, c)
    try:
        pg.goto(base + f"/o/{c['org_id']}/assessments/new", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        pg.locator("#name").fill("QA19963 Emoji Check")
        pg.evaluate("()=>{const e=document.querySelector('#usable_in-competency');if(e)(e.closest('label')||e).click();}")
        sec = pg.locator('input[name="sections.0.name"]')
        sec.fill(EMOJI)
        pg.locator('input[name="sections.0.questions.0.title"]').fill("Pergunta teste")
        val_antes = sec.input_value()
        log(f"[campo seção] valor após fill = {val_antes!r} | tem 🧠? {chr(0x1F9E0) in val_antes}")
        tw.snap(pg, PASTA, "chk-01-preenchido", full=True)
        # salvar
        btn = pg.get_by_role("button", name=re.compile(r"^Salvar", re.I)).first
        btn.click(timeout=6000); pg.wait_for_timeout(5000); tw.dispensar_nps(pg)
        # estado pós-save
        redir = "/new" not in pg.url
        # mensagens de validação/erro visíveis
        erros = pg.evaluate(r"""()=>{
          const inval=[...document.querySelectorAll('[aria-invalid=true],[class*=error i],[class*=invalid i]')].map(e=>(e.innerText||e.getAttribute('aria-invalid')||'').toString().trim()).filter(Boolean).slice(0,8);
          const txtErro=[...document.querySelectorAll('p,span,div')].map(e=>(e.innerText||'').trim()).filter(t=>/erro|inv[áa]lid|emoji|caractere|n[ãa]o.*permit|obrigat/i.test(t)&&t.length<120).slice(0,6);
          return {inval, txtErro};}""")
        val_depois = pg.locator('input[name="sections.0.name"]').input_value() if pg.locator('input[name="sections.0.name"]').count() else "(saiu da tela)"
        log(f"[pós-save] redir={redir} url={pg.url[-30:]}")
        log(f"[pós-save] POST_status={posts[-1][0] if posts else 'NENHUM'} body={posts[-1][1] if posts else ''!r}")
        log(f"[pós-save] valido/erros={erros}")
        log(f"[pós-save] valor seção agora={val_depois!r}")
        tw.snap(pg, PASTA, "chk-02-pos-save", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "chk-99-erro", full=True)
        except Exception: pass
    finally:
        ctx.close(); b.close()
