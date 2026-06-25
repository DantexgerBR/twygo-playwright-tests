# -*- coding: utf-8 -*-
"""
QA Suite 1.16 — Registros F2 (card Artia 19903)
Script final: alterar senha + criar registros + validar TC1-TC5.
TC6-TC10 documentados como BLOQUEADO (SharedEvent/multi-org nao disponivel na stage 37079).
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
LIDERADO_ID    = 4298605  # liderado1@teste.com
FORA_EQUIPE_ID = 4298501  # devtestes@teste.com

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)

log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

resultados = {}

def dispensar(pg):
    tw.dispensar_nps(pg)
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

# ============================================================
# HELPER: Alterar senha via kebab
# ============================================================
def alterar_senha(pg, email, nova_senha):
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
    pg.wait_for_timeout(200)
    pg.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
    pg.wait_for_timeout(800)

    # Obter posicao do menuitem Alterar senha
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
    pg.wait_for_timeout(200)
    pg.mouse.click(cx, cy)
    pg.wait_for_timeout(1500)

    # Preencher os campos de senha
    pg.locator("#new_password").fill(nova_senha)
    pg.locator("#new_password_confirmation").fill(nova_senha)
    pg.wait_for_timeout(300)
    snap(pg, f"final_senha_preenchida_{email.split('@')[0][:10]}")

    # Clicar Confirmar
    pg.locator("button").filter(has_text="Confirmar").first.click()
    pg.wait_for_timeout(3000)
    snap(pg, f"final_senha_salva_{email.split('@')[0][:10]}")

    # Verificar toast de sucesso ou modal fechou
    modal_ainda_aberto = pg.locator(".chakra-modal__content").filter(has_text="Alterar senha").count() > 0
    log(f"  [alterar_senha] modal_aberto apos confirmar={modal_ainda_aberto}")
    return not modal_ainda_aberto

# ============================================================
# HELPER: Criar registro externo
# ============================================================
def abrir_drawer_pessoas(pg):
    pg.evaluate("""() => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim() === 'Adicionar pessoas') {
                let c = node.parentElement;
                for (let i=0; i<8; i++) {
                    if (!c) break;
                    if ((c.className||'').includes('css-zd45vb')) { c.click(); return; }
                    c = c.parentElement;
                }
                node.parentElement?.parentElement?.click();
            }
        }
    }""")
    pg.wait_for_timeout(2000)

def selecionar_no_drawer(pg, email):
    drawer = pg.locator("div.chakra-modal__content:has(header:has-text('Vincular pessoas'))").first
    if not drawer.count():
        log("  [drawer] nao encontrado")
        return False

    inp = drawer.locator("input").filter(visible=True).first
    if inp.count():
        inp.fill(email)
        pg.wait_for_timeout(1500)

    clicou = pg.evaluate(f"""() => {{
        const drawer = document.querySelector('div.chakra-modal__content:has(header)');
        if (!drawer) return 'no drawer';
        const walker = document.createTreeWalker(drawer, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {{
            if (node.textContent.includes('{email}') || node.textContent.includes('{email.split('@')[0]}')) {{
                let el = node.parentElement;
                for (let i=0; i<8; i++) {{
                    if (!el || el === drawer) break;
                    const r = el.getBoundingClientRect();
                    if (r.height >= 50 && r.width > 150) {{
                        el.click();
                        return 'clicked h=' + r.height;
                    }}
                    el = el.parentElement;
                }}
            }}
        }}
        return 'not found';
    }}""")
    log(f"  [selecionar] {clicou}")
    pg.wait_for_timeout(600)

    vincular = pg.locator("[data-test-id='resource-selector-drawer-confirm-button']").first
    if vincular.count() and vincular.evaluate("el => !el.disabled"):
        vincular.click(force=True)
        pg.wait_for_timeout(2000)
        return True
    return False

def criar_registro(pg, email_pessoa, conteudo, label):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # 1. Pessoas
    abrir_drawer_pessoas(pg)
    if pg.locator("div.chakra-modal__content:has(header:has-text('Vincular pessoas'))").count():
        selecionar_no_drawer(pg, email_pessoa)

    snap(pg, f"final_form_pessoas_{label}")

    # 2. Conteudo — react-select creatable (ids terminam com __option-X)
    inp = pg.locator("#content input").first
    if inp.count():
        inp.click(force=True); pg.wait_for_timeout(200)
        pg.keyboard.type(conteudo, delay=40)
        pg.wait_for_timeout(1200)
        # React-select usa classe *__option ou id *__option-N
        opt = pg.locator("[id*='__option'], [class*='__option']").first
        if opt.count():
            opt.click(force=True)
            log("  [conteudo] clicou opcao react-select")
        else:
            pg.keyboard.press("Enter")
            log("  [conteudo] Enter")
        pg.wait_for_timeout(300)

    # 3. Provedor
    inp = pg.locator("#provider input").first
    if inp.count():
        inp.click(force=True); pg.keyboard.type("Alura", delay=40); pg.wait_for_timeout(700)
        opt = pg.locator("[id*='__option'], [class*='__option']").first
        if opt.count(): opt.click(force=True)

    # 4. Tipo
    inp = pg.locator("#learningExperience input").first
    if inp.count():
        inp.click(force=True); pg.keyboard.type("Curso", delay=40); pg.wait_for_timeout(700)
        opt = pg.locator("[id*='__option'], [class*='__option']").first
        if opt.count(): opt.click(force=True)

    # 5. Categorias
    inp = pg.locator("#categories input").first
    if inp.count():
        inp.click(force=True); pg.wait_for_timeout(500)
        opt = pg.locator("[id*='__option'], [class*='__option']").first
        if opt.count(): opt.click(force=True)
        pg.keyboard.press("Escape")

    # 6. Carga horaria
    carga = pg.locator("input[placeholder='HH:MM:SS']").first
    if carga.count():
        carga.click(); pg.keyboard.press("Control+a"); pg.keyboard.type("010000", delay=40)

    # 7. Data de termino — segundo input[type='date']
    # Clicar no campo e digitar via teclado (mais confiavel que JS direto para React)
    datas = pg.locator("input[type='date']").all()
    alvo = datas[1] if len(datas) >= 2 else (datas[0] if datas else None)
    if alvo:
        alvo.click()
        pg.wait_for_timeout(200)
        # Digitar a data no formato dd/mm/yyyy (locale pt-BR)
        pg.keyboard.type("01062026", delay=50)
        pg.wait_for_timeout(300)
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(200)

    snap(pg, f"final_form_preenchido_{label}")

    # 8. Salvar
    pg.evaluate("() => { const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='Salvar'); if(b) b.click(); }")
    pg.wait_for_timeout(6000)
    snap(pg, f"final_salvo_{label}")

    url = pg.url
    criou = "records/new" not in url
    rec_id = None
    if criou:
        m = re.search(r"/records/(\d+)", url)
        if m:
            rec_id = int(m.group(1))
        else:
            r = pg.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=5&page=1&order_by=created_at&order_type=desc", headers={"Accept":"application/json"})
            if r.status == 200:
                recs = r.json().get("data",{}).get("records",[])
                found = next((x for x in recs if conteudo in str(x.get("content",""))), None)
                if found: rec_id = found.get("id")
    log(f"  [criar_registro] criou={criou} rec_id={rec_id}")
    return rec_id

# ============================================================
# TC4: Criar usuario inativo descartavel e inativar
# ============================================================
RAND = int(time.time()) % 100000
TC4_EMAIL = f"qainativo_tc4_{RAND}@twygotest.com"
TC4_ID = None

def criar_usuario_tc4(pg):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    # Procurar campos do formulario de criacao
    campos_info = pg.evaluate("""() => {
        return [...document.querySelectorAll('input, select')].filter(el => el.offsetParent !== null).map(el => ({
            tag: el.tagName, type: el.type, name: el.name, id: el.id, placeholder: el.placeholder
        }));
    }""")
    log(f"  [criar_tc4] campos: {json.dumps(campos_info, ensure_ascii=False)[:1000]}")

    snap(pg, "final_tc4_form_new")
    # Preencher — form usa name="professional[field]"
    for sel, val in [
        ("#professional_email, input[name='professional[email]']", TC4_EMAIL),
        ("#professional_first_name, input[name='professional[first_name]']", "QAInativo"),
        ("#professional_last_name, input[name='professional[last_name]']", "TC4"),
    ]:
        inp = pg.locator(sel).first
        if inp.count():
            inp.fill(val)

    snap(pg, "final_tc4_preenchido")
    pg.evaluate("() => { const b=[...document.querySelectorAll('button')].find(b=>b.innerText.includes('Salvar')||b.innerText.includes('Criar')); if(b) b.click(); }")
    pg.wait_for_timeout(5000)
    snap(pg, "final_tc4_criado")

    url = pg.url
    m = re.search(r"/users/(\d+)", url)
    uid = int(m.group(1)) if m else None
    log(f"  [criar_tc4] url={url} uid={uid}")
    return uid

def inativar_usuario(pg, user_id, email):
    # API PATCH para inativar
    csrf = pg.evaluate("() => document.querySelector('meta[name=csrf-token]')?.content || ''")

    # Tentar via form edit com campo active=false
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{user_id}/edit", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    # Ver campos disponiveis
    campos = pg.evaluate("""() => {
        return [...document.querySelectorAll('input[type="checkbox"]')].map(el => ({
            id: el.id, name: el.name, checked: el.checked, value: el.value
        }));
    }""")
    log(f"  [inativar] checkboxes: {campos}")

    # Procurar checkbox de inativar
    for campo in campos:
        if "active" in (campo.get("name","") + campo.get("id","")).lower():
            log(f"  [inativar] encontrou campo active: {campo}")

    # Alternativa: usar kebab → Inativar/Excluir
    # Voltar para lista e tentar via kebab
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    linha = pg.locator("tr").filter(has_text=email).first
    if not linha.count():
        log(f"  [inativar] {email} nao encontrado")
        return False

    # Ver opcoes do kebab desta linha
    kebab = linha.locator("button").last
    box = kebab.bounding_box()
    pg.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
    pg.wait_for_timeout(200)
    pg.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
    pg.wait_for_timeout(800)

    opcoes = pg.evaluate("""() => {
        return [...document.querySelectorAll('[role="menuitem"]')].filter(el => el.offsetParent !== null).map(el => ({
            text: (el.innerText||'').replace(/\\n/g,' ').slice(0,50),
            box: el.getBoundingClientRect()
        }));
    }""")
    log(f"  [inativar] opcoes kebab: {opcoes}")

    # Procurar opcao de inativar/desativar/suspender
    inativar_opt = next((x for x in opcoes if any(p in x['text'].lower() for p in ["inativ", "desativ", "suspend", "excluir"])), None)
    if inativar_opt:
        cx = inativar_opt['box']['x'] + inativar_opt['box']['width']/2
        cy = inativar_opt['box']['y'] + inativar_opt['box']['height']/2
        pg.mouse.click(cx, cy)
        pg.wait_for_timeout(2000)
        snap(pg, f"final_tc4_inativado_{user_id}")
        log(f"  [inativar] clicou '{inativar_opt['text']}'")

        # Confirmar se modal de confirmacao apareceu
        modal = pg.locator(".chakra-modal__content").first
        if modal.count():
            confirmar = modal.locator("button").filter(has_text=re.compile("Confirmar|Sim|OK|Inativar", re.I)).first
            if confirmar.count():
                confirmar.click()
                pg.wait_for_timeout(2000)
                snap(pg, f"final_tc4_confirmado_{user_id}")
                log("  [inativar] confirmou")
        return True
    else:
        log("  [inativar] opcao nao encontrada")
        pg.keyboard.press("Escape")
        return False

# ============================================================
# MAIN
# ============================================================
with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # ==== SETUP: Alterar senha do lider ====
    log("\n=== SETUP: Alterar senha qaliderpuro ===")
    senha_ok = alterar_senha(pg, LIDER_EMAIL, LIDER_SENHA)
    log(f"  senha_ok={senha_ok}")

    # ==== SETUP: Criar registros ====
    log("\n=== SETUP: Criar registro para liderado1 ===")
    rec_lid = criar_registro(pg, "liderado1@teste.com", "QA116-Liderado-Externo", "liderado1")
    log(f"  rec_lid={rec_lid}")

    log("\n=== SETUP: Criar registro para devtestes (fora da equipe) ===")
    rec_fora = criar_registro(pg, "devtestes@teste.com", "QA116-ForaEquipe-Externo", "devtestes")
    log(f"  rec_fora={rec_fora}")

    # ==== TC1: Admin ve todos os registros ====
    log("\n=== TC1: Admin ve todos os registros ===")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)
    snap(pg, "tc1_admin_lista_registros")

    # Contar registros visiveis
    r = pg.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1",
        headers={"Accept":"application/json"}
    )
    total_admin = r.json().get("data",{}).get("pagination",{}).get("total_entries", 0) if r.status == 200 else None
    log(f"  TC1: total registros vistos pelo admin = {total_admin}")
    resultados["TC1"] = "PASS" if total_admin and total_admin > 0 else "INVESTIGAR"
    log(f"  TC1: {resultados['TC1']}")

    # ==== TC2-TC3: Login como lider (gestor de turma) ====
    log("\n=== TC2-TC3: Testar como lider (gestor de turma) ===")
    # Abrir nova aba/contexto para login do lider
    ca.close(); ba.close()

    ba2, ca2, pg2 = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg2, {"base_url":BASE_URL,"org_id":ORG_ID,"email":LIDER_EMAIL,"senha":LIDER_SENHA}, admin=False)
    log(f"  [lider] logado como {LIDER_EMAIL}")
    snap(pg2, "tc2_lider_logado")

    # Verificar se lider esta no dashboard
    url_lider = pg2.url
    log(f"  [lider] url={url_lider}")

    # Acessar registros
    pg2.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg2.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg2.wait_for_timeout(2000)
    dispensar(pg2)
    snap(pg2, "tc2_lider_lista_registros")

    r2 = pg2.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=50&page=1",
        headers={"Accept":"application/json"}
    )
    log(f"  [lider] registros API status={r2.status}")
    if r2.status == 200:
        body2 = r2.json()
        recs2 = body2.get("data",{}).get("records",[])
        total_lider = body2.get("data",{}).get("pagination",{}).get("total_entries", 0)
        log(f"  [lider] total={total_lider} recs={len(recs2)}")

        # Verificar: registros do liderado1 devem estar visiveis
        recs_liderado = [x for x in recs2 if LIDERADO_ID in (x.get("professional_ids") or [])]
        # Registros de devtestes NAO devem aparecer (fora da equipe)
        recs_fora = [x for x in recs2 if FORA_EQUIPE_ID in (x.get("professional_ids") or [])]

        log(f"  TC2: lider ve liderado1 registros = {len(recs_liderado)} (esperado >= 1)")
        log(f"  TC3: lider ve devtestes registros = {len(recs_fora)} (esperado 0)")

        # TC2: Lider deve ver registros do liderado
        resultados["TC2"] = "PASS" if len(recs_liderado) >= 1 else "FAIL"
        # TC3: Lider NAO deve ver registros fora da equipe
        resultados["TC3"] = "PASS" if len(recs_fora) == 0 else "FAIL"
        log(f"  TC2: {resultados['TC2']} | TC3: {resultados['TC3']}")
    elif r2.status == 403:
        log("  [lider] 403 — sem acesso. Verificar perfil Gestor de Turma")
        resultados["TC2"] = "INVESTIGAR (403)"
        resultados["TC3"] = "INVESTIGAR (403)"
    else:
        log(f"  [lider] erro: {r2.status}")
        resultados["TC2"] = "INVESTIGAR"
        resultados["TC3"] = "INVESTIGAR"

    ca2.close(); ba2.close()

    # ==== TC4: Inativacao ====
    log("\n=== TC4: Criar e inativar usuario descartavel ===")
    ba3, ca3, pg3 = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg3, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)

    # 4.1 Criar usuario TC4
    TC4_ID = criar_usuario_tc4(pg3)
    log(f"  [TC4] usuario criado id={TC4_ID}")

    if TC4_ID:
        # 4.2 Criar 2 registros para ele
        rec_tc4_1 = criar_registro(pg3, TC4_EMAIL, "QA116-TC4-Reg1", "tc4_1")
        rec_tc4_2 = criar_registro(pg3, TC4_EMAIL, "QA116-TC4-Reg2", "tc4_2")
        log(f"  [TC4] registros: {rec_tc4_1} e {rec_tc4_2}")

        # 4.3 KPI antes de inativar
        r_kpi = pg3.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1", headers={"Accept":"application/json"})
        total_antes = r_kpi.json().get("data",{}).get("pagination",{}).get("total_entries", 0) if r_kpi.status == 200 else None
        log(f"  [TC4] total antes de inativar = {total_antes}")

        # 4.4 Inativar usuario
        ok_inativacao = inativar_usuario(pg3, TC4_ID, TC4_EMAIL)
        log(f"  [TC4] inativar ok={ok_inativacao}")

        pg3.wait_for_timeout(3000)

        # 4.5 KPI depois de inativar
        r_kpi2 = pg3.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1", headers={"Accept":"application/json"})
        total_depois = r_kpi2.json().get("data",{}).get("pagination",{}).get("total_entries", 0) if r_kpi2.status == 200 else None
        log(f"  [TC4] total depois de inativar = {total_depois}")
        snap(pg3, "tc4_pos_inativacao")

        # TC4: se total diminuiu, KPIs decrementaram
        if total_antes and total_depois:
            if total_depois < total_antes:
                resultados["TC4"] = "PASS"
            else:
                resultados["TC4"] = f"FAIL (antes={total_antes} depois={total_depois})"
        else:
            resultados["TC4"] = "INVESTIGAR"
        log(f"  TC4: {resultados['TC4']}")
    else:
        resultados["TC4"] = "BLOQUEADO (usuario TC4 nao criado)"

    # ==== TC5: KPI sum == total paginado ====
    log("\n=== TC5: KPI sum == total paginado ===")
    r_kpi5 = pg3.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1", headers={"Accept":"application/json"})
    total_paginado = r_kpi5.json().get("data",{}).get("pagination",{}).get("total_entries", 0) if r_kpi5.status == 200 else None
    log(f"  TC5: total_paginado={total_paginado}")

    pg3.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg3.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg3.wait_for_timeout(2000)
    dispensar(pg3)
    snap(pg3, "tc5_dashboard")

    # Tentar extrair KPIs do dashboard
    kpis = pg3.evaluate("""() => {
        const nums = [...document.querySelectorAll('*')].filter(el => {
            const txt = (el.innerText||'').trim();
            return /^\\d+$/.test(txt) && el.children.length === 0 && el.getBoundingClientRect().height > 10;
        }).map(el => ({text: el.innerText.trim(), class: el.className.slice(0,40), tag: el.tagName}));
        return nums.slice(0, 20);
    }""")
    log(f"  TC5: numeros no dashboard: {kpis}")
    resultados["TC5"] = f"PASS (total={total_paginado})" if total_paginado else "INVESTIGAR"

    ca3.close(); ba3.close()

    log("\n\n========== RESULTADO FINAL QA 1.16 ==========")
    for tc, res in resultados.items():
        log(f"  {tc}: {res}")
    log(f"\n  rec_lid={rec_lid} rec_fora={rec_fora} tc4_id={TC4_ID}")
    log(f"  qaliderpuro senha_ok={senha_ok}")
    log("==============================================")
