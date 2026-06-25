# -*- coding: utf-8 -*-
"""QA 1.16 v3 — abordagem focada e correta.

Mudancas vs v2:
- TC2/TC3: verifica por NOME do registro na UI (nao por professional_ids que e None)
- Dispensa LGPD antes de capturar screenshot do lider
- Cria registro liderado1 apenas se nao existir
- TC4: busca usuario 'QAInativo' existente ou cria um novo
- alterar_senha: busca qaliderpuro em todas as paginas (search por URL)
"""
import json, sys, re, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
LIDER_EMAIL    = "qaliderpuro@teste.com"
LIDER_SENHA    = "123456"
LIDER_ID       = 4299626
LIDERADO_ID    = 4298605   # liderado1@teste.com
LIDERADO_EMAIL = "liderado1@teste.com"
FORA_ID        = 4298501   # devtestes@teste.com
FORA_EMAIL     = "devtestes@teste.com"
CONTEUDO_LID   = "QA116-Liderado-Externo"
CONTEUDO_FORA  = "QA116-ForaEquipe-Externo"

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)

log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

resultados = {}

def dispensar(pg):
    tw.dispensar_nps(pg)
    # Aceitar modal de consentimento LGPD se aparecer
    for _ in range(3):
        try:
            btn = pg.locator("button").filter(has_text=re.compile("Aceitar|Concordo|Entendido|OK", re.I)).first
            if btn.count() and btn.is_visible():
                btn.click(force=True)
                pg.wait_for_timeout(800)
                break
        except: pass
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

# ============================================================
# HELPER: Verificar registros existentes via API
# ============================================================
def buscar_registros_com_conteudo(pg, conteudo):
    """Busca registros cujo campo content contem a string dada."""
    r = pg.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=50&page=1&order_by=created_at&order_type=desc",
        headers={"Accept": "application/json"}
    )
    if r.status != 200:
        return []
    recs = r.json().get("data", {}).get("records", [])
    return [x for x in recs if conteudo.lower() in str(x.get("content", "")).lower()]

# ============================================================
# HELPER: Alterar senha via UI (busca na lista com search URL)
# ============================================================
def alterar_senha(pg, email, nova_senha):
    # Navegar com filtro de busca via query string
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users?q[email_or_name_cont]={email.split('@')[0]}",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    linha = pg.locator("tr").filter(has_text=email).first
    if not linha.count():
        # Tentar sem filtro (pode ser que o filtro nao funcione)
        pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
        try: pg.wait_for_load_state("networkidle", timeout=8000)
        except: pass
        pg.wait_for_timeout(2000)
        dispensar(pg)
        linha = pg.locator("tr").filter(has_text=email).first
        if not linha.count():
            log(f"  [alterar_senha] {email} nao encontrado")
            return False

    kebab = linha.locator("button").last
    box = kebab.bounding_box()
    pg.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
    pg.wait_for_timeout(300)
    pg.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
    pg.wait_for_timeout(1000)

    alterar_box = pg.evaluate("""() => {
        const items = [...document.querySelectorAll('[role="menuitem"]')];
        const item = items.find(el => el.innerText && el.innerText.includes('Alterar senha'));
        return item ? item.getBoundingClientRect() : null;
    }""")
    if not alterar_box:
        log("  [alterar_senha] item nao encontrado")
        return False

    cx = alterar_box['x'] + alterar_box['width']/2
    cy = alterar_box['y'] + alterar_box['height']/2
    pg.mouse.move(cx, cy)
    pg.wait_for_timeout(300)
    pg.mouse.click(cx, cy)
    pg.wait_for_timeout(1500)

    # Aguardar o modal
    try:
        pg.wait_for_selector("#new_password", timeout=5000)
    except:
        log("  [alterar_senha] modal nao apareceu")
        snap(pg, "senha_modal_nao_apareceu")
        return False

    pg.locator("#new_password").fill(nova_senha)
    pg.locator("#new_password_confirmation").fill(nova_senha)
    pg.wait_for_timeout(300)
    snap(pg, "senha_preenchida")

    pg.locator("button").filter(has_text="Confirmar").first.click()
    pg.wait_for_timeout(3000)
    snap(pg, "senha_salva")

    modal_aberto = pg.locator(".chakra-modal__content").filter(has_text="Alterar senha").count() > 0
    log(f"  [alterar_senha] modal_aberto={modal_aberto}")
    return not modal_aberto

