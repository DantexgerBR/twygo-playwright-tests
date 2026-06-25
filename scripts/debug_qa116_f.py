# -*- coding: utf-8 -*-
"""Debug F — setup completo: organograma, perfis, criar registros."""
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

def fechar_modal(pg):
    for sel in ["button[aria-label*='Close']", "button[aria-label*='close']", "button[aria-label*='fechar']", "[role='dialog'] button:first-child"]:
        btn = pg.locator(sel).first
        if btn.count():
            try: btn.click(); pg.wait_for_timeout(600); return True
            except: pass
    pg.keyboard.press("Escape"); pg.wait_for_timeout(600); return True

def criar_registro_ui(pg, pessoa_email, conteudo):
    """Cria registro externo via form da UI como admin."""
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # 1. Campo Pessoas — clicar no input visível (não o hidden)
    # A estrutura tem um input visible com placeholder "Adicionar pessoas" + um button com ícone
    pessoas_inp = pg.locator("input[placeholder*='Adicionar'], input[placeholder*='pessoas']").first
    if pessoas_inp.count():
        # Clicar no ícone de pessoa ao lado
        # Ou no input diretamente
        pessoas_inp.click(timeout=4000, force=True)
        pg.wait_for_timeout(2000)
    else:
        # Tentar via JS click no container
        pg.evaluate("""() => {
            const inp = document.querySelector('input[placeholder*="Adicionar"]') ||
                       document.querySelector('[data-test-id="people-selector-hidden-input"]');
            if (inp) {
                const parent = inp.closest('form') || inp.parentElement;
                const icon = parent.querySelector('button, [role="button"]');
                if (icon) icon.click();
            }
        }""")
        pg.wait_for_timeout(2000)

    # 2. No modal — buscar e selecionar usuário
    modal = pg.locator("[role='dialog']").filter(visible=True).first
    if not modal.count():
        # Tentar via modal container
        modal = pg.locator(".chakra-modal__content").first
    log(f"  [modal] aberto: {modal.count() > 0}")

    if modal.count():
        # Buscar pelo email
        search = modal.locator("input").first
        if search.count():
            search.fill(pessoa_email)
            pg.wait_for_timeout(1500)

        # Selecionar checkbox do usuário
        # Os itens têm checkbox — selecionar o que tem o email
        user_item = modal.locator(f"text={pessoa_email}").first
        if user_item.count() == 0:
            user_item = modal.locator(f"text={pessoa_email.split('@')[0]}").first
        if user_item.count():
            # Encontrar o checkbox mais próximo
            chk = user_item.locator("xpath=ancestor::*[self::label or self::div[@class]][1]//input[@type='checkbox']").first
            if chk.count() == 0:
                chk = user_item.locator("xpath=preceding::input[@type='checkbox'][1]").first
            if chk.count():
                chk.click(force=True)
                pg.wait_for_timeout(500)
                log(f"  [modal] checkbox clicado para {pessoa_email}")
            else:
                # Clicar direto no item
                user_item.click(force=True)
                pg.wait_for_timeout(500)
                log(f"  [modal] item clicado para {pessoa_email}")

        snap(pg, f"f_modal_selecionado_{conteudo[:8]}")

        # Clicar "Associar" ou similar
        btn_assoc = modal.locator("button:last-of-type").first
        btns = modal.locator("button").all_text_contents()
        log(f"  [modal] botões: {btns}")
        btn_assoc2 = modal.locator("button").filter(has_text=re.compile(r"Associar|Vincular|Salvar|Confirmar", re.I)).first
        if btn_assoc2.count():
            btn_assoc2.click()
            pg.wait_for_timeout(2000)
            log("  [modal] Associar clicado")
        else:
            # Usar último botão (geralmente é o de confirmação)
            all_btns = modal.locator("button").all()
            if all_btns:
                all_btns[-1].click()
                pg.wait_for_timeout(2000)
                log("  [modal] último botão clicado")

    pg.wait_for_timeout(500)
    snap(pg, f"f_form_apos_modal_{conteudo[:8]}")

    # 3. Conteúdo (react-select creatable)
    # ID é #content mas pode ser react-select
    cont_input = pg.locator("#content").first
    if cont_input.count():
        # É um div de react-select — procurar o input dentro
        inp = cont_input.locator("input").first
        if inp.count():
            inp.click(); pg.wait_for_timeout(300)
            pg.keyboard.type(conteudo, delay=30); pg.wait_for_timeout(800)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            else: pg.keyboard.press("Enter")
            pg.wait_for_timeout(400)
            log(f"  [conteudo] digitado: {conteudo}")
    else:
        # Tentar pelo placeholder
        inp = pg.locator("[placeholder*='onteúdo'], [placeholder*='onteudo']").first
        if inp.count():
            inp.click(); pg.keyboard.type(conteudo, delay=30); pg.wait_for_timeout(500)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            else: pg.keyboard.press("Enter")

    # 4. Provedor
    prov = pg.locator("#provider").first
    if prov.count():
        prov_inp = prov.locator("input").first
        if prov_inp.count():
            prov_inp.click(); pg.wait_for_timeout(300)
            pg.keyboard.type("Alura", delay=30); pg.wait_for_timeout(800)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click(); pg.wait_for_timeout(300)
            log("  [provedor] Alura")

    # 5. Tipo de experiência
    tipo = pg.locator("#learningExperience").first
    if tipo.count():
        tipo_inp = tipo.locator("input").first
        if tipo_inp.count():
            tipo_inp.click(); pg.wait_for_timeout(300)
            pg.keyboard.type("Curso", delay=30); pg.wait_for_timeout(800)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click(); pg.wait_for_timeout(300)
            log("  [tipo] Curso")

    # 6. Categorias
    cat = pg.locator("#categories").first
    if cat.count():
        cat_inp = cat.locator("input").first
        if cat_inp.count():
            cat_inp.click(); pg.wait_for_timeout(300)
            pg.keyboard.type("T", delay=30); pg.wait_for_timeout(800)
            opts = pg.locator("[role='option']").all()
            if opts: opts[0].click(); pg.wait_for_timeout(300)
            pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
            log("  [categorias] selecionada")

    # 7. Carga horária
    carga = pg.locator("input[placeholder='HH:MM:SS']").first
    if carga.count():
        carga.fill("01:00:00"); log("  [carga] 01:00:00")

    # 8. Data de término
    date_inp = pg.locator("input[type='date']").first
    if date_inp.count():
        date_inp.fill("2026-06-01"); log("  [data] 2026-06-01")

    snap(pg, f"f_form_preenchido_{conteudo[:8]}")

    # 9. Salvar via JS (evita overlay)
    pg.evaluate("""() => {
        const btn = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Salvar');
        if (btn) btn.click();
    }""")
    pg.wait_for_timeout(5000)
    snap(pg, f"f_salvo_{conteudo[:8]}")
    log(f"  [salvar] url={pg.url}")

    # 10. Capturar ID
    url_depois = pg.url
    criou = "records/new" not in url_depois
    rec_id = None
    if criou:
        m = re.search(r"/records/(\d+)", url_depois)
        if m:
            rec_id = int(m.group(1))
        else:
            resp = pg.request.get(
                f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=10&page=1&order_by=created_at&order_type=desc",
                headers={"Accept":"application/json"},
            )
            if resp.status == 200:
                recs = resp.json().get("data",{}).get("records",[])
                match = next((r for r in recs if conteudo in str(r.get("content",""))), None)
                if match: rec_id = match.get("id")
    log(f"  → criou={criou} rec_id={rec_id}")
    return rec_id


