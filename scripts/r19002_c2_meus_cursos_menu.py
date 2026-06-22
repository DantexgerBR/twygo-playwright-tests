"""19002 — listar 'Meus Cursos' do aluno clicando no menu (SPA), com titulos+ids."""
import re, json
import _twygo as tw

admin = tw.cfg("")
BASE = admin["base_url"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", admin["email"]); page.fill("#user_password", admin["senha"]); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    print("home:", page.url)

    # clicar "Meus Cursos" no menu lateral do aluno
    try:
        page.get_by_text(re.compile(r"^Meus Cursos$", re.I)).first.click(timeout=6000)
    except Exception as e:
        print("clique Meus Cursos:", e)
    page.wait_for_timeout(5000); tw.dispensar_nps(page)
    print("apos Meus Cursos:", page.url)
    tw.snap(page, PASTA, "C2-meus-cursos")

    cursos = page.evaluate(
        r"""() => {
            const out=[]; const seen={};
            // cards de curso: links /e/ID ou /contents/ID, com titulo do card
            document.querySelectorAll('a[href*="/e/"], a[href*="/contents/"], [class*=card]').forEach(el=>{
                const a = el.matches('a')? el : el.querySelector('a[href*="/e/"],a[href*="/contents/"]');
                const href = a ? (a.getAttribute('href')||'') : '';
                const m = href.match(/\/(?:e|contents)\/(\d+)/);
                const card = el.closest('[class*=card],li,article') || el;
                const titulo=(card.innerText||'').replace(/\s+/g,' ').trim().slice(0,70);
                if(m){ if(seen[m[1]])return; seen[m[1]]=1; out.push({id:m[1], titulo}); }
            });
            return out;
        }""")
    print(f"[meus cursos] {len(cursos)}:")
    for cu in cursos:
        print(f"   {cu['id']:>8}  {cu['titulo']}")
    (PASTA / "_meus_cursos.json").write_text(json.dumps(cursos, ensure_ascii=False, indent=2), encoding="utf-8")
    page.wait_for_timeout(800)
    ctx.close(); browser.close()