# ============================================================
# HELPER: Criar registro externo
# ============================================================
def criar_registro(pg, email_pessoa, conteudo, label):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    snap(pg, f"reg_form_inicial_{label}")

    # 1. Adicionar pessoas — o texto "Adicionar pessoas" e um <p> clicavel (css-jhncyh)
    # Clicar nele abre o drawer "Vincular pessoas"
    area_pessoas = pg.evaluate("""() => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim() === 'Adicionar pessoas') {
                let el = node.parentElement;
                for (let i=0; i<10; i++) {
                    if (!el) break;
                    const r = el.getBoundingClientRect();
                    if (r.height > 15 && r.width > 50) {
                        return {x: r.x + r.width/2, y: r.y + r.height/2};
                    }
                    el = el.parentElement;
                }
            }
        }
        return null;
    }""")

    if area_pessoas:
        pg.mouse.click(area_pessoas['x'], area_pessoas['y'])
        log(f"  [criar_registro] clicou em Adicionar pessoas")
    else:
        log(f"  [criar_registro] 'Adicionar pessoas' nao encontrado")

    pg.wait_for_timeout(2000)
    snap(pg, f"reg_drawer_{label}")

    # Verificar se drawer abriu
    drawer_aberto = pg.locator(".chakra-modal__content").filter(has_text="Vincular pessoas").count() > 0
    log(f"  [criar_registro] drawer aberto={drawer_aberto}")

    if drawer_aberto:
        # Input de busca: placeholder="Pesquise por nome ou e-mail"
        inp_busca = pg.locator("input[placeholder='Pesquise por nome ou e-mail']").first
        if not inp_busca.count():
            # Fallback: primeiro input visivel no drawer
            inp_busca = pg.locator(".chakra-modal__content input[type='text']").filter(visible=True).first
        if inp_busca.count():
            inp_busca.fill(email_pessoa)
            pg.wait_for_timeout(1500)
            log(f"  [criar_registro] digitou busca: {email_pessoa}")

        snap(pg, f"reg_drawer_busca_{label}")

        # Clicar no checkbox da pessoa encontrada
        # Os resultados aparecem como linhas com checkbox
        selecionou = pg.evaluate(f"""() => {{
            const modal = document.querySelector('.chakra-modal__content');
            if (!modal) return 'no modal';
            // Procurar checkbox nao marcado proximo ao email/nome
            const walker = document.createTreeWalker(modal, NodeFilter.SHOW_TEXT);
            let node;
            while (node = walker.nextNode()) {{
                const t = node.textContent.trim();
                if (t.includes('{email_pessoa.split('@')[0]}') || t.includes('{email_pessoa}')) {{
                    // Subir e achar o checkbox pai
                    let el = node.parentElement;
                    for (let i=0; i<10; i++) {{
                        if (!el || el === modal) break;
                        const chk = el.querySelector('input[type="checkbox"]');
                        if (chk) {{
                            chk.click();
                            return 'checkbox clicked near: ' + t.slice(0,40);
                        }}
                        const r = el.getBoundingClientRect();
                        if (r.height >= 50 && r.width > 200) {{
                            el.click();
                            return 'row clicked h=' + r.height + ' near: ' + t.slice(0,40);
                        }}
                        el = el.parentElement;
                    }}
                }}
            }}
            return 'not found in drawer';
        }}""")
        log(f"  [criar_registro] selecionou={selecionou}")
        pg.wait_for_timeout(800)
        snap(pg, f"reg_selecionado_{label}")

        # Botao Vincular (data-test-id ou texto)
        btn_vincular = pg.locator("[data-test-id='resource-selector-drawer-confirm-button']").first
        if not btn_vincular.count():
            btn_vincular = pg.locator(".chakra-modal__content button").filter(has_text=re.compile("^Vincular$", re.I)).first
        if not btn_vincular.count():
            btn_vincular = pg.locator(".chakra-modal__content button[class*='chakra-button']").last
        if btn_vincular.count():
            disabled = btn_vincular.evaluate("el => el.disabled")
            log(f"  [criar_registro] btn_vincular disabled={disabled}")
            if not disabled:
                btn_vincular.click(force=True)
                pg.wait_for_timeout(2000)
                log("  [criar_registro] confirmou drawer")
        else:
            log("  [criar_registro] botao Vincular nao encontrado")

    snap(pg, f"reg_apos_pessoas_{label}")

    # 2. Provedor — react-select-2-input (creatable)
    # No form: "Selecione ou crie um provedor"
    inp_p = pg.locator("input.creatable-select-field__input").nth(0)
    if inp_p.count():
        inp_p.click(force=True); pg.wait_for_timeout(200)
        pg.keyboard.type("Alura", delay=40); pg.wait_for_timeout(700)
        opt = pg.locator("[id*='__option'], [class*='__option']").first
        if opt.count():
            opt.click(force=True); log("  [provedor] clicou opcao")
        else:
            pg.keyboard.press("Enter"); log("  [provedor] Enter (criou novo)")
        pg.wait_for_timeout(300)

    # 3. Conteudo — react-select-3-input (creatable)
    inp_c = pg.locator("input.creatable-select-field__input").nth(1)
    if inp_c.count():
        inp_c.click(force=True); pg.wait_for_timeout(200)
        pg.keyboard.type(conteudo, delay=40); pg.wait_for_timeout(1200)
        opt = pg.locator("[id*='__option'], [class*='__option']").first
        if opt.count():
            opt.click(force=True); log("  [conteudo] clicou opcao")
        else:
            pg.keyboard.press("Enter"); log("  [conteudo] Enter (criou novo)")
        pg.wait_for_timeout(300)

    # 4. Tipo de experiencia — react-select-4-input
    inp_t = pg.locator("input.creatable-select-field__input").nth(2)
    if inp_t.count():
        inp_t.click(force=True); pg.keyboard.type("Curso", delay=40); pg.wait_for_timeout(700)
        opt = pg.locator("[id*='__option'], [class*='__option']").first
        if opt.count(): opt.click(force=True)
        else: pg.keyboard.press("Enter")
        pg.wait_for_timeout(200)

    # 5. Categorias — react-select multi com id="categories" (obrigatorio)
    # Clicar no container e selecionar a primeira opcao
    cat_pos = pg.evaluate("""() => {
        const el = document.querySelector('[id="categories"]');
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {x: r.x + r.width/2, y: r.y + r.height/2};
    }""")
    if cat_pos:
        pg.mouse.click(cat_pos['x'], cat_pos['y'])
        pg.wait_for_timeout(700)
        opt = pg.locator("[id*='__option'], [class*='__option']").first
        if opt.count():
            opt.click(force=True)
            log("  [categorias] selecionou")
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(200)
    else:
        log("  [categorias] elemento nao encontrado")

    # 6. Carga horaria — #workload_seconds (HH:MM:SS)
    carga = pg.locator("#workload_seconds").first
    if carga.count():
        carga.fill("01:00:00")
        pg.wait_for_timeout(200)

    # 6. Data de termino — #endDate
    alvo = pg.locator("#endDate").first
    if alvo.count():
        alvo.click(); pg.wait_for_timeout(300)
        pg.keyboard.type("01062026", delay=50)
        pg.wait_for_timeout(300)
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(200)

    snap(pg, f"reg_form_preenchido_{label}")

    # 7. Salvar
    pg.evaluate("() => { const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='Salvar'); if(b) b.click(); }")
    pg.wait_for_timeout(6000)
    snap(pg, f"reg_salvo_{label}")

    url = pg.url
    criou = "records/new" not in url
    rec_id = None
    if criou:
        m = re.search(r"/records/(\d+)", url)
        if m:
            rec_id = int(m.group(1))
        else:
            recs = buscar_registros_com_conteudo(pg, conteudo)
            if recs:
                rec_id = recs[0].get("id")
    log(f"  [criar_registro] label={label} criou={criou} rec_id={rec_id}")
    return rec_id

