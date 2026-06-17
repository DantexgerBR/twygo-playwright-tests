# -*- coding: utf-8 -*-
"""20108 build — cria um MODELO de avaliacao em /assessments/new marcando 'Pode ser
usado em: Avaliacao de desempenho', com 1 secao + 1 pergunta (unica escolha) + 2
opcoes, e Salva. Esse modelo deve passar a aparecer no seletor do ciclo."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
NOME = "QA20108 Modelo Desempenho"
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:45])) if r.request.method in ("POST","PUT") and "/api/" in r.url and ("assessment" in r.url.lower() or "questionnair" in r.url.lower()) else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/assessments/new", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.locator("#name").fill(NOME, timeout=4000)
        # marca "Avaliação de desempenho" em Pode ser usado em
        st = pg.evaluate(r"""()=>{const lab=[...document.querySelectorAll('label,div,span,p')].find(e=>{const t=(e.innerText||'').trim();return t==='Avaliação de desempenho'&&e.getBoundingClientRect().left>260});
          if(!lab)return null;const row=lab.closest('label')||lab.parentElement;const cb=(row&&row.querySelector('input[type=checkbox]'))||lab.previousElementSibling;
          const target=cb||lab;const r=(cb?cb:lab).getBoundingClientRect();return{x:r.left+ (cb?8:-12),y:r.top+r.height/2};}""")
        if st: pg.mouse.click(st["x"], st["y"]); pg.wait_for_timeout(700); log("marquei 'Avaliação de desempenho'")
        # secao + pergunta
        pg.locator("input[name='sections.0.name']").fill("Desempenho Geral", timeout=4000)
        pg.locator("input[name='sections.0.questions.0.title']").fill("O colaborador demonstra bom desempenho?", timeout=4000)
        # opcoes (textareas com id contendo -alt- e terminando em -text)
        opts = pg.locator("textarea[id*='-alt-'][id$='-text']")
        log("textareas de opcao:", opts.count())
        for i, val in enumerate(["Sim, plenamente", "Parcialmente"]):
            if i < opts.count():
                try: opts.nth(i).fill(val, timeout=3000); log(f"  opcao {i}: {val}")
                except Exception as ex: log(f"  opcao {i} erro: {str(ex)[:40]}")
        tw.snap(pg, PASTA, "modelo-create-01", full=True)
        # salvar
        net.clear()
        pg.get_by_role("button", name=re.compile("^Salvar$", re.I)).first.click(timeout=5000); pg.wait_for_timeout(3500)
        errs = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=error i],[role=alert],.chakra-form__error-message')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()).map(e=>e.innerText.trim()).slice(0,6)""")
        log("net:", net[-4:]); log("erros:", [*dict.fromkeys(errs)])
        salvou = ("/assessments" in pg.url and "/new" not in pg.url) or any(s in (200,201) for _,s,_ in net)
        log("url:", pg.url[-40:]); log("MODELO SALVO:", salvou)
        tw.snap(pg, PASTA, "modelo-create-02", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "modelo-create-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
