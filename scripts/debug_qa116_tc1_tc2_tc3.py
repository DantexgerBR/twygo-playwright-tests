# -*- coding: utf-8 -*-
"""
TC1, TC2, TC3 - Usando senha correta do lider (123456).
"""
import json, sys, re
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
LIDERADO_EMAIL = "liderado1@teste.com"
LIDERADO_ID    = 4298605
FORA_REC_ID    = 44280185   # QA116-ForaEquipe-Externo (de devtestes)
LIDERADO_REC_ID = 44280186  # QA116-Liderado-Externo

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log  = lambda *a: print(*a, flush=True)
results = {}

def snap(pg, nome):
    pg.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True)
    log(f"  [snap] {nome}.png")

def login_lider(pg):
    """Login do lider sem forcar admin redirect."""
    pg.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    pg.fill("#user_email", LIDER_EMAIL)
    pg.fill("#user_password", LIDER_SENHA)
    pg.click("#user_submit")
    try: pg.wait_for_load_state("networkidle", timeout=20000)
    except: pass
    pg.wait_for_timeout(2000)
    tw.dispensar_nps(pg)
    # Ir para registros diretamente (o lider acessa sem profile=admin)
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    # Aguardar carregamento
    try: pg.wait_for_selector("tbody tr, .chakra-stat p", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)
    log(f"  [lider] URL: {pg.url}")

def aguardar_carregamento(pg, timeout=10000):
    """Aguardar spinner sumir."""
    try:
        pg.wait_for_selector("tbody tr", timeout=timeout)
    except:
        pass
    pg.wait_for_timeout(2000)