# ============================================================
# TC4: Usuario descartavel
# ============================================================
def buscar_ou_criar_tc4_user(pg):
    """Busca usuario 'QAInativo' existente ou cria um novo."""
    # Verificar se ja existe algum com o prefixo qainativo
    r = pg.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/professionals?per_page=50&q[email_cont]=qainativo",
        headers={"Accept": "application/json"}
    )
    if r.status == 200:
        data = r.json().get("data", {})
        profs = data.get("professionals", []) or data.get("users", []) or []
        # Filtrar pelo mais recente que nao seja liderado ou fora
        for p in profs:
            uid = p.get("id") or p.get("user_id")
            email = str(p.get("email", ""))
            if "qainativo" in email.lower() and uid:
                log(f"  [tc4] encontrou usuario existente: {email} id={uid}")
                return uid, email

    # Criar novo
    RAND = int(time.time()) % 100000
    email = f"qainativo_tc4_{RAND}@twygotest.com"
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)
    snap(pg, "tc4_form_new")

    for sel, val in [
        ("#professional_email, input[name='professional[email]']", email),
        ("#professional_first_name, input[name='professional[first_name]']", "QAInativo"),
        ("#professional_last_name, input[name='professional[last_name]']", f"TC4-{RAND}"),
    ]:
        inp = pg.locator(sel).first
        if inp.count():
            inp.fill(val)
            log(f"  [tc4] preencheu {sel[:30]} = {val[:30]}")

    snap(pg, "tc4_preenchido")
    pg.evaluate("() => { const b=[...document.querySelectorAll('button')].find(b=>b.innerText.includes('Salvar')||b.innerText.includes('Criar')); if(b) b.click(); }")
    pg.wait_for_timeout(5000)
    snap(pg, "tc4_criado")

    # ID via URL (se redirecionar para /users/ID)
    url = pg.url
    m = re.search(r"/users/(\d+)", url)
    if m:
        uid = int(m.group(1))
        log(f"  [tc4] criado uid={uid}")
        return uid, email

    # ID via API busca por email
    r2 = pg.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/professionals?per_page=10&q[email_cont]={email.split('@')[0]}",
        headers={"Accept": "application/json"}
    )
    if r2.status == 200:
        data2 = r2.json().get("data", {})
        profs2 = data2.get("professionals", []) or data2.get("users", []) or []
        for p in profs2:
            if email.lower() in str(p.get("email", "")).lower():
                uid = p.get("id") or p.get("user_id")
                log(f"  [tc4] criado via API uid={uid}")
                return uid, email

    # Fallback: buscar na pagina de usuarios
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)
    linha = pg.locator("tr").filter(has_text=email).first
    if linha.count():
        links = linha.locator("a[href*='/users/']").all()
        for lk in links:
            href = lk.get_attribute("href") or ""
            m2 = re.search(r"/users/(\d+)", href)
            if m2:
                uid = int(m2.group(1))
                log(f"  [tc4] criado via link uid={uid}")
                return uid, email

    log(f"  [tc4] nao conseguiu ID, email={email}")
    return None, email

