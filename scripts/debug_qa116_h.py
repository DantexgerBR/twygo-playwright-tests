# -*- coding: utf-8 -*-
"""Debug H — setup final definitivo: perfis, senha, registros."""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)

LIDER_PURO_ID  = 4299626   # qaliderpuro@teste.com
LIDERADO_ID    = 4298605   # liderado1@teste.com
FORA_ID        = 4298501   # devtestes@teste.com

log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

def dispensar(pg):
    tw.dispensar_nps(pg)
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

def criar_registro_ui_v2(pg, pessoa_email, conteudo):
    """Criar registro externo pela UI — versão com depuração do modal."""
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # Estrutura do campo Pessoas — baseado no screenshot:
    # <div>
    #   <input type="hidden" data-test-id="people-selector-hidden-input">
    #   <input type="text" placeholder="Adicionar pessoas">  ← visível
    #   <button>  ← ícone de pessoa
    # </div>
    # Precisamos clicar no botão visível
    pessoas_btn = pg.locator("input[placeholder*='Adicionar pessoas']").first
    if pessoas_btn.count():
        pessoas_btn.click(force=True, timeout=5000)
        pg.wait_for_timeout(2000)
        log(f"  [pessoas] clicou no input")
    else:
        log("  [pessoas] input não encontrado, tentando outro seletor")
        # Tentar o ícone
        pg.evaluate("""() => {
            const els = [...document.querySelectorAll('*')];
            const pessoas = els.find(e => e.placeholder === 'Adicionar pessoas');
            if (pessoas) pessoas.click();
        }""")
        pg.wait_for_timeout(2000)

    modal = pg.locator("[role='dialog']").filter(visible=True).first
    log(f"  [modal] aberto: {modal.count() > 0}")

    if modal.count():
        # Buscar
        search = modal.locator("input[type='search'], input[type='text'], input[placeholder*='email']").first
        if search.count():
            search.fill(pessoa_email)
            pg.wait_for_timeout(1500)

        snap(pg, f"h_modal_buscado_{conteudo[:8]}")

        # Verificar itens disponíveis
        items_text = modal.inner_text()
        log(f"  [modal] content: {items_text[:400]}")

        # Tentar clicar no item com o email
        user_row = modal.locator(f"text={pessoa_email}").first
        if user_row.count() == 0:
            nome_sem_arroba = pessoa_email.split("@")[0]
            user_row = modal.locator(f"text={nome_sem_arroba}").first

        if user_row.count():
            # Rolar até o elemento e clicar
            user_row.scroll_into_view_if_needed()
            pg.wait_for_timeout(300)
            # Clicar na área que tem checkbox
            # Tentar vários seletores no contexto do row
            clicou = False
            for sel in [
                "input[type='checkbox']",
                ".chakra-checkbox__control",
                ".pessoa-item-checkbox",
            ]:
                chk = user_row.locator(f"xpath=ancestor::div[contains(@class,'chakra') or contains(@class,'item')][1]//{sel.replace('.','[@class*=')}").first
                # Simplificar
                pass
            # Usar evaluate para clicar no elemento pai do email
            result = pg.evaluate(f"""() => {{
                // Encontrar o elemento que contém o email
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                let node;
                while (node = walker.nextNode()) {{
                    if (node.textContent.includes('{pessoa_email.split("@")[0]}')) {{
                        const el = node.parentElement;
                        // Ir até o container clicável
                        let container = el;
                        for (let i=0; i<5; i++) {{
                            if (!container) break;
                            const chk = container.querySelector('input[type="checkbox"]');
                            if (chk) {{ chk.click(); return 'clicked checkbox via ' + container.tagName; }}
                            container = container.parentElement;
                        }}
                        el.click();
                        return 'clicked element ' + el.tagName;
                    }}
                }}
                return 'not found';
            }}""")
            log(f"  [modal] JS click result: {result}")
            pg.wait_for_timeout(500)
            snap(pg, f"h_modal_chk_{conteudo[:8]}")

        # Botões do modal
        btns_txt = [b.strip() for b in modal.locator("button").all_text_contents() if b.strip()]
        log(f"  [modal] botões: {btns_txt}")

        btn_conf = modal.locator("button").filter(has_text=re.compile(r"Associar|Vincular|Adicionar|Confirmar|Salvar|OK", re.I)).first
        if btn_conf.count():
            btn_conf.click(); pg.wait_for_timeout(2000)
            log("  [modal] confirmou")
        elif btns_txt:
            # Clicar no último botão (normalmente o primário)
            modal.locator("button").last.click(); pg.wait_for_timeout(2000)
            log("  [modal] clicou último botão")

    snap(pg, f"h_apos_modal_{conteudo[:8]}")

    # Preencher campos (por IDs conhecidos dos select2/react-select)
    # Conteúdo
    cont = pg.locator("#content, [id^='react-select'][id*='content']").first
    if cont.count() == 0:
        # Buscar pelo placeholder
        cont = pg.locator("[placeholder*='onteúdo'], [placeholder*='onteudo']").first
    if cont.count():
        inp = cont.locator("input").first if cont.tag_name() != "input" else cont
        if inp.count() and inp.tag_name() == "input":
            inp.click(); pg.keyboard.type(conteudo, delay=30); pg.wait_for_timeout(800)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            else: pg.keyboard.press("Enter")
            log(f"  [conteudo] OK")

    # Provedor — digitar "Alura" e selecionar
    prov = pg.locator("#provider").first
    if prov.count():
        inp = prov.locator("input").first
        if inp.count():
            inp.click(); pg.keyboard.type("Alura", delay=30); pg.wait_for_timeout(800)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            log("  [provedor] OK")

    # Tipo de experiência
    tipo = pg.locator("#learningExperience").first
    if tipo.count():
        inp = tipo.locator("input").first
        if inp.count():
            inp.click(); pg.keyboard.type("Curso", delay=30); pg.wait_for_timeout(800)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            log("  [tipo] OK")

    # Categorias
    cat = pg.locator("#categories").first
    if cat.count():
        inp = cat.locator("input").first
        if inp.count():
            inp.click(); pg.wait_for_timeout(500)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            pg.keyboard.press("Escape")
            log("  [cat] OK")

    # Carga horária
    carga = pg.locator("input[placeholder='HH:MM:SS']").first
    if carga.count(): carga.fill("01:00:00"); log("  [carga] OK")

    # Data de término
    date = pg.locator("input[type='date']").first
    if date.count(): date.fill("2026-06-01"); log("  [data] OK")

    snap(pg, f"h_preenchido_{conteudo[:8]}")

    # Salvar via JS
    pg.evaluate("""() => {
        const btn = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Salvar');
        if (btn) btn.click();
    }""")
    pg.wait_for_timeout(5000)
    snap(pg, f"h_salvo_{conteudo[:8]}")
    log(f"  [salvar] url={pg.url}")

    criou = "records/new" not in pg.url
    rec_id = None
    if criou:
        m = re.search(r"/records/(\d+)", pg.url)
        if m: rec_id = int(m.group(1))
        else:
            resp = pg.request.get(
                f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=10&page=1&order_by=created_at&order_type=desc",
                headers={"Accept":"application/json"},
            )
            if resp.status == 200:
                recs = resp.json().get("data",{}).get("records",[])
                match = next((r for r in recs if conteudo in str(r.get("content",""))), None)
                if match: rec_id = match.get("id")
    log(f"  → rec_id={rec_id}")
    return rec_id

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # 1. Marcar Gestor de turma no qaliderpuro via click no label (não is_checked)
    log("\n--- 1. Marcar Gestor de turma no qaliderpuro ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDER_PURO_ID}/edit", wait_until="domcontentloaded", timeout=15000)
    dispensar(pg); pg.wait_for_timeout(2000)

    # Verificar estado atual via JS evaluate (que retornou checked=False antes)
    perfis = pg.evaluate("""() => {
        const chks = {
            admin: document.querySelector('#user_profile_settings_admin'),
            instructor: document.querySelector('#user_profile_settings_instructor'),
            manager_class: document.querySelector('#user_profile_settings_manager_class'),
        };
        return Object.entries(chks).reduce((acc, [k,el]) => {
            if (el) acc[k] = {checked: el.checked, type: el.type};
            return acc;
        }, {});
    }""")
    log(f"  Perfis atuais: {perfis}")

    # Gestor de turma = manager_class — marcar se não marcado
    if perfis.get("manager_class") and not perfis["manager_class"]["checked"]:
        pg.evaluate("""() => {
            const chk = document.querySelector('#user_profile_settings_manager_class');
            if (chk && !chk.checked) {
                chk.click();
                ['input','change'].forEach(evt => chk.dispatchEvent(new Event(evt, {bubbles:true})));
            }
        }""")
        pg.wait_for_timeout(300)
        log("  Gestor de turma marcado via JS")

    # Desmarcar Admin/Instructor se marcados
    for chk_id in ["user_profile_settings_admin", "user_profile_settings_instructor"]:
        pg.evaluate(f"""() => {{
            const chk = document.querySelector('#{chk_id}');
            if (chk && chk.checked) {{
                chk.click();
                ['input','change'].forEach(evt => chk.dispatchEvent(new Event(evt, {{bubbles:true}})));
            }}
        }}""")

    snap(pg, "h_lider_perfis")
    pg.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=5000)
    pg.wait_for_timeout(3000)
    log(f"  url: {pg.url}")
    snap(pg, "h_lider_salvo")

    # 2. Verificar se há campo senha em /o/37079/users/{id} (sem /edit)
    log("\n--- 2. Tentar definir senha ---")
    # Verificar endpoint de reset de senha via Rails helpers
    for endpoint, method, payload in [
        (f"/o/{ORG_ID}/users/{LIDER_PURO_ID}/generate_password", "POST", "{}"),
        (f"/o/{ORG_ID}/users/{LIDER_PURO_ID}/admin_reset_password", "POST", json.dumps({"password":"123456"})),
        (f"/api/v1/o/{ORG_ID}/professionals/{LIDER_PURO_ID}/update_password", "PATCH", json.dumps({"password":"123456"})),
    ]:
        if method == "POST":
            resp = pg.request.post(BASE_URL + endpoint, headers={"Accept":"application/json","Content-Type":"application/json"}, data=payload)
        else:
            resp = pg.request.patch(BASE_URL + endpoint, headers={"Accept":"application/json","Content-Type":"application/json"}, data=payload)
        log(f"  {method} {endpoint}: {resp.status} {resp.text()[:100]}")

    # 3. Criar registros via UI
    log("\n--- 3. Criar registro para liderado1 ---")
    rec_lid = criar_registro_ui_v2(pg, "liderado1@teste.com", "QA116-Liderado-Externo")
    log(f"  rec_liderado_id={rec_lid}")

    log("\n--- 4. Criar registro para devtestes ---")
    rec_fora = criar_registro_ui_v2(pg, "devtestes@teste.com", "QA116-ForaEquipe-Externo")
    log(f"  rec_fora_id={rec_fora}")

    log(f"\nResultado final:")
    log(f"  LIDER_PURO_ID={LIDER_PURO_ID}")
    log(f"  LIDERADO_ID={LIDERADO_ID}")
    log(f"  FORA_ID={FORA_ID}")
    log(f"  rec_liderado_id={rec_lid}")
    log(f"  rec_fora_id={rec_fora}")

    ca.close(); ba.close()
