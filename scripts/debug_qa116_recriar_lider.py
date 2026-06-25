# -*- coding: utf-8 -*-
"""Recriar qaliderpuro com senha conhecida (123456) + reconfigurar perfil e organograma."""
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
LIDERADO_ID = 4298605  # liderado1@teste.com

log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

def dispensar(pg):
    tw.dispensar_nps(pg)
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

def excluir_usuario(pg, email):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    linha = pg.locator("tr").filter(has_text=email).first
    if not linha.count():
        log(f"  [excluir] usuario {email} nao encontrado")
        return False

    kebab = linha.locator("button").last
    kebab_box = kebab.bounding_box()
    pg.mouse.click(kebab_box['x'] + kebab_box['width']/2, kebab_box['y'] + kebab_box['height']/2)
    pg.wait_for_timeout(1000)

    # Clicar em Excluir
    excluir_box = pg.evaluate("""() => {
        const items = [...document.querySelectorAll('[role="menuitem"]')];
        const item = items.find(el => el.innerText && el.innerText.includes('Excluir'));
        return item ? item.getBoundingClientRect() : null;
    }""")
    if not excluir_box:
        log("  [excluir] item Excluir nao encontrado")
        return False

    cx = excluir_box['x'] + excluir_box['width']/2
    cy = excluir_box['y'] + excluir_box['height']/2
    pg.mouse.click(cx, cy)
    pg.wait_for_timeout(2000)
    snap(pg, f"recriar_excluir_{email.split('@')[0][:10]}")

    # Confirmar dialogo de exclusao
    # Pode ser um confirm nativo ou modal chakra
    try:
        pg.on("dialog", lambda d: d.accept())
    except: pass

    # Verificar se apareceu modal de confirmacao
    modal = pg.locator(".chakra-modal__content").first
    if modal.count():
        confirmar = modal.locator("button").filter(has_text=re.compile("Confirmar|Excluir|Sim|OK", re.I)).first
        if confirmar.count():
            confirmar.click()
            pg.wait_for_timeout(2000)
    else:
        # Tentar pressionar Enter para confirmar
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(2000)

    snap(pg, f"recriar_excluido_{email.split('@')[0][:10]}")
    log(f"  [excluir] {email} -> tentou excluir")
    return True

def criar_usuario(pg, nome, email, senha, funcao=""):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)
    snap(pg, f"recriar_form_new_{email.split('@')[0][:10]}")

    # Preencher formulario
    nome_parts = nome.split(" ", 1)
    first_name = nome_parts[0]
    last_name = nome_parts[1] if len(nome_parts) > 1 else ""

    for sel, val in [
        ("input[id*='first_name'], input[name*='first_name']", first_name),
        ("input[id*='last_name'], input[name*='last_name']", last_name),
        ("input[type='email'], input[id*='email']", email),
        ("input[type='password'], input[id*='password']", senha),
    ]:
        inp = pg.locator(sel).first
        if inp.count():
            inp.fill(val)
            log(f"  [criar] {sel[:20]} = {val[:20]}")

    snap(pg, f"recriar_form_preenchido_{email.split('@')[0][:10]}")

    # Salvar
    pg.evaluate("() => { const b=[...document.querySelectorAll('button')].find(b=>b.innerText.includes('Salvar')); if(b) b.click(); }")
    pg.wait_for_timeout(5000)
    snap(pg, f"recriar_criado_{email.split('@')[0][:10]}")

    url = pg.url
    log(f"  [criar] url={url}")
    m = re.search(r"/users/(\d+)", url)
    uid = int(m.group(1)) if m else None
    log(f"  [criar] uid={uid}")
    return uid

