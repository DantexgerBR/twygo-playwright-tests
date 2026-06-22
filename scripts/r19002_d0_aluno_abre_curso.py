"""19002 — como ALUNO (conta dante, perfil aluno), abrir curso 787724 e achar a
atividade de questionario (Avaliacao) p/ responder. Captura URL/DOM que revela o
question_list id (necessario p/ controlar o switch Analise por IA via admin)."""
import re, json
import _twygo as tw

admin = tw.cfg("")
BASE = admin["base_url"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"
EID = "787724"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    # login (perfil aluno = sem switch admin)
    page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", admin["email"]); page.fill("#user_password", admin["senha"]); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    page.wait_for_timeout(2500); tw.dispensar_nps(page)
    print("home:", page.url)

    # abrir o curso como aluno
    for url in [f"{BASE}/e/{EID}", f"{BASE}/e/{EID}/show", f"{BASE}/aprender/e/{EID}"]:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        if "/users/login" not in page.url and "nao existe" not in page.content().lower():
            break
    print("curso aluno:", page.url)
    tw.snap(page, PASTA, "D0-aluno-curso")

    # listar atividades visiveis no player + achar links de questionario
    ativs = page.evaluate(
        r"""() => {
            const out=[];
            document.querySelectorAll('a,li,[class*=activity],[class*=atividade],[class*=lesson]').forEach(el=>{
                const t=(el.innerText||'').replace(/\s+/g,' ').trim();
                if(/avalia|question|prova|quiz/i.test(t) && t.length<60){
                    const a=el.matches('a')?el:el.querySelector('a');
                    out.push({t:t.slice(0,50), href:a?a.getAttribute('href'):''});
                }
            });
            const seen={}; return out.filter(o=>{const k=o.t+o.href; if(seen[k])return false; seen[k]=1; return true;}).slice(0,20);
        }""")
    print("[atividades/avaliacoes no player]:")
    for a in ativs:
        print(f"   {a['t']}  -> {a['href']}")
    # procurar qualquer referencia a question_list no DOM/scripts
    qids = page.evaluate(r"""()=>{const h=document.documentElement.innerHTML;const m=h.match(/question_list[_s]?\D{0,3}(\d{4,7})/gi)||[];return [...new Set(m)].slice(0,10);}""")
    print("[refs question_list no DOM]:", qids)
    (PASTA / "_aluno_curso.json").write_text(json.dumps({"url": page.url, "ativs": ativs, "qids": qids}, ensure_ascii=False, indent=2), encoding="utf-8")
    page.wait_for_timeout(800)
    ctx.close(); browser.close()