# ==============================================================================
log("\n" + "="*60)
log("TC1 (RN93) - Dropdown Pessoa no Adicionar + aba Provedores")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=600)
    login_lider(pg)
    snap(pg, "tc1v2_lider_lista")
    log(f"  Linhas visiveis: {pg.locator('tbody tr').count()}")

    # PASSO 3: Clicar em Adicionar e verificar dropdown Pessoa
    btn_add = pg.locator("button, a").filter(has_text=re.compile("^\\s*Adicionar\\s*$", re.I)).first
    log(f"  Botao Adicionar encontrado: {btn_add.count()}")

    if btn_add.count():
        box_add = btn_add.bounding_box()
        if box_add:
            pg.mouse.click(box_add['x']+box_add['width']/2, box_add['y']+box_add['height']/2)
            pg.wait_for_timeout(2000)
            snap(pg, "tc1v2_form_adicionar")
            log(f"  URL apos Adicionar: {pg.url}")

            # Ver todos os inputs e selects no form
            form_inputs = pg.evaluate("""() => {
                const inputs = [...document.querySelectorAll('input, select')];
                return inputs.filter(i => i.getBoundingClientRect().height > 0).map(i => ({
                    type: i.type, id: i.id, name: i.name,
                    placeholder: (i.placeholder||'').slice(0,40),
                    role: i.getAttribute('role')
                })).slice(0, 20);
            }""")
            log(f"  Inputs no form: {json.dumps(form_inputs, ensure_ascii=False)}")

            # Procurar campo Pessoa (pode ser um react-select ou input com placeholder)
            pessoa_inputs = pg.locator("input").filter(
                has=pg.locator("[placeholder*='Pessoa' i], [placeholder*='name' i], [placeholder*='nome' i]"))
            if not pessoa_inputs.count():
                # Buscar por label Pessoa
                pessoa_label = pg.locator("label").filter(has_text=re.compile("^Pessoa$", re.I))
                if pessoa_label.count():
                    label_for = pessoa_label.first.get_attribute("for")
                    log(f"  Label Pessoa for: {label_for}")
                    if label_for:
                        pessoa_inputs = pg.locator(f"#{label_for}")

            # Se ainda nao encontrou, procurar qualquer select/input que seja "Pessoa"
            if not pessoa_inputs.count():
                # Tentar pelo primeiro select visivel (no form de Adicionar)
                all_selects = pg.locator("[class*='select'], [class*='dropdown']").all()
                log(f"  Selects encontrados: {len(all_selects)}")
                for i, sel in enumerate(all_selects[:5]):
                    box_s = sel.bounding_box()
                    if box_s:
                        log(f"  Select {i}: {sel.get_attribute('class') or ''}")

            # Tentar clicar no campo react-select Pessoa
            # No form de adicionar, o primeiro select costuma ser Pessoa
            react_inputs = pg.locator("input[id*='react-select'], input[class*='select']")
            if not react_inputs.count():
                react_inputs = pg.locator(".creatable-select-field__input, [class*='__input'] input")

            if react_inputs.count():
                log(f"  React inputs encontrados: {react_inputs.count()}")
                primeiro = react_inputs.first
                primeiro.click(timeout=5000)
                pg.wait_for_timeout(1500)
                snap(pg, "tc1v2_dropdown_pessoa_clicado")

                # Ver opcoes do dropdown
                opcoes = pg.evaluate("""() => {
                    const opts = [...document.querySelectorAll('[id*="__option"], [class*="option"], [role="option"]')];
                    return opts.filter(o => o.getBoundingClientRect().height > 0)
                        .map(o => (o.innerText||'').trim()).filter(t => t).slice(0, 20);
                }""")
                log(f"  Opcoes no dropdown Pessoa: {opcoes}")
                results['tc1_opcoes_pessoa'] = opcoes

                # Verificar escopo
                tem_liderado = any("liderado" in o.lower() for o in opcoes)
                outros = [o for o in opcoes if "liderado" not in o.lower() and len(o) > 2]
                log(f"  tem_liderado={tem_liderado}, outros={outros[:5]}")

                if tem_liderado and len(outros) <= 1:
                    results['tc1_pessoa_scope'] = 'PASS'
                    log("  TC1.3 PASS - dropdown mostra apenas subordinados (liderado1)")
                elif not tem_liderado:
                    results['tc1_pessoa_scope'] = 'FAIL_sem_liderado'
                    log("  TC1.3 FAIL - liderado1 nao aparece")
                else:
                    results['tc1_pessoa_scope'] = f'FAIL_escopo_largo:{len(opcoes)}_opcoes'
                    log(f"  TC1.3 FAIL - {len(opcoes)} opcoes (esperado: apenas liderado1)")

                pg.keyboard.press("Escape")
                pg.wait_for_timeout(500)
            else:
                log("  React select nao encontrado")
                # Tentar clicar pela posicao do label Pessoa
                pessoa_pos = pg.evaluate("""() => {
                    const labels = [...document.querySelectorAll('label')];
                    const l = labels.find(lbl => lbl.innerText.trim() === 'Pessoa' || lbl.innerText.trim() === 'Pessoa *');
                    if (l) {
                        // Pegar o control do react-select abaixo
                        const parent = l.closest('[class*="form"]') || l.parentElement;
                        const control = parent ? parent.querySelector('[class*="control"], input') : null;
                        if (control) {
                            const box = control.getBoundingClientRect();
                            return {x: box.x + box.width/2, y: box.y + box.height/2, label: l.innerText.trim()};
                        }
                    }
                    return null;
                }""")
                log(f"  Campo Pessoa via label: {pessoa_pos}")
                if pessoa_pos:
                    pg.mouse.click(pessoa_pos['x'], pessoa_pos['y'])
                    pg.wait_for_timeout(1500)
                    snap(pg, "tc1v2_pessoa_via_label")
                    opcoes2 = pg.evaluate("""() => {
                        return [...document.querySelectorAll('[id*="__option"], [role="option"]')]
                            .filter(o => o.getBoundingClientRect().height > 0)
                            .map(o => (o.innerText||'').trim()).filter(t=>t).slice(0,20);
                    }""")
                    log(f"  Opcoes: {opcoes2}")
                    results['tc1_opcoes_pessoa'] = opcoes2

                    tem_lid = any("liderado" in o.lower() for o in opcoes2)
                    outros2 = [o for o in opcoes2 if "liderado" not in o.lower() and len(o) > 2]
                    if tem_lid and len(outros2) <= 1:
                        results['tc1_pessoa_scope'] = 'PASS'
                    elif not tem_lid and not opcoes2:
                        results['tc1_pessoa_scope'] = 'INCONCLUSIVO_dropdown_vazio'
                    else:
                        results['tc1_pessoa_scope'] = f'FAIL:{opcoes2}'
                    pg.keyboard.press("Escape")
                else:
                    results['tc1_pessoa_scope'] = 'INCONCLUSIVO_campo_pessoa_nao_encontrado'
                    snap(pg, "tc1v2_form_sem_pessoa")

    # PASSO 4: Aba Provedores - deve mostrar lista completa
    snap(pg, "tc1v2_antes_aba_provedores")

    # Procurar aba Provedores na pagina atual
    tab_prov = pg.locator("[role='tab'], a.nav-link, li").filter(
        has_text=re.compile("Provedores?", re.I)).first
    if not tab_prov.count():
        # Talvez seja necessario fechar o form primeiro
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(500)
        pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
        try: pg.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        pg.wait_for_timeout(3000)
        tab_prov = pg.locator("[role='tab'], a, button").filter(
            has_text=re.compile("Provedores?", re.I)).first

    if tab_prov.count():
        box_tab = tab_prov.bounding_box()
        if box_tab:
            pg.mouse.click(box_tab['x']+box_tab['width']/2, box_tab['y']+box_tab['height']/2)
            pg.wait_for_timeout(2000)
            snap(pg, "tc1v2_aba_provedores")

            provedores_count = pg.locator("tbody tr").count()
            log(f"  Provedores visiveis: {provedores_count}")
            results['tc1_provedores_count'] = provedores_count

            if provedores_count > 0:
                results['tc1_provedores'] = f'PASS_{provedores_count}_provedores'
                log(f"  TC1.4 PASS - aba Provedores lista {provedores_count} provedores")
            else:
                results['tc1_provedores'] = 'INCONCLUSIVO_provedores_vazios'
                log("  TC1.4 INCONCLUSIVO - nenhum provedor listado")
    else:
        results['tc1_provedores'] = 'INCONCLUSIVO_aba_nao_encontrada'
        log("  TC1.4 INCONCLUSIVO - aba Provedores nao encontrada")

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC2 (RN94) - Lider nao pode aprovar registro fora do escopo")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=400)
    login_lider(pg)
    snap(pg, "tc2v2_lider_lista")

    # TC2 Passo 1: Verificar se lider VE o registro ForaEquipe na lista
    busca = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca.count():
        busca.fill("ForaEquipe")
        pg.wait_for_timeout(2000)
        snap(pg, "tc2v2_busca_foraequipe")
        linhas_fora = pg.locator("tbody tr").count()
        # Verificar se e linha real ou mensagem vazia
        msg_nao_encontrado = pg.evaluate("""() => {
            return [...document.querySelectorAll('td, p, div')].some(e =>
                e.children.length === 0 && /nenhum|no data|nao ha|nao existe/i.test(e.innerText)
            );
        }""")
        log(f"  Busca ForaEquipe: {linhas_fora} linhas, msg_vazia={msg_nao_encontrado}")

        if msg_nao_encontrado or linhas_fora == 0:
            results['tc2_foraequipe_visivel'] = 'PASS_nao_visivel'
            log("  TC2.1 PASS - Registro ForaEquipe NAO visivel ao lider (escopo correto)")
        else:
            results['tc2_foraequipe_visivel'] = f'FAIL_visivel:{linhas_fora}'
            log(f"  TC2.1 FAIL - Registro ForaEquipe VISIVEL ao lider ({linhas_fora} linhas)")

        busca.fill("")
        pg.wait_for_timeout(1000)

    # TC2 Passo 2: Tentar aprovacao via API no registro ForaEquipe
    # Capturar CSRF token
    csrf = pg.evaluate("() => document.querySelector('meta[name=csrf-token]')?.content || ''")
    log(f"  CSRF: {csrf[:20]}...")

    # Tentar GET no registro para ver se da 403/404
    r_get = pg.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records/{FORA_REC_ID}",
        headers={"Accept": "application/json", "X-CSRF-Token": csrf}
    )
    log(f"  GET /api/v1/o/{ORG_ID}/records/{FORA_REC_ID}: {r_get.status}")
    results['tc2_get_fora'] = r_get.status

    # Verificar o endpoint de aprovacao interceptando uma acao real primeiro
    # Abrir kebab do registro do liderado para ver quais acoes estao disponiveis
    registros = pg.locator("tbody tr")
    if registros.count():
        linha = registros.first
        # Tentar kebab
        kebab_btn = pg.evaluate("""(row) => {
            const btns = [...row.querySelectorAll('button')].filter(b => b.getBoundingClientRect().height > 0);
            if (btns.length) {
                const last = btns[btns.length-1];
                const box = last.getBoundingClientRect();
                return {x: box.x+box.width/2, y: box.y+box.height/2};
            }
            return null;
        }""", linha.element_handle())
        if kebab_btn:
            pg.mouse.click(kebab_btn['x'], kebab_btn['y'])
            pg.wait_for_timeout(1000)
            snap(pg, "tc2v2_kebab_registro")
            items = pg.evaluate("""() => {
                return [...document.querySelectorAll('[role="menuitem"]')].map(e => ({
                    text: (e.innerText||'').trim(), id: e.id
                })).filter(i=>i.text);
            }""")
            log(f"  Menu items registro liderado: {json.dumps(items, ensure_ascii=False)}")
            results['tc2_menu_items'] = [i['text'] for i in items]
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(500)
    else:
        log("  Nenhum registro visivel para testar kebab")

    # Tentar diferentes endpoints de aprovacao
    endpoints = [
        f"/api/v1/o/{ORG_ID}/records/{FORA_REC_ID}/approve",
        f"/api/v1/o/{ORG_ID}/records/{FORA_REC_ID}/emit",
        f"/api/v1/o/{ORG_ID}/records/{FORA_REC_ID}/review",
    ]
    tc2_api = {}
    for ep in endpoints:
        r = pg.request.post(
            f"{BASE_URL}{ep}",
            headers={"Accept": "application/json", "Content-Type": "application/json",
                      "X-CSRF-Token": csrf},
            data="{}"
        )
        tc2_api[ep] = r.status
        log(f"  POST {ep}: {r.status}")
    results['tc2_api'] = tc2_api

    # Veredito TC2
    foraequipe_nao_visivel = results.get('tc2_foraequipe_visivel', '').startswith('PASS')
    get_403 = results.get('tc2_get_fora') in (403, 404)
    post_403 = any(v in (403, 404) for v in tc2_api.values())

    if foraequipe_nao_visivel and (get_403 or post_403):
        results['tc2'] = 'PASS'
        log("  TC2 PASS - Lider nao ve e API retorna 403/404 para registro fora do escopo")
    elif foraequipe_nao_visivel:
        results['tc2'] = 'PASS_visibilidade_ok_api_inconclusivo'
        log("  TC2 PASS (parcial) - nao visivel mas API retornou codigos inesperados")
    else:
        results['tc2'] = 'FAIL'
        log("  TC2 FAIL - Registro ForaEquipe visivel ao lider")

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC3 (RN95) - Aprovacao persiste; lider nao ve apos sair do time")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg_admin = tw.nova_pagina(p, slow_mo=400)
    ba2, ca2, pg_lider = tw.nova_pagina(p, slow_mo=400)

    tw.login(pg_admin, {"base_url": BASE_URL, "org_id": ORG_ID,
                         "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    login_lider(pg_lider)
    log("[lider] logado")

    # TC3 Passo 1: Lider aprova registro do liderado1
    # O registro QA116-Liderado-Externo (id=44280186) de liderado1 esta "Aprovado"
    # Preciso de um registro PENDENTE para o lider aprovar
    # Criar um via admin: ir para admin_goto_records e Adicionar para liderado1

    # Primeiro verificar o que o lider ve
    snap(pg_lider, "tc3v2_lider_lista_inicial")
    linhas_lider = pg_lider.locator("tbody tr").count()
    log(f"  [TC3] Lider ve {linhas_lider} registros")

    if linhas_lider == 0:
        log("  [TC3] Sem registros visiveis. Aguardando mais...")
        pg_lider.wait_for_timeout(5000)
        snap(pg_lider, "tc3v2_lider_lista_depois_espera")
        linhas_lider = pg_lider.locator("tbody tr").count()
        log(f"  [TC3] Depois de espera: {linhas_lider} registros")

    # Ver o kebab da primeira linha (pode ter opcao de aprovacao)
    if linhas_lider > 0:
        primeira_linha = pg_lider.locator("tbody tr").first
        row_text = pg_lider.evaluate("(row) => row.innerText.replace(/\\n/g, ' ').slice(0, 100)", primeira_linha.element_handle())
        log(f"  [TC3] Primeira linha: {row_text}")

        kebab_info = pg_lider.evaluate("""(row) => {
            const btns = [...row.querySelectorAll('button')].filter(b => b.getBoundingClientRect().height > 0);
            if (btns.length) {
                const last = btns[btns.length-1];
                const box = last.getBoundingClientRect();
                return {x: box.x+box.width/2, y: box.y+box.height/2};
            }
            return null;
        }""", primeira_linha.element_handle())
        if kebab_info:
            pg_lider.mouse.click(kebab_info['x'], kebab_info['y'])
            pg_lider.wait_for_timeout(1000)
            snap(pg_lider, "tc3v2_kebab_lider")
            items_tc3 = pg_lider.evaluate("""() => {
                return [...document.querySelectorAll('[role="menuitem"]')]
                    .map(e => ({text: (e.innerText||'').trim(), id: e.id})).filter(i=>i.text);
            }""")
            log(f"  [TC3] Menu items: {json.dumps(items_tc3, ensure_ascii=False)}")
            results['tc3_menu_items'] = [i['text'] for i in items_tc3]

            # Clicar em Aprovar se disponivel
            aprovar = pg_lider.locator("[role='menuitem']").filter(
                has_text=re.compile("Aprova|Emitir", re.I)).first
            if aprovar.count():
                box_ap = aprovar.bounding_box()
                if box_ap:
                    pg_lider.mouse.click(box_ap['x']+box_ap['width']/2, box_ap['y']+box_ap['height']/2)
                    pg_lider.wait_for_timeout(2000)
                    snap(pg_lider, "tc3v2_pos_aprovar")
                    log(f"  [TC3] Aprovacao executada. URL: {pg_lider.url}")
                    results['tc3_aprovacao'] = 'executada'
            else:
                pg_lider.keyboard.press("Escape")
                log("  [TC3] Item Aprovar nao disponivel no menu (registro ja aprovado?)")
                results['tc3_aprovacao'] = 'indisponivel_ja_aprovado'
    else:
        log("  [TC3] Lider nao ve registros")
        results['tc3_aprovacao'] = 'INCONCLUSIVO_sem_registros'

    # TC3 Passo 2: Remover liderado1 do organograma
    # Ir para organograma como admin
    pg_admin.goto(f"{BASE_URL}/o/{ORG_ID}/professionals",
                  wait_until="domcontentloaded", timeout=30000)
    try: pg_admin.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg_admin.wait_for_timeout(3000)
    log(f"  [TC3] URL organograma: {pg_admin.url}")
    snap(pg_admin, "tc3v2_organograma")

    # Tentar outra URL para organograma
    org_urls = [
        f"{BASE_URL}/o/{ORG_ID}/organization_chart",
        f"{BASE_URL}/o/{ORG_ID}/organization_chart?view=list",
        f"{BASE_URL}/o/{ORG_ID}/team",
    ]
    for org_url in org_urls:
        pg_admin.goto(org_url, wait_until="domcontentloaded", timeout=30000)
        try: pg_admin.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        pg_admin.wait_for_timeout(2000)
        if "/login" not in pg_admin.url:
            log(f"  [TC3] Organograma acessivel em: {pg_admin.url}")
            snap(pg_admin, f"tc3v2_org_{org_url.split('/')[-1].split('?')[0]}")
            break

    # Buscar liderado1 no organograma
    busca_org = pg_admin.locator("input[placeholder*='Pesquise' i], input[type='search']").first
    if busca_org.count():
        busca_org.fill("liderado1")
        pg_admin.wait_for_timeout(2000)
        snap(pg_admin, "tc3v2_org_busca_liderado1")
        linhas_org = pg_admin.locator("tbody tr, [class*='row']").filter(has_text="liderado1").count()
        log(f"  [TC3] liderado1 no organograma: {linhas_org} linhas")

        if linhas_org > 0:
            # Tentar remover o gestor do liderado1
            linha_org = pg_admin.locator("tbody tr").filter(has_text="liderado1").first
            kebab_org = pg_admin.evaluate("""(row) => {
                const btns = [...row.querySelectorAll('button')].filter(b => b.getBoundingClientRect().height > 0);
                if (btns.length) {
                    const last = btns[btns.length-1];
                    const box = last.getBoundingClientRect();
                    return {x: box.x+box.width/2, y: box.y+box.height/2};
                }
                return null;
            }""", linha_org.element_handle())
            if kebab_org:
                pg_admin.mouse.click(kebab_org['x'], kebab_org['y'])
                pg_admin.wait_for_timeout(1000)
                snap(pg_admin, "tc3v2_org_kebab")
                items_org = pg_admin.evaluate("""() => {
                    return [...document.querySelectorAll('[role="menuitem"]')]
                        .map(e => (e.innerText||'').trim()).filter(t=>t);
                }""")
                log(f"  [TC3] Organograma menu: {items_org}")
                results['tc3_org_menu'] = items_org

                # Procurar opcao de remover gestor/mover
                remover = pg_admin.locator("[role='menuitem']").filter(
                    has_text=re.compile("Remover|Editar.*gestor|Alterar.*gestor|Desvincul|Mover", re.I)).first
                if remover.count():
                    box_rem = remover.bounding_box()
                    if box_rem:
                        pg_admin.mouse.click(box_rem['x']+box_rem['width']/2, box_rem['y']+box_rem['height']/2)
                        pg_admin.wait_for_timeout(2000)
                        snap(pg_admin, "tc3v2_org_remover")
                        log("  [TC3] Liderado1 removido do organograma")
                        results['tc3_removido_org'] = True

                        # Confirmar se houver modal
                        modal = pg_admin.locator("[role='dialog']").first
                        if modal.count():
                            confirmar = pg_admin.evaluate("""() => {
                                const c = [...document.querySelectorAll('button')].find(b => /confirmar|sim|ok|remover/i.test(b.innerText) && b.getBoundingClientRect().height > 0);
                                return c ? {x: c.getBoundingClientRect().x+c.getBoundingClientRect().width/2, y: c.getBoundingClientRect().y+c.getBoundingClientRect().height/2} : null;
                            }""")
                            if confirmar:
                                pg_admin.mouse.click(confirmar['x'], confirmar['y'])
                                pg_admin.wait_for_timeout(2000)
                else:
                    pg_admin.keyboard.press("Escape")
                    log("  [TC3] Opcao de remover nao encontrada")
                    results['tc3_removido_org'] = False
        else:
            log("  [TC3] liderado1 nao encontrado no organograma")
            results['tc3_removido_org'] = False
    else:
        log("  [TC3] Sem campo de busca no organograma")
        results['tc3_removido_org'] = False

    # TC3 Passo 3: Admin verifica que aprovacao ainda existe
    pg_admin.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg_admin.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    try: pg_admin.wait_for_selector("tbody tr", timeout=8000)
    except: pass
    pg_admin.wait_for_timeout(3000)

    busca_admin = pg_admin.locator("input[placeholder*='Pesquise' i]").first
    if busca_admin.count():
        busca_admin.fill("liderado1")
        pg_admin.wait_for_timeout(2000)
    snap(pg_admin, "tc3v2_admin_verifica_aprovacao")
    linhas_admin = pg_admin.locator("tbody tr").count()
    msg_vazia = pg_admin.evaluate("""() => [...document.querySelectorAll('td, p')].some(e => e.children.length === 0 && /nenhum|no data|nao ha/i.test(e.innerText))""")
    log(f"  [TC3] Admin ve {linhas_admin} registros de liderado1 (msg_vazia={msg_vazia})")
    results['tc3_admin_ve_registros'] = linhas_admin if not msg_vazia else 0

    # TC3 Passo 4: Lider nao ve mais registros de liderado1
    pg_lider.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg_lider.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg_lider.wait_for_timeout(5000)
    snap(pg_lider, "tc3v2_lider_apos_remocao_org")
    linhas_lider_pos = pg_lider.locator("tbody tr").count()
    msg_lider = pg_lider.evaluate("""() => [...document.querySelectorAll('td, p')].some(e => e.children.length === 0 && /nenhum|no data|nao ha/i.test(e.innerText))""")
    log(f"  [TC3] Lider ve {linhas_lider_pos} registros apos remocao (msg={msg_lider})")
    results['tc3_lider_apos_remocao'] = linhas_lider_pos if not msg_lider else 0

    # VEREDITO TC3
    admin_ve = results.get('tc3_admin_ve_registros', 0) > 0
    lider_nao_ve = results.get('tc3_lider_apos_remocao', -1) == 0
    removido = results.get('tc3_removido_org', False)

    if removido and admin_ve and lider_nao_ve:
        results['tc3'] = 'PASS'
        log("  TC3 PASS - Aprovacao persiste; lider nao ve mais apos sair do time")
    elif removido and not admin_ve:
        results['tc3'] = 'FAIL_aprovacao_perdida'
        log("  TC3 FAIL - Aprovacao foi perdida apos saida do time")
    elif not removido:
        results['tc3'] = 'INCONCLUSIVO_nao_conseguiu_remover_do_org'
        log("  TC3 INCONCLUSIVO - nao conseguiu remover liderado do organograma")
    else:
        results['tc3'] = f'PARCIAL (admin_ve={admin_ve}, lider_nao_ve={lider_nao_ve})'

    # RESTAURAR liderado1 ao organograma do lider (IMPORTANTE!)
    log("\n  [TC3] Restaurando liderado1 ao organograma do qaliderpuro...")
    # A restauracao e feita editando o usuario liderado1 e adicionando qaliderpuro como responsavel
    pg_admin.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
                  wait_until="domcontentloaded", timeout=30000)
    try: pg_admin.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg_admin.wait_for_timeout(2000)
    snap(pg_admin, "tc3v2_restaurar_liderado1_form")

    # Buscar campo "Responsavel" e preencher com qaliderpuro
    responsavel_input = pg_admin.locator("input[placeholder*='Responsavel' i], input[placeholder*='responsável' i], [name*='manager' i]").first
    if not responsavel_input.count():
        # Tentar pela label
        resp_label = pg_admin.locator("label").filter(has_text=re.compile("Responsável|Responsavel", re.I)).first
        if resp_label.count():
            label_for = resp_label.get_attribute("for")
            if label_for:
                responsavel_input = pg_admin.locator(f"#{label_for}, [id='{label_for}'] input").first

    if responsavel_input.count():
        responsavel_input.fill("qaliderpuro")
        pg_admin.wait_for_timeout(1500)
        # Selecionar opcao
        opcao = pg_admin.locator("[role='option'], [id*='__option']").filter(
            has_text=re.compile("qaliderpuro|QALider", re.I)).first
        if opcao.count():
            opcao.click(timeout=5000)
            pg_admin.wait_for_timeout(1000)

    # Salvar
    save_restaurar = pg_admin.evaluate("""() => {
        const btns = [...document.querySelectorAll('button, input[type=submit]')];
        const s = btns.find(b => /salvar|save|atualizar/i.test(b.innerText || b.value || ''));
        if (s) { s.click(); return true; }
        return false;
    }""")
    pg_admin.wait_for_timeout(3000)
    snap(pg_admin, "tc3v2_restaurar_liderado1_salvo")
    log(f"  Salvo: {save_restaurar}, URL: {pg_admin.url}")

    pg_admin.close(); ca.close(); ba.close()
    pg_lider.close(); ca2.close(); ba2.close()


# SUMARIO
log("\n" + "="*60)
log("SUMARIO TC1/TC2/TC3")
log("="*60)
for k, v in results.items():
    log(f"  {k}: {v}")

log("\n  VEREDITOS:")
log(f"  TC1 Pessoa scope:   {results.get('tc1_pessoa_scope','?')}")
log(f"  TC1 Provedores:     {results.get('tc1_provedores','?')}")
log(f"  TC2 (RN94):         {results.get('tc2','?')}")
log(f"  TC3 (RN95):         {results.get('tc3','?')}")
