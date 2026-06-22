"""19002 — recon: aba 'Meus Cursos' do aluno (dante) — titulos+ids+progresso, p/
achar o curso de teste (mais recente / com questionario)."""
import re, json
import _twygo as tw

admin = tw.cfg("")
BASE, ORG = admin["base_url"], admin["org_id"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", admin["email"]); page.fill("#user_password", admin["senha"]); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    page.wait_for_timeout(2500); tw.dispensar_nps(page)

    # Meus Cursos
    page.goto(f"{BASE}/student_contents", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print("url:", page.url)
    if "/users/login" in page.url:
        # fallback: clicar no menu Meus Cursos
        page.goto(f"{BASE}/dashboard_students", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2500)
        try:
            page.get_by_text(re.compile("Meus Cursos", re.I)).first.click(timeout=5000)
            page.wait_for_timeout(4000)
        except Exception as e:
            print("menu meus cursos:", e)
    print("url2:", page.url)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "C1-meus-cursos")

    cursos = page.evaluate(
        r"""() => {
            const out=[]; const seen={};
            document.querySelectorAll('a[href*="/e/"]').forEach(a=>{
                const m=(a.getAttribute('href')||'').match(/\/e\/(\d+)/); if(!m) return;
                const card=a.closest('[class*=card],li,.content,article,div');
                const titulo=(card?card.innerText:a.innerText||'').replace(/\s+/g,' ').trim().slice(0,70);
                if(seen[m[1]]) return; seen[m[1]]=1;
                out.push({id:m[1], titulo});
            });
            return out;
        }""")
    print(f"[meus cursos] {len(cursos)}:")
    for cu in cursos:
        print(f"   e/{cu['id']:>8}  {cu['titulo']}")
    (PASTA / "_meus_cursos.json").write_text(json.dumps(cursos, ensure_ascii=False, indent=2), encoding="utf-8")
    page.wait_for_timeout(800)
    ctx.close(); browser.close()