with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # 1. Montar organograma: liderado1 → qaliderpuro como Responsável
    log("\n--- 1. Montar organograma via campo manager_name ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit", wait_until="domcontentloaded", timeout=15000)
    dispensar(pg)
    pg.wait_for_timeout(3000)

    # Limpar campo Responsável e preencher com qaliderpuro
    # O campo manager_name não é visível diretamente — usar JS para setar valor
    # e disparar o evento para o Rails reconhecer
    manager_check = pg.evaluate("""() => {
        const mn = document.querySelector('#manager_name, input[name="manager_name"]');
        const mi = document.querySelector('#professional_manager_id, input[name="professional[manager_id]"]');
        return {
            manager_name_exists: !!mn,
            manager_id_exists: !!mi,
            current_name: mn?.value,
            current_id: mi?.value,
        };
    }""")
    log(f"  [manager] campos: {manager_check}")

    snap(pg, "f_liderado_edit_antes_salvar")

    # Verificar se tem botão de busca ao lado do campo manager
    manager_id_inp = pg.locator("input#professional_manager_id, input[name='professional[manager_id]']").first
    log(f"  manager_id atual: {manager_id_inp.count() and manager_id_inp.get_attribute('value')}")

    # Tentar definir o manager_id diretamente via JS
    set_manager = pg.evaluate(f"""() => {{
        const inp = document.querySelector('#professional_manager_id') ||
                    document.querySelector('input[name="professional[manager_id]"]');
        const name_inp = document.querySelector('#manager_name') ||
                         document.querySelector('input[name="manager_name"]');
        if (inp && name_inp) {{
            inp.value = '{LIDER_PURO_ID}';
            name_inp.value = 'QALider Puro116';
            // Disparar eventos para React reconhecer
            ['input', 'change'].forEach(evt => {{
                inp.dispatchEvent(new Event(evt, {{bubbles: true}}));
                name_inp.dispatchEvent(new Event(evt, {{bubbles: true}}));
            }});
            return {{manager_id: inp.value, manager_name: name_inp.value}};
        }}
        return 'campos não encontrados';
    }}""")
    log(f"  [JS] set_manager = {set_manager}")
    pg.wait_for_timeout(500)
    snap(pg, "f_liderado_manager_js")

    # Salvar
    pg.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=5000)
    pg.wait_for_timeout(3000)
    snap(pg, "f_liderado_salvo")
    log(f"  url apos salvar liderado: {pg.url}")

    # Verificar se manager_id foi salvo
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit", wait_until="domcontentloaded", timeout=15000)
    dispensar(pg); pg.wait_for_timeout(2000)
    manager_val = pg.evaluate("""() => {
        const inp = document.querySelector('#professional_manager_id, input[name="professional[manager_id]"]');
        const name = document.querySelector('#manager_name, input[name="manager_name"]');
        return {manager_id: inp?.value, manager_name: name?.value};
    }""")
    log(f"  [verify] manager após salvar: {manager_val}")
    snap(pg, "f_liderado_verify")

    # 2. Marcar perfil "Gestor de turma" no qaliderpuro
    log("\n--- 2. Marcar Gestor de turma no qaliderpuro ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDER_PURO_ID}/edit", wait_until="domcontentloaded", timeout=15000)
    dispensar(pg); pg.wait_for_timeout(2000)

    # Os checkboxes de perfil parecem ser inputs padrão
    perfis_info = pg.evaluate("""() => {
        const all_inputs = [...document.querySelectorAll('input[type="checkbox"]')];
        return all_inputs.map(inp => ({
            id: inp.id,
            name: inp.name,
            checked: inp.checked,
            visible: inp.offsetParent !== null,
            parent_text: (inp.closest('label') || inp.parentElement || {}).innerText?.trim().slice(0,50) || '',
        }));
    }""")
    log(f"  Checkboxes encontrados: {perfis_info}")

    # Marcar/desmarcar por name
    # Baseado na estrutura vista, os checkboxes de perfil têm names como professional[profiles][]
    for info in perfis_info or []:
        nm = info.get("name", "")
        if "profile" in nm.lower() or "perfil" in nm.lower() or "role" in nm.lower():
            log(f"  Perfil checkbox: {info}")

    # Tentar por seletor específico de perfis de acesso
    # O HTML mostra: Administrador, Instrutor, Gestor de turma como checkboxes em "PERFIL DE ACESSO"
    snap(pg, "f_lider_perfis_antes")

    # Marcar Gestor de turma via position (terceiro checkbox de perfil)
    gestor_set = pg.evaluate("""() => {
        // Buscar a seção PERFIL DE ACESSO
        const all_els = [...document.querySelectorAll('*')];
        const header = all_els.find(e => (e.innerText||'').trim() === 'SELECIONE OS PERFIS DESTE USUÁRIO.');
        if (!header) return 'header not found';
        const container = header.closest('div') || header.parentElement;
        const checkboxes = [...container.querySelectorAll('input[type="checkbox"]')];
        const labels = checkboxes.map(c => {
            const lbl = c.closest('label') || c.nextElementSibling;
            return {checked: c.checked, text: (lbl?.innerText||'').trim(), name: c.name};
        });
        return labels;
    }""")
    log(f"  Perfis de acesso: {gestor_set}")

    ca.close(); ba.close()
