"""19002 — recon do lado ALUNO: logar como aluno e listar cursos inscritos (mais
recentes), p/ achar o curso ja montado com questionario. Tambem lista os
questionarios recentes (admin) p/ cruzar."""
import os, re, json
import _twygo as tw

# dante.tavares e a MESMA conta admin — usar a credencial que ja funciona,
# mas SEM trocar pro perfil admin (fica na visao de aluno / dashboard_students).
admin = tw.cfg("")
aluno = {"base_url": admin["base_url"], "org_id": admin["org_id"],
         "email": admin["email"], "senha": admin["senha"]}
BASE = admin["base_url"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    # login aluno (sem switch admin)
    page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", aluno["email"]); page.fill("#user_password", aluno["senha"])
    page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    print(f"[aluno login] {aluno['email']} -> {page.url}")
    tw.snap(page, PASTA, "C0-aluno-home")

    # listar cards de curso na home/dashboard do aluno
    cursos = page.evaluate(
        r"""() => {
            const out = [];
            document.querySelectorAll('a[href*="/e/"]').forEach(a => {
                const m = (a.getAttribute('href')||'').match(/\/e\/(\d+)/);
                if (!m) return;
                const txt = (a.innerText||a.getAttribute('title')||'').replace(/\s+/g,' ').trim();
                out.push({id:m[1], txt: txt.slice(0,60), href:a.getAttribute('href')});
            });
            // dedup por id
            const seen = {}; return out.filter(o=>{ if(seen[o.id])return false; seen[o.id]=1; return true; });
        }""")
    print(f"[cursos do aluno] {len(cursos)}:")
    for cur in cursos[:30]:
        print(f"   e/{cur['id']:>8}  {cur['txt']}")
    (PASTA / "_cursos_aluno.json").write_text(json.dumps(cursos, ensure_ascii=False, indent=2), encoding="utf-8")
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
