# -*- coding: utf-8 -*-
"""Diagnostico — abre 'Vincular pessoas' no ciclo 166 e captura TODAS as requisicoes
de API (status) pra entender por que a lista de pessoas nao carrega."""
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
    reqs = []
    pg.on("response", lambda r: reqs.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:70])) if "/api/" in r.url and r.request.method=="GET" and any(k in r.url.lower() for k in ("people","participant","collaborator","colaborador","user","member","employee")) else None)
    pendentes = []
    pg.on("requestfailed", lambda req: pendentes.append((req.method, req.failure, req.url[-70:])) if "/api/" in req.url else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles/{CID}/campaigns/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.locator("input[name=name]").fill("QA20108 Campanha")
        click_tab(pg, "Quem participa"); pg.wait_for_timeout(800)
        reqs.clear()
        pg.get_by_text("Definir participantes", exact=True).last.click(timeout=4000)
        pg.wait_for_timeout(8000)  # espera a lista (ou o erro)
        log("=== requisicoes de pessoas/participantes ===")
        for r in reqs[-12:]: log("  ", r)
        log("=== requests FAILED ===")
        for r in pendentes[-8:]: log("  ", r)
        # checa se ainda tem spinner
        spin = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]');return drw?!!drw.querySelector('[class*=spinner i],.chakra-spinner'):false}""")
        vazio = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]');return drw?/nenhum|sem resultado|n[aã]o encontrad|vazi/i.test(drw.innerText):false}""")
        log("ainda tem spinner:", spin, "| mostra vazio:", vazio)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
