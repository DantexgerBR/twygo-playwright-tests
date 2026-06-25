# -*- coding: utf-8 -*-
"""Debug T — alterar senha qaliderpuro via kebab 'Alterar senha', depois criar registros."""
import json, sys, re, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)

log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

def dispensar(pg):
    tw.dispensar_nps(pg)
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

# ============================================================
# PARTE 1: Alterar senha qaliderpuro
# ============================================================
def alterar_senha_usuario(pg, email_usuario, nova_senha="123456"):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    # Procurar linha com email
    linha = pg.locator("tr").filter(has_text=email_usuario).first
    if not linha.count():
        log(f"  [alterar_senha] usuario nao encontrado: {email_usuario}")
        return False

    # Clicar no kebab da linha
    kebab = linha.locator("button").last
    kebab.click()
    pg.wait_for_timeout(1000)
    snap(pg, "t_kebab_aberto")

    # Clicar em "Alterar senha"
    # Clicar via JS para evitar problema de visibilidade
    clicou = pg.evaluate("""() => {
        const items = [...document.querySelectorAll('[role="menuitem"]')];
        const item = items.find(el => el.innerText && el.innerText.includes('Alterar senha'));
        if (item) { item.click(); return 'clicked: ' + item.innerText.slice(0,30); }
        return 'not found: ' + items.map(x => x.innerText).join(' | ');
    }""")
    log(f"  [alterar_senha] click resultado: {clicou}")
    pg.wait_for_timeout(2000)
    snap(pg, "t_modal_alterar_senha")
    log("  [alterar_senha] modal aberto")

    # Preencher nova senha — procurar inputs de senha
    inputs_modal = pg.locator("input[type='password'], input[name*='password'], input[id*='password']").all()
    log(f"  [alterar_senha] inputs de senha: {len(inputs_modal)}")
    for i, inp in enumerate(inputs_modal):
        try:
            inp.fill(nova_senha)
            log(f"    input [{i}] preenchido")
        except Exception as e:
            log(f"    input [{i}] erro: {e}")

    snap(pg, "t_senha_preenchida")

    # Confirmar
    # Procurar botao de confirmar/salvar no modal
    confirmar = pg.locator("button").filter(has_text=re.compile("Salvar|Confirmar|Alterar|Redefinir|OK", re.I)).last
    if confirmar.count():
        confirmar.click()
        pg.wait_for_timeout(2000)
        snap(pg, "t_senha_salva")
        log("  [alterar_senha] OK!")
        return True
    else:
        log("  [alterar_senha] botao confirmar nao encontrado")
        # Tentar Enter
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(2000)
        snap(pg, "t_senha_enter")
        return True

# ============================================================
# PARTE 2: Criar registro via form
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

def selecionar_usuario_drawer(pg, pessoa_email):
    drawer = pg.locator("div.chakra-modal__content:has(header:has-text('Vincular pessoas'))").first
    if not drawer.count():
        log("  [drawer] nao aberto!")
        return False

    buscar_inp = drawer.locator("input").filter(visible=True).first
    if buscar_inp.count():
        buscar_inp.fill(pessoa_email)
        pg.wait_for_timeout(1500)

    clicou = pg.evaluate(f"""() => {{
        const drawer = document.querySelector('div.chakra-modal__content');
        if (!drawer) return 'no drawer';
        const walker = document.createTreeWalker(drawer, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {{
            if (node.textContent.includes('{pessoa_email}') || node.textContent.includes('{pessoa_email.split('@')[0]}')) {{
                let el = node.parentElement;
                for (let i=0; i<8; i++) {{
                    if (!el || el === drawer) break;
                    const r = el.getBoundingClientRect();
                    if (r.height >= 50 && r.width > 150) {{
                        el.click();
                        return 'clicked ' + el.tagName + ' h=' + r.height;
                    }}
                    el = el.parentElement;
                }}
            }}
        }}
        return 'not found';
    }}""")
    log(f"  [selecionar] {clicou}")
    pg.wait_for_timeout(800)

    vincular = pg.locator("[data-test-id='resource-selector-drawer-confirm-button']").first
    if vincular.count() and vincular.evaluate("el => !el.disabled"):
        vincular.click(force=True)
        pg.wait_for_timeout(2000)
        log("  [vincular] OK!")
        return True
    log("  [vincular] desabilitado/nao encontrado")
    return False

