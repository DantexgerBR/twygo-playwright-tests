"""19002 — inspecionar atividades dos cursos 787722/723/724 (admin) p/ achar
qual tem questionario. Dump: titulo do curso + data-title de cada atividade."""
import re, json
import _twygo as tw

c = tw.cfg("")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"
CURSOS = ["787724", "787723", "787722"]

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    resultado = {}
    for eid in CURSOS:
        page.goto(f"{BASE}/e/{eid}/contents", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000); tw.dispensar_nps(page)
        titulo = page.evaluate(r"""()=>{const h=document.querySelector('h1,.title,[class*=title]');const bc=document.body.innerText.match(/Atividades\s*>\s*([^\n]+)/);return bc?bc[1].trim():(h?h.innerText.trim():'')}""")
        ativs = page.evaluate(r"""()=>Array.from(document.querySelectorAll('li.dd-item')).map(li=>({id:li.getAttribute('data-id'),title:(li.getAttribute('data-title')||li.innerText||'').replace(/\s+/g,' ').trim().slice(0,50)}))""")
        resultado[eid] = {"titulo": titulo, "atividades": ativs}
        print(f"\n=== curso {eid}: {titulo} ===")
        for a in ativs:
            print(f"   atividade id={a['id']} :: {a['title']}")
        tw.snap(page, PASTA, f"C3-curso-{eid}")
    (PASTA / "_inspecao_cursos.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    page.wait_for_timeout(800)
    ctx.close(); browser.close()