def configurar_perfil_gestor_turma(pg, user_id):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{user_id}/edit", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    # Marcar SOMENTE Gestor de Turma — desmarcar Admin e Instrutor se marcados
    resultado = pg.evaluate("""() => {
        const admin_chk = document.querySelector('#user_profile_settings_admin');
        const instr_chk = document.querySelector('#user_profile_settings_instructor');
        const gest_chk = document.querySelector('#user_profile_settings_manager_class');
        const log = [];

        // Desmarcar admin se estiver marcado
        if (admin_chk && admin_chk.checked) {
            admin_chk.click();
            log.push('desmarcou admin');
        }
        // Desmarcar instrutor se estiver marcado
        if (instr_chk && instr_chk.checked) {
            instr_chk.click();
            log.push('desmarcou instrutor');
        }
        // Marcar Gestor de Turma se nao estiver
        if (gest_chk && !gest_chk.checked) {
            gest_chk.click();
            log.push('marcou gestor_turma');
        } else {
            log.push('gestor_turma ja marcado');
        }
        return log;
    }""")
    log(f"  [perfil] {resultado}")
    pg.wait_for_timeout(500)

    # Salvar
    pg.evaluate("() => { const b=[...document.querySelectorAll('input[type=submit], button[type=submit], button')].find(b=>b.innerText&&b.innerText.includes('Salvar')); if(b) b.click(); }")
    pg.wait_for_timeout(3000)
    snap(pg, f"recriar_perfil_salvo_{user_id}")
    log(f"  [perfil] salvo para {user_id}")

def configurar_organograma(pg, liderado_id, lider_id, lider_nome):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{liderado_id}/edit", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    dispensar(pg)

    resultado = pg.evaluate(f"""() => {{
        const inp = document.querySelector('#professional_manager_id');
        const name_inp = document.querySelector('#manager_name');
        if (inp && name_inp) {{
            inp.value = '{lider_id}';
            name_inp.value = '{lider_nome}';
            ['input', 'change'].forEach(evt => {{
                inp.dispatchEvent(new Event(evt, {{bubbles: true}}));
                name_inp.dispatchEvent(new Event(evt, {{bubbles: true}}));
            }});
            return 'OK manager_id=' + inp.value;
        }}
        return 'inputs nao encontrados: manager_id=' + !!inp + ' name=' + !!name_inp;
    }}""")
    log(f"  [organograma] {resultado}")

    pg.evaluate("() => { const b=[...document.querySelectorAll('input[type=submit], button[type=submit], button')].find(b=>b.innerText&&b.innerText.includes('Salvar')); if(b) b.click(); }")
    pg.wait_for_timeout(3000)
    snap(pg, f"recriar_organograma_salvo_{liderado_id}")
    log(f"  [organograma] liderado {liderado_id} -> lider {lider_id}")

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # Passo 1: Excluir qaliderpuro antigo
    log("\n=== Passo 1: Excluir qaliderpuro antigo ===")
    ok = excluir_usuario(pg, "qaliderpuro@teste.com")
    log(f"  excluir ok={ok}")
    pg.wait_for_timeout(2000)

    # Passo 2: Criar qaliderpuro novo com senha 123456
    log("\n=== Passo 2: Criar qaliderpuro novo ===")
    novo_id = criar_usuario(pg, "QALider Puro116", "qaliderpuro@teste.com", "123456")
    log(f"  novo_id={novo_id}")

    if novo_id:
        # Passo 3: Configurar como Gestor de Turma
        log("\n=== Passo 3: Configurar como Gestor de Turma ===")
        configurar_perfil_gestor_turma(pg, novo_id)

        # Passo 4: Reconfigurar organograma (liderado1 -> qaliderpuro)
        log("\n=== Passo 4: Reconfigurar organograma ===")
        configurar_organograma(pg, LIDERADO_ID, novo_id, "QALider Puro116")

        # Verificar via API
        r = pg.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/professionals/{LIDERADO_ID}", headers={"Accept":"application/json"})
        if r.status == 200:
            data = r.json().get("data",{}).get("professional",{})
            log(f"  liderado1 manager_id={data.get('manager_id')} (esperado {novo_id})")

        log(f"\n=== RESULTADO ===")
        log(f"  Novo qaliderpuro ID: {novo_id}")
        log(f"  Liderado1 configurado como liderado do novo qaliderpuro")
        snap(pg, "recriar_estado_final")
    else:
        log("  FALHOU criar usuario")

    ca.close(); ba.close()