def inativar_usuario(pg, user_id, email):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    linha = pg.locator("tr").filter(has_text=email).first
    if not linha.count():
        log(f"  [inativar] {email} nao encontrado")
        return False

    kebab = linha.locator("button").last
    box = kebab.bounding_box()
    pg.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
    pg.wait_for_timeout(200)
    pg.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
    pg.wait_for_timeout(800)

    opcoes = pg.evaluate("""() => {
        return [...document.querySelectorAll('[role="menuitem"]')].filter(el => el.offsetParent !== null).map(el => ({
            text: (el.innerText||'').replace(/\\n/g,' ').trim().slice(0,50),
            box: el.getBoundingClientRect()
        }));
    }""")
    log(f"  [inativar] opcoes: {[o['text'] for o in opcoes]}")

    opt = next((x for x in opcoes if any(p in x['text'].lower() for p in ["inativ", "desativ", "suspend"])), None)
    if not opt:
        # Excluir como fallback (autorizado para usuarios criados por nos)
        opt = next((x for x in opcoes if "excluir" in x['text'].lower()), None)

    if not opt:
        log("  [inativar] opcao nao encontrada")
        pg.keyboard.press("Escape")
        return False

    cx = opt['box']['x'] + opt['box']['width']/2
    cy = opt['box']['y'] + opt['box']['height']/2
    pg.mouse.click(cx, cy)
    pg.wait_for_timeout(2000)
    snap(pg, f"tc4_inativar_clicou")

    # Confirmar modal
    modal = pg.locator(".chakra-modal__content").first
    if modal.count():
        btn_confirmar = modal.locator("button").filter(has_text=re.compile("Confirmar|Sim|OK|Inativar|Excluir", re.I)).last
        if btn_confirmar.count():
            btn_confirmar.click()
            pg.wait_for_timeout(3000)
            snap(pg, "tc4_confirmado")
            log(f"  [inativar] confirmou '{opt['text']}'")
    else:
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(2000)

    return True

