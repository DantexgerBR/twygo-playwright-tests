"""19002 — E2E. Org 37060. Conta dante@teste.com (admin+aluno). qid=73255 (Prova).

CONTROLE POSITIVO (switch ON): liga 'Analise por IA', responde como aluno, e checa
se a notificacao 'analisado por IA' aparece no sino (medindo a latencia L).

Roda 1 fase por vez via env FASE: 'on' (positivo) ou 'off' (negativo).
Resultados/latencia -> _resultado_FASE.json. Screenshots em evidencias/19002_validacao/.
"""
import os, re, json, time
import _twygo as tw

c = tw.cfg("IATEST")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "19002_validacao"
QID = "73255"
FASE = os.environ.get("FASE", "on")            # 'on' = positivo, 'off' = negativo
LIGAR = FASE == "on"
RESP_TXT = "Aprendi sobre o tema e aplico no dia a dia. Resposta para analise por IA."


def set_switch(page, ligar):
    page.goto(f"{BASE}/o/{ORG}/question_lists/{QID}/edit", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    sw = page.locator(".chakra-switch, [role=switch]").first
    estado = page.evaluate("()=>{const i=document.querySelector('.chakra-switch input,[role=switch]');return i?!!i.checked:null;}")
    if estado != ligar:
        sw.click(timeout=4000); page.wait_for_timeout(800)
    novo = page.evaluate("()=>{const i=document.querySelector('.chakra-switch input,[role=switch]');return i?!!i.checked:null;}")
    print(f"[switch] antes={estado} desejado={ligar} agora={novo}")
    # salvar
    for txt in ["Salvar", "Atualizar", "Concluir"]:
        b = page.get_by_role("button", name=re.compile(rf"^{txt}$", re.I))
        if b.count() and b.first.is_visible():
            b.first.click(timeout=4000); break
    page.wait_for_timeout(2500); tw.dispensar_nps(page)
    return novo


def get_eid(page):
    page.goto(f"{BASE}/dashboard_students", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    eids = page.evaluate(r"""()=>{const s=new Set();document.querySelectorAll('a[href*="/e/"]').forEach(a=>{const m=a.getAttribute('href').match(/\/e\/(\d+)/);if(m)s.add(m[1]);});return [...s];}""")
    return eids[0] if eids else None


def ler_notificacoes(page):
    """Abre o sino e retorna lista de textos das notificacoes."""
    try:
        bell = page.locator("[aria-label*='otification'], [aria-label*='otifica']").first
        bell.click(timeout=4000); page.wait_for_timeout(2000)
    except Exception:
        # fallback: clicar no 2o/3o icone do topo
        page.evaluate("()=>{const b=[...document.querySelectorAll('header button,nav button,[class*=bell]')].find(e=>/bell|notif|sino/i.test((e.className||'')+(e.getAttribute('aria-label')||'')));if(b)b.click();}")
        page.wait_for_timeout(2000)
    notes = page.evaluate(r"""()=>{
        const cont=[...document.querySelectorAll('[class*=notification],[class*=Notification],[role=menu],[class*=popover],[class*=dropdown]')].filter(e=>e.offsetParent);
        const out=[];
        cont.forEach(c=>c.querySelectorAll('li,div,a,p').forEach(e=>{const t=(e.innerText||'').replace(/\s+/g,' ').trim();if(t&&t.length>8&&t.length<160)out.push(t);}));
        return [...new Set(out)].slice(0,30);
    }""")
    return notes


def tem_notif_ia(notes):
    pat = re.compile(r"(an[aá]lise|analisad|intelig|\bIA\b|respostas?.{0,20}quest)", re.I)
    return [n for n in notes if pat.search(n)]


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    print(f"=== FASE {FASE.upper()} (switch {'ON' if LIGAR else 'OFF'}) ===")

    estado_sw = set_switch(page, LIGAR)
    eid = get_eid(page)
    print("EID:", eid)
    if not eid:
        tw.snap(page, PASTA, f"G-{FASE}-sem-eid"); raise SystemExit("nao achei eid do curso")

    # baseline de notificacoes ANTES de responder
    notes_antes = ler_notificacoes(page)
    print(f"[notif ANTES] {len(notes_antes)}: {notes_antes[:6]}")
    tw.snap(page, PASTA, f"G-{FASE}-01-notif-antes")
    page.keyboard.press("Escape"); page.wait_for_timeout(500)

    # entrar no curso e responder
    page.goto(f"{BASE}/e/{eid}", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    tw.snap(page, PASTA, f"G-{FASE}-02-curso")
    for nm in ["Continuar", "Iniciar", "Acessar conteúdo", "Acessar"]:
        try:
            page.get_by_role("button", name=re.compile(nm, re.I)).first.click(timeout=4000); break
        except Exception:
            try:
                page.get_by_text(re.compile(rf"^{nm}$", re.I)).first.click(timeout=2500); break
            except Exception: pass
    page.wait_for_timeout(5000); tw.dispensar_nps(page)
    print("player:", page.url)
    tw.snap(page, PASTA, f"G-{FASE}-03-player")

    # iniciar avaliacao se houver botao
    for nm in ["Iniciar", "Responder", "Começar", "Iniciar avaliação", "Iniciar questionário"]:
        try:
            page.get_by_role("button", name=re.compile(nm, re.I)).first.click(timeout=2500)
            page.wait_for_timeout(2500); break
        except Exception: pass
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, f"G-{FASE}-04-questionario")

    # responder: text/textarea -> texto ; radio -> 1a opcao
    page.evaluate(f"""()=>{{
        document.querySelectorAll('textarea, input[type=text]').forEach(i=>{{if(i.offsetParent){{i.value={json.dumps(RESP_TXT)};i.dispatchEvent(new Event('input',{{bubbles:true}}));i.dispatchEvent(new Event('change',{{bubbles:true}}));}}}});
    }}""")
    # CKEditor (resposta dissertativa rica)
    page.evaluate(f"""()=>{{if(window.CKEDITOR){{for(const k in CKEDITOR.instances){{CKEDITOR.instances[k].setData({json.dumps(RESP_TXT)});}}}}}}""")
    # radios: marcar 1 por grupo (name)
    page.evaluate("""()=>{const grp={};document.querySelectorAll('input[type=radio]').forEach(r=>{if(r.offsetParent&&!grp[r.name]){r.click();grp[r.name]=1;}});}""")
    page.wait_for_timeout(1000)
    tw.snap(page, PASTA, f"G-{FASE}-05-respondido")

    # enviar / finalizar
    enviou = False
    for nm in ["Enviar respostas", "Finalizar", "Enviar", "Concluir", "Próximo", "Salvar respostas"]:
        try:
            page.get_by_role("button", name=re.compile(rf"^{nm}", re.I)).first.click(timeout=3000)
            enviou = True; print(f"[enviar] '{nm}'"); break
        except Exception: pass
    page.wait_for_timeout(2500); tw.dispensar_nps(page)
    # confirmar modal de envio se aparecer
    for nm in ["Confirmar", "Sim", "Finalizar", "Enviar"]:
        try:
            page.get_by_role("button", name=re.compile(rf"^{nm}$", re.I)).first.click(timeout=2000)
            page.wait_for_timeout(1500); break
        except Exception: pass
    t_submit = time.time()
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, f"G-{FASE}-06-pos-envio")
    print(f"[envio] enviou={enviou} t_submit={t_submit}")

    # POLL do sino por notificacao de IA (ate ~3min)
    achou_em = None
    notes_final = []
    for i in range(18):  # 18 x 10s = 180s
        page.wait_for_timeout(10000)
        notes = ler_notificacoes(page)
        novas = [n for n in notes if n not in notes_antes]
        ia = tem_notif_ia(novas)
        print(f"   [poll {i+1}/18 | +{int(time.time()-t_submit)}s] novas={len(novas)} ia={len(ia)} :: {ia[:2]}")
        page.keyboard.press("Escape"); page.wait_for_timeout(300)
        if ia:
            achou_em = int(time.time() - t_submit); notes_final = notes;
            tw.snap(page, PASTA, f"G-{FASE}-07-NOTIF-IA")
            break
        notes_final = notes

    res = {"fase": FASE, "switch": estado_sw, "eid": eid, "enviou": enviou,
           "notif_ia_em_s": achou_em, "notas_antes": notes_antes, "notas_final": notes_final}
    (PASTA / f"_resultado_{FASE}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print("RESULTADO:", json.dumps({k: res[k] for k in ['fase','switch','enviou','notif_ia_em_s']}, ensure_ascii=False))
    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
