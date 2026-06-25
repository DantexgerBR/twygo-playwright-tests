# -*- coding: utf-8 -*-
"""Debug G — setup final: marcar Gestor de turma, verificar login, criar registros."""
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

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # 1. Marcar "Gestor de turma" no qaliderpuro via checkbox
    log("\n--- 1. Marcar Gestor de turma no qaliderpuro ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDER_PURO_ID}/edit", wait_until="domcontentloaded", timeout=15000)
    dispensar(pg); pg.wait_for_timeout(2000)

    # Marcar o checkbox via seletor confirmado
    chk_gestor = pg.locator("#user_profile_settings_manager_class").first
    if chk_gestor.count():
        is_checked = chk_gestor.is_checked()
        log(f"  Gestor de turma checked antes: {is_checked}")
        if not is_checked:
            chk_gestor.check()
            pg.wait_for_timeout(300)
            log(f"  Gestor de turma marcado: {chk_gestor.is_checked()}")
    else:
        log("  checkbox gestor não encontrado!")

    # Desmarcar Admin e Instrutor se marcados
    for chk_id in ["user_profile_settings_admin", "user_profile_settings_instructor"]:
        chk = pg.locator(f"#{chk_id}").first
        if chk.count() and chk.is_checked():
            chk.uncheck()
            log(f"  Desmarcou {chk_id}")

    snap(pg, "g_lider_perfis")

    # Salvar
    pg.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=5000)
    pg.wait_for_timeout(3000)
    log(f"  url: {pg.url}")
    snap(pg, "g_lider_salvo")

    # 2. Verificar login com senha padrão e alternativas
    log("\n--- 2. Verificar login do líder puro ---")
    bd, cd, pg_l = tw.nova_pagina(p)

    for senha in ["123456", "twygoqa2026", "", "Twygo@123"]:
        pg_l.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
        pg_l.fill("#user_email", "qaliderpuro@teste.com")
        pg_l.fill("#user_password", senha if senha else "")
        pg_l.click("#user_submit")
        try: pg_l.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        pg_l.wait_for_timeout(1500)
        url_l = pg_l.url
        logou = "/login" not in url_l and "/users/login" not in url_l
        log(f"  senha='{senha}': url={url_l} logou={logou}")
        if logou:
            snap(pg_l, "g_lider_logado")
            break

    cd.close(); bd.close()

    # 3. Se não logou, recriar o usuário com campo de senha
    log("\n--- 3. Recriar qaliderpuro com senha definida ---")
    # Primeiro deletar o existente via UI (inativar/excluir)
    # Ou: atualizar via form antigo do Rails que pode ter campo de senha

    # Verificar se há campo senha na criação de NOVO usuário
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/new", wait_until="domcontentloaded", timeout=15000)
    dispensar(pg); pg.wait_for_timeout(2000)
    campos_senha = pg.evaluate("""() => {
        return [...document.querySelectorAll('input[type="password"], input[name*="password"]')].map(i => ({
            type: i.type, name: i.name, id: i.id, placeholder: i.placeholder
        }));
    }""")
    log(f"  Campos senha no form new: {campos_senha}")

    # Também verificar se há aba "Senha" ou campo específico
    tabs = pg.locator("[role='tab'], .chakra-tabs__tab, .nav-tab, a.tab").all_text_contents()
    log(f"  Abas: {tabs}")
    snap(pg, "g_novo_user_form")

    # 4. Tentar criar registros via UI (independente do login do líder)
    log("\n--- 4. Criar registro para liderado1 via UI ---")

    # Ir para records/new e capturar rede
    net_reqs = []
    pg.on("request", lambda r: net_reqs.append({
        "method": r.method,
        "url": r.url.split("twygoead.com")[-1][:80],
        "post": r.post_data[:500] if r.post_data else None,
    }) if r.method in ("POST","PUT","PATCH") and "/records" in r.url else None)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # Clicar no campo Pessoas (força)
    pg.evaluate("""() => {
        // Encontrar o botão ou área clicável do campo Pessoas
        const container = document.querySelector('[data-test-id="people-selector-hidden-input"]');
        if (container) {
            const parent = container.parentElement;
            const clickable = parent.querySelector('button, .chakra-input, input:not([type="hidden"])');
            if (clickable) clickable.click();
            else parent.click();
        }
    }""")
    pg.wait_for_timeout(2000)
    snap(pg, "g_form_pessoas_click")

    modal = pg.locator("[role='dialog']").filter(visible=True).first
    log(f"  Modal aberto: {modal.count() > 0}")
    if modal.count():
        modal_text = modal.inner_text()
        log(f"  Modal texto: {modal_text[:300]}")
        snap(pg, "g_modal_pessoas")

        # Buscar liderado1
        search = modal.locator("input").first
        if search.count():
            search.fill("liderado1")
            pg.wait_for_timeout(1500)

        snap(pg, "g_modal_pesquisado")

        # Tentar selecionar o primeiro resultado
        # Os itens têm avatar circular com iniciais e texto do nome/email
        items = modal.locator("[class*='chakra-checkbox'], input[type='checkbox']").all()
        log(f"  Itens/checkboxes no modal: {len(items)}")

        # Tentar clicar no item liderado1
        liderado_item = modal.locator("text=liderado1").first
        if liderado_item.count() == 0:
            liderado_item = modal.locator("text=liderado 1").first
        if liderado_item.count():
            # Clicar no checkbox pai
            chk_pai = liderado_item.locator("xpath=ancestor::label[1]//input | xpath=../input").first
            if chk_pai.count():
                chk_pai.click(force=True)
                pg.wait_for_timeout(500)
            else:
                liderado_item.click(force=True)
                pg.wait_for_timeout(500)
            log("  Clicou em liderado1")
        snap(pg, "g_modal_selecionado")

        # Capturar botões do modal
        btns_modal = modal.locator("button").all_text_contents()
        log(f"  Botões modal: {btns_modal}")

        # Clicar no botão de confirmação (geralmente o último)
        btn_confirm = modal.locator("button").filter(has_text=re.compile(r"Associar|Vincular|Salvar|OK|Confirmar", re.I)).first
        if btn_confirm.count():
            btn_confirm.click()
            pg.wait_for_timeout(2000)
            log("  Clicou no botão de confirmação")
        else:
            # Usar o último botão
            all_btns = modal.locator("button").all()
            if len(all_btns) > 1:
                all_btns[-1].click()
                pg.wait_for_timeout(2000)
                log("  Clicou no último botão")

    snap(pg, "g_form_apos_modal")

    # Capturar qualquer POST que aconteceu
    log(f"  Requisições de rede capturadas: {net_reqs}")

    ca.close(); ba.close()
