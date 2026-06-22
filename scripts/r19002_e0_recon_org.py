"""19002 — recon da org dedicada (testeanalisedderespostas...). Descobre org_id,
o unico curso e o unico questionario (id + estado do switch 'Analise por IA')."""
import re, json
import _twygo as tw

c = tw.cfg("IATEST")  # base/email/senha (sem org ainda)
BASE = c["base_url"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    # login simples (sem switch admin — org desconhecida)
    page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", c["email"]); page.fill("#user_password", c["senha"]); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    print("pos-login:", page.url)
    tw.snap(page, PASTA, "E0-pos-login")

    # org_id: tentar achar em links /o/{id}/
    org = page.evaluate(r"""()=>{const m=document.documentElement.innerHTML.match(/\/o\/(\d+)\//);return m?m[1]:null;}""")
    if not org:
        # forcar perfil admin via varias orgs? tentar achar via link de menu
        org = page.evaluate(r"""()=>{const a=[...document.querySelectorAll('a[href*="/o/"]')][0];if(!a)return null;const m=a.href.match(/\/o\/(\d+)/);return m?m[1]:null;}""")
    print("org_id:", org)

    if org:
        # ir pro admin (events) e listar cursos
        page.goto(f"{BASE}/o/{org}/events?tab=events&profile=admin", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "E1-admin-eventos")
        cursos = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr[id^=row],[id^=row],a[href*="/e/"]')).map(e=>{const m=(e.id||'').match(/row(\d+)/)||(e.getAttribute('href')||'').match(/\/e\/(\d+)/);return m?{id:m[1],txt:(e.getAttribute('tag-name')||e.innerText||'').replace(/\s+/g,' ').trim().slice(0,50)}:null;}).filter(Boolean)""")
        seen={}; cursos=[x for x in cursos if not seen.get(x['id']) and not seen.update({x['id']:1})]
        print("cursos:", cursos)

        # listar questionarios
        page.goto(f"{BASE}/o/{org}/question_lists", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "E2-questionarios")
        quests = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,a[href*="question_lists/"]')).map(e=>{const a=e.matches('a')?e:e.querySelector('a[href*="question_lists/"]');const href=a?a.getAttribute('href'):'';const m=href.match(/question_lists\/(\d+)/);return m?{id:m[1],txt:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,50)}:null;}).filter(Boolean)""")
        seen2={}; quests=[x for x in quests if not seen2.get(x['id']) and not seen2.update({x['id']:1})]
        print("questionarios:", quests)

        # se achou 1 questionario, abrir edit e ler switch Analise por IA
        if quests:
            qid = quests[0]["id"]
            page.goto(f"{BASE}/o/{org}/question_lists/{qid}/edit", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3500); tw.dispensar_nps(page)
            tw.snap(page, PASTA, "E3-questionario-edit")
            sw = page.evaluate(r"""()=>{const lab=[...document.querySelectorAll('*')].find(e=>/Habilitar a geração de análise via IA/i.test(e.textContent||'')&&e.children.length<3);const ctrl=document.querySelector('.chakra-switch input,[role=switch]');return {achou_label:!!lab, switch_aria:ctrl?ctrl.getAttribute('aria-checked'):null, switch_checked:ctrl?ctrl.checked:null};}""")
            print(f"questionario {qid} switch Analise por IA:", sw)
            data = {"org_id": org, "cursos": cursos, "questionarios": quests, "qid_principal": qid, "switch": sw}
            (PASTA / "_org_iatest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