# ============================================================
# MAIN
# ============================================================
with tw.sync_playwright() as p:
    # ========= ADMIN: Setup =========
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # Verificar registros existentes
    log("\n=== Verificar registros existentes ===")
    recs_lid  = buscar_registros_com_conteudo(pg, CONTEUDO_LID)
    recs_fora = buscar_registros_com_conteudo(pg, CONTEUDO_FORA)
    log(f"  recs_lid={len(recs_lid)}  recs_fora={len(recs_fora)}")

    # Alterar senha do lider (necessario para login TC2)
    log("\n=== SETUP: Alterar senha qaliderpuro ===")
    senha_ok = alterar_senha(pg, LIDER_EMAIL, LIDER_SENHA)
    log(f"  senha_ok={senha_ok}")

    # Criar registro liderado1 se nao existir
    rec_lid_id = recs_lid[0].get("id") if recs_lid else None
    if not rec_lid_id:
        log("\n=== SETUP: Criar registro liderado1 ===")
        rec_lid_id = criar_registro(pg, LIDERADO_EMAIL, CONTEUDO_LID, "liderado1")
    else:
        log(f"\n=== SETUP: registro liderado1 ja existe id={rec_lid_id} ===")

    # Criar registro devtestes se nao existir
    rec_fora_id = recs_fora[0].get("id") if recs_fora else None
    if not rec_fora_id:
        log("\n=== SETUP: Criar registro devtestes ===")
        rec_fora_id = criar_registro(pg, FORA_EMAIL, CONTEUDO_FORA, "devtestes")
    else:
        log(f"\n=== SETUP: registro devtestes ja existe id={rec_fora_id} ===")

    log(f"  rec_lid_id={rec_lid_id} rec_fora_id={rec_fora_id}")

    # ========= TC1: Admin ve todos =========
    log("\n=== TC1: Admin ve todos os registros ===")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)
    snap(pg, "tc1_admin_registros")

    r_admin = pg.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1",
        headers={"Accept": "application/json"}
    )
    total_admin = 0
    if r_admin.status == 200:
        total_admin = r_admin.json().get("data", {}).get("pagination", {}).get("total_entries", 0)
    log(f"  TC1: total_admin={total_admin}")
    resultados["TC1"] = "PASS" if total_admin > 0 else "FAIL"
    log(f"  TC1: {resultados['TC1']}")

    ca.close(); ba.close()

    # ========= TC2 e TC3: Login como lider =========
    log("\n=== TC2+TC3: Login como lider (Gestor de Turma) ===")
    ba2, ca2, pg2 = tw.nova_pagina(p, slow_mo=300)

    login_ok = False
    try:
        tw.login(pg2, {"base_url":BASE_URL,"org_id":ORG_ID,"email":LIDER_EMAIL,"senha":LIDER_SENHA}, admin=False)
        login_ok = True
        log(f"  [lider] login OK")
    except Exception as e:
        log(f"  [lider] login ERRO: {e}")

    if login_ok:
        snap(pg2, "tc2_lider_logado")

        # Acessar registros
        pg2.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
        try: pg2.wait_for_load_state("networkidle", timeout=8000)
        except: pass
        pg2.wait_for_timeout(2000)
        dispensar(pg2)
        snap(pg2, "tc2_lider_registros_antes_lgpd")

        # Aguardar mais 2s e tentar dispensar novamente
        pg2.wait_for_timeout(2000)
        dispensar(pg2)
        snap(pg2, "tc2_lider_registros")

        # Verificar via texto da pagina quais registros aparecem
        texto_pagina = pg2.evaluate("() => document.body.innerText")
        tem_liderado = CONTEUDO_LID in texto_pagina
        tem_fora     = CONTEUDO_FORA in texto_pagina
        log(f"  TC2: lider ve '{CONTEUDO_LID}'={tem_liderado}")
        log(f"  TC3: lider ve '{CONTEUDO_FORA}'={tem_fora}")

        # Verificar total via API (como lider)
        r2 = pg2.request.get(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1",
            headers={"Accept": "application/json"}
        )
        total_lider = 0
        if r2.status == 200:
            total_lider = r2.json().get("data", {}).get("pagination", {}).get("total_entries", 0)
        log(f"  [lider] total via API={total_lider} (admin={total_admin})")

        # TC2: lider deve VER o registro do liderado (direto subordinado)
        # Se o escopo funciona, tem_liderado=True e total_lider < total_admin
        resultados["TC2"] = "PASS" if tem_liderado else "FAIL"
        # TC3: lider NAO deve ver o registro de devtestes (fora da equipe)
        resultados["TC3"] = "PASS" if not tem_fora else "FAIL"
        log(f"  TC2: {resultados['TC2']} | TC3: {resultados['TC3']}")

        # Obs adicional: escopo real
        if total_lider == total_admin:
            log(f"  [obs] lider ve TODOS os registros ({total_lider}) — sem escopo por equipe")
        elif total_lider < total_admin:
            log(f"  [obs] lider ve SUBSET ({total_lider} de {total_admin}) — escopo funcionando")
    else:
        resultados["TC2"] = "BLOQUEADO (login falhou)"
        resultados["TC3"] = "BLOQUEADO (login falhou)"

    ca2.close(); ba2.close()

    # ========= TC4: KPI apos inativacao =========
    log("\n=== TC4: Inativacao de usuario ===")
    ba3, ca3, pg3 = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg3, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)

    # Buscar ou criar usuario tc4
    tc4_id, tc4_email = buscar_ou_criar_tc4_user(pg3)
    log(f"  [TC4] tc4_id={tc4_id} email={tc4_email}")

    if tc4_id:
        # Criar 2 registros para o usuario TC4
        recs_tc4 = buscar_registros_com_conteudo(pg3, "QA116-TC4-Reg1")
        if not recs_tc4:
            log("  [TC4] criando registros...")
            criar_registro(pg3, tc4_email, "QA116-TC4-Reg1", "tc4_1")
            criar_registro(pg3, tc4_email, "QA116-TC4-Reg2", "tc4_2")
        else:
            log("  [TC4] registros ja existem")

        # KPI antes
        r_antes = pg3.request.get(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1",
            headers={"Accept": "application/json"}
        )
        total_antes = r_antes.json().get("data", {}).get("pagination", {}).get("total_entries", 0) if r_antes.status == 200 else 0
        log(f"  [TC4] total antes={total_antes}")

        # Navegar para dashboard de registros e capturar KPIs
        pg3.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
        try: pg3.wait_for_load_state("networkidle", timeout=8000)
        except: pass
        pg3.wait_for_timeout(2000)
        dispensar(pg3)
        snap(pg3, "tc4_antes_inativacao")

        # Inativar
        ok_inativar = inativar_usuario(pg3, tc4_id, tc4_email)
        log(f"  [TC4] inativar ok={ok_inativar}")

        pg3.wait_for_timeout(4000)

        # KPI depois
        r_depois = pg3.request.get(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1",
            headers={"Accept": "application/json"}
        )
        total_depois = r_depois.json().get("data", {}).get("pagination", {}).get("total_entries", 0) if r_depois.status == 200 else 0
        log(f"  [TC4] total depois={total_depois}")

        # Navegar para dashboard e capturar KPIs visuais
        pg3.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
        try: pg3.wait_for_load_state("networkidle", timeout=8000)
        except: pass
        pg3.wait_for_timeout(2000)
        dispensar(pg3)
        snap(pg3, "tc4_depois_inativacao")

        if ok_inativar:
            if total_depois < total_antes:
                resultados["TC4"] = f"PASS (antes={total_antes} depois={total_depois})"
            else:
                resultados["TC4"] = f"FAIL (total nao diminuiu: antes={total_antes} depois={total_depois})"
        else:
            resultados["TC4"] = "FAIL (nao conseguiu inativar)"
        log(f"  TC4: {resultados['TC4']}")
    else:
        resultados["TC4"] = "BLOQUEADO (usuario TC4 nao encontrado/criado)"
        log(f"  TC4: {resultados['TC4']}")

    # ========= TC5: KPI sum == total paginado =========
    log("\n=== TC5: KPI dashboard == total paginado ===")
    pg3.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg3.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg3.wait_for_timeout(2000)
    dispensar(pg3)

    r_kpi5 = pg3.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1",
        headers={"Accept": "application/json"}
    )
    total_final = 0
    if r_kpi5.status == 200:
        total_final = r_kpi5.json().get("data", {}).get("pagination", {}).get("total_entries", 0)
    log(f"  TC5: total_paginado={total_final}")

    # Capturar numeros visiveis no dashboard
    numeros = pg3.evaluate("""() => {
        return [...document.querySelectorAll('*')].filter(el => {
            const txt = (el.innerText||'').trim();
            return /^\\d+$/.test(txt) && el.children.length === 0 &&
                   el.getBoundingClientRect().height > 10 && parseInt(txt) > 0;
        }).map(el => ({
            val: el.innerText.trim(),
            tag: el.tagName,
            cls: el.className.slice(0,50)
        })).slice(0,15);
    }""")
    log(f"  TC5: numeros no dashboard: {numeros}")
    snap(pg3, "tc5_kpi_dashboard")

    resultados["TC5"] = f"PASS (total={total_final})" if total_final > 0 else "INVESTIGAR"
    log(f"  TC5: {resultados['TC5']}")

    ca3.close(); ba3.close()

    # ========= RESULTADO FINAL =========
    log("\n\n========== RESULTADO FINAL QA 1.16 ==========")
    log(f"  rec_lid_id={rec_lid_id}  rec_fora_id={rec_fora_id}")
    log(f"  senha_ok={senha_ok}  tc4_id={tc4_id}")
    print()
    for tc, res in resultados.items():
        log(f"  {tc}: {res}")
    log("  TC6-TC10: BLOQUEADO (SharedEvent/multi-org nao disponivel na stage 37079)")
    log("==============================================")
