"""19002 — ETAPA B1: criar Curso novo (React form) e capturar o evento_id.
Depois abre /e/{id}/contents e mostra como adicionar atividade (screenshot)."""
import json
import re
import _twygo as tw

c = tw.cfg("")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"
NOME_CURSO = "QA 19002 Curso Analise IA"
IDS = PASTA / "_ids.json"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    page.goto(f"{BASE}/o/{ORG}/contents/new?kind=0", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "B0-form-curso")

    # Nome
    page.fill('input[name="name"]', NOME_CURSO)
    # Tipo de experiencia (react-select creatable) — digita "Curso" + Enter
    try:
        le = page.locator("#learningExperience, [id*=learningExperience]").first
        le.click(timeout=4000)
        page.keyboard.type("Curso", delay=40)
        page.wait_for_timeout(1200)
        page.keyboard.press("Enter")
    except Exception as e:
        print(f"[aviso] learningExperience: {e}")
    page.wait_for_timeout(800)
    # Descricao CKEditor (best-effort)
    try:
        page.evaluate("()=>{if(window.CKEDITOR){for(const k in CKEDITOR.instances){CKEDITOR.instances[k].setData('Curso de teste 19002');}}}")
    except Exception:
        pass
    tw.snap(page, PASTA, "B1-curso-preenchido")

    # Salvar/Criar
    for txt in ["Salvar", "Criar", "Avançar", "Continuar", "Concluir"]:
        b = page.get_by_role("button", name=re.compile(rf"^{txt}$", re.I))
        if b.count() and b.first.is_visible():
            b.first.click(timeout=5000); print(f"[salvar curso] '{txt}'"); break
    page.wait_for_timeout(5000); tw.dispensar_nps(page)
    print(f"[apos criar curso] url={page.url}")
    tw.snap(page, PASTA, "B2-apos-criar-curso")

    m = re.search(r"/e/(\d+)", page.url) or re.search(r"/events/(\d+)", page.url) or re.search(r"/contents/(\d+)", page.url)
    eid = m.group(1) if m else None
    print(f"[evento_id] {eid}")

    # abrir lista de atividades do curso
    if eid:
        page.goto(f"{BASE}/e/{eid}/contents", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000); tw.dispensar_nps(page)
        print(f"[contents] {page.url}")
        tw.snap(page, PASTA, "B3-contents-curso")
        botoes = page.evaluate(
            "()=>Array.from(document.querySelectorAll('button,a,[role=button]')).map(b=>(b.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<40).slice(0,40)")
        print(f"[botoes contents] {botoes}")

    # persistir ids
    data = json.loads(IDS.read_text(encoding="utf-8")) if IDS.exists() else {}
    data.update({"evento_id": eid, "curso_nome": NOME_CURSO})
    IDS.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[ids] {data}")
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
