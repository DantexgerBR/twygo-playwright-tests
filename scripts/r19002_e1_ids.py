"""19002 — pegar ids do questionario e do curso na org 37060 + estado do switch."""
import re, json
import _twygo as tw

c = tw.cfg("IATEST")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)  # agora com org -> switch admin
    print("login:", page.url)

    # QUESTIONARIO id — na lista, ler href de edicao (pencil) ou data
    page.goto(f"{BASE}/o/{ORG}/question_lists", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    qids = page.evaluate(r"""()=>{
        const ids=new Set();
        document.querySelectorAll('a[href*="question_lists/"]').forEach(a=>{const m=a.getAttribute('href').match(/question_lists\/(\d+)/);if(m)ids.add(m[1]);});
        // tambem onclick/data
        document.querySelectorAll('[onclick],[data-href]').forEach(e=>{const s=(e.getAttribute('onclick')||'')+(e.getAttribute('data-href')||'');const m=s.match(/question_lists\/(\d+)/);if(m)ids.add(m[1]);});
        return [...ids];
    }""")
    print("question_list ids na lista:", qids)
    qid = qids[0] if qids else None
    if not qid:
        # fallback: clicar no pencil da primeira linha e ler URL
        try:
            page.locator("tr").filter(has_text="questionario").first.locator("a, [class*=edit], svg").first.click(timeout=4000)
            page.wait_for_timeout(2500)
            m = re.search(r"question_lists/(\d+)", page.url); qid = m.group(1) if m else None
        except Exception as e:
            print("pencil fallback:", e)
    print("QID:", qid)

    # abrir edit do questionario e ler switch Analise por IA
    sw = None
    if qid:
        page.goto(f"{BASE}/o/{ORG}/question_lists/{qid}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3500); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "E4-questionario-edit")
        sw = page.evaluate(r"""()=>{
            const ctrl=document.querySelector('.chakra-switch input,[role=switch]');
            const lab=[...document.querySelectorAll('*')].some(e=>/Habilitar a geração de análise via IA/i.test(e.textContent||''));
            return {label_ia:lab, aria_checked:ctrl?ctrl.getAttribute('aria-checked'):null, checked:ctrl?ctrl.checked:null};
        }""")
        print("switch Analise por IA:", sw)

    # CURSO id — events list
    page.goto(f"{BASE}/o/{ORG}/events?tab=events", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    eids = page.evaluate(r"""()=>{
        const ids=new Set();
        document.querySelectorAll('[id^=row]').forEach(e=>{const m=e.id.match(/row(\d+)/);if(m)ids.add(m[1]);});
        document.querySelectorAll('a[href*="/e/"]').forEach(a=>{const m=a.getAttribute('href').match(/\/e\/(\d+)/);if(m)ids.add(m[1]);});
        document.querySelectorAll('[onclick]').forEach(e=>{const m=(e.getAttribute('onclick')||'').match(/\/e\/(\d+)/);if(m)ids.add(m[1]);});
        return [...ids];
    }""")
    print("event ids:", eids)
    tw.snap(page, PASTA, "E5-eventos")

    data = {"org_id": ORG, "qid": qid, "switch": sw, "event_ids": eids}
    (PASTA / "_org_iatest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SALVO:", data)
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