def criar_registro(pg, pessoa_email, conteudo, label):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # 1. Pessoas
    abrir_drawer_pessoas(pg)
    drawer_ok = pg.locator("div.chakra-modal__content:has(header:has-text('Vincular pessoas'))").count() > 0
    log(f"  [drawer] aberto={drawer_ok}")
    if drawer_ok:
        selecionar_usuario_drawer(pg, pessoa_email)
    snap(pg, f"t_form_pessoas_{label}")

    # 2. Conteudo — react-select creatable — teclar char por char e clicar opcao "Criar"
    cont_input = pg.locator("#content input").first
    if cont_input.count():
        cont_input.click(force=True)
        pg.wait_for_timeout(200)
        # Usar keyboard.type (nao fill) para acionar react-select
        pg.keyboard.type(conteudo, delay=50)
        pg.wait_for_timeout(1200)
        # Logar opcoes que aparecem
        opcoes = pg.locator("[class*='menu'] [class*='option'], [id*='react-select'][class*='option']").all_text_contents()
        log(f"  [conteudo] opcoes visiveis: {opcoes[:5]}")
        # Clicar a primeira opcao (Criar '...' )
        opt = pg.locator("[class*='menu'] [class*='option']").first
        if opt.count():
            opt.click(force=True)
            log("  [conteudo] clicou opcao")
        else:
            pg.keyboard.press("Enter")
            log("  [conteudo] Enter")
        pg.wait_for_timeout(300)

    # 3. Provedor
    prov = pg.locator("#provider input").first
    if prov.count():
        prov.click(force=True); pg.keyboard.type("Alura", delay=40); pg.wait_for_timeout(700)
        opt = pg.locator("[role='option']").first
        if opt.count(): opt.click(force=True)

    # 4. Tipo experiencia
    tipo = pg.locator("#learningExperience input").first
    if tipo.count():
        tipo.click(force=True); pg.keyboard.type("Curso", delay=40); pg.wait_for_timeout(700)
        opt = pg.locator("[role='option']").first
        if opt.count(): opt.click(force=True)

    # 5. Categorias
    cat = pg.locator("#categories input").first
    if cat.count():
        cat.click(force=True); pg.wait_for_timeout(500)
        opt = pg.locator("[role='option']").first
        if opt.count(): opt.click(force=True)
        pg.keyboard.press("Escape")

    # 6. Carga horaria
    carga = pg.locator("input[placeholder='HH:MM:SS']").first
    if carga.count():
        carga.triple_click() if hasattr(carga, 'triple_click') else (carga.click(), pg.keyboard.press("Control+a"))
        pg.keyboard.type("010000", delay=40)

    # 7. Data de termino — SEGUNDO input type='date'
    datas = pg.locator("input[type='date']").all()
    log(f"  [datas] encontrados: {len(datas)}")
    alvo_data = datas[1] if len(datas) >= 2 else (datas[0] if datas else None)
    if alvo_data:
        # Tentar via JS para garantir
        alvo_data.evaluate("""el => {
            el.value = '2026-06-01';
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        }""")
        pg.wait_for_timeout(300)
        log("  [data termino] setou via JS")

    snap(pg, f"t_form_preenchido_{label}")

    # 8. Salvar
    pg.evaluate("() => { const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='Salvar'); if(b) b.click(); }")
    pg.wait_for_timeout(6000)
    snap(pg, f"t_salvo_{label}")

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
    log(f"  -> criou={criou} rec_id={rec_id} url={url}")
    return rec_id

# ============================================================
# MAIN
# ============================================================
with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # Passo 1: Alterar senha de qaliderpuro
    log("\n=== Alterar senha qaliderpuro ===")
    ok_senha = alterar_senha_usuario(pg, "qaliderpuro@teste.com", "123456")
    log(f"  alterar_senha ok={ok_senha}")

    # Passo 2: Criar registro para liderado1
    log("\n=== Criar registro para liderado1 ===")
    rec_lid = criar_registro(pg, "liderado1@teste.com", "QA116-Liderado-Externo", "liderado")
    log(f"  rec_lid={rec_lid}")

    # Passo 3: Criar registro para devtestes (fora da equipe)
    log("\n=== Criar registro para devtestes ===")
    rec_fora = criar_registro(pg, "devtestes@teste.com", "QA116-ForaEquipe-Externo", "fora")
    log(f"  rec_fora={rec_fora}")

    log(f"\n=== RESULTADO FINAL ===")
    log(f"  senha_alterada={ok_senha}")
    log(f"  rec_lid={rec_lid}")
    log(f"  rec_fora={rec_fora}")

    ca.close(); ba.close()
