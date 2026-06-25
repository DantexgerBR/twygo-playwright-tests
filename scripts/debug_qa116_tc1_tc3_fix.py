# -*- coding: utf-8 -*-
"""
TC1.3 correto (campo Pessoas, nao Provedor)
TC1.4 cross-check admin Provedores
TC3 com endpoint capturado + registro pendente
TC5 cross-check bucket admin
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
LIDERADO_ID    = 4298605
FORA_REC_ID    = 44280185

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log  = lambda *a: print(*a, flush=True)
results = {}

def snap(pg, nome):
    pg.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True)
    log(f"  [snap] {nome}.png")

def login_lider(pg):
    pg.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    pg.fill("#user_email", LIDER_EMAIL)
    pg.fill("#user_password", LIDER_SENHA)
    pg.click("#user_submit")
    try: pg.wait_for_load_state("networkidle", timeout=20000)
    except: pass
    pg.wait_for_timeout(2000)
    tw.dispensar_nps(pg)
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    try: pg.wait_for_selector("tbody tr", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)

def contar_linhas_reais(pg):
    """Conta linhas, retornando 0 se ha apenas mensagem de 'nao ha dados'."""
    count = pg.locator("tbody tr").count()
    if count == 0:
        return 0
    # Verificar se ha mensagem de vazio
    vazio = pg.evaluate("""() => {
        const rows = [...document.querySelectorAll('tbody tr')];
        // Se todas as linhas contem apenas texto de "nao ha dados"
        return rows.every(r => /nenhum|nao ha|no data|sem registro/i.test(r.innerText));
    }""")
    return 0 if vazio else count


# ==============================================================================
log("\n" + "="*60)
log("STEP 1: Capturar endpoint de aprovacao como admin")
log("="*60)

approval_endpoint = None

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=400)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # Criar um registro pendente para liderado1 para ter algo a aprovar
    # Primeiro ver o que ja existe
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    try: pg.wait_for_selector("tbody tr", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)

    busca = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca.count():
        busca.fill("liderado1")
        pg.wait_for_timeout(2000)
        snap(pg, "step1_admin_busca_liderado1")

    linhas_liderado = contar_linhas_reais(pg)
    log(f"  Registros de liderado1: {linhas_liderado}")

    # Ver situacao dos registros
    situacoes = pg.evaluate("""() => {
        return [...document.querySelectorAll('tbody tr')].map(tr => {
            const situacao = tr.querySelector('[class*="badge"], [class*="tag"], td:last-child');
            return {row: tr.innerText.replace(/\\n/g, ' ').slice(0, 80), situacao: situacao?.innerText?.trim() || ''};
        });
    }""")
    log(f"  Situacoes: {json.dumps(situacoes, ensure_ascii=False)}")

    # Precisamos de um registro PENDENTE para testar a aprovacao
    # Criar via Adicionar (form novo)
    log("  Criando registro pendente para liderado1...")
    if busca.count():
        busca.fill("")
        pg.wait_for_timeout(1000)

    btn_add = pg.locator("button").filter(has_text=re.compile("^\\s*\\+ Adicionar\\s*$|^\\s*Adicionar\\s*$", re.I)).first
    if btn_add.count():
        box_add = btn_add.bounding_box()
        if box_add:
            pg.mouse.click(box_add['x']+box_add['width']/2, box_add['y']+box_add['height']/2)
            pg.wait_for_timeout(2000)
            log(f"  URL form: {pg.url}")

            # Preencher campo Pessoas (clicar no icone ou no campo)
            pessoas_area = pg.locator("div").filter(has_text=re.compile("^Adicionar pessoas$")).first
            if not pessoas_area.count():
                # Tentar pelo icone ou container
                pessoas_area = pg.locator("[class*='pessoas'], [placeholder*='Adicionar pessoas' i]").first

            if pessoas_area.count():
                box_p = pessoas_area.bounding_box()
                if box_p:
                    pg.mouse.click(box_p['x']+box_p['width']/2, box_p['y']+box_p['height']/2)
                    pg.wait_for_timeout(2000)
                    snap(pg, "step1_pessoas_clicado")

                    # Ver se abriu drawer/modal
                    drawer = pg.locator("[role='dialog'], [class*='drawer'], [class*='modal']").first
                    if drawer.count():
                        log("  Drawer aberto")
                        # Buscar liderado1 no drawer
                        busca_drawer = drawer.locator("input[type='text'], input[type='search']").first
                        if busca_drawer.count():
                            busca_drawer.fill("liderado1")
                            pg.wait_for_timeout(1500)
                            snap(pg, "step1_drawer_busca")
                            # Clicar na primeira opcao
                            opcao = drawer.locator("[role='option'], [class*='option'], [class*='item']").first
                            if opcao.count():
                                opcao.click(timeout=5000)
                                pg.wait_for_timeout(1000)
                        # Confirmar
                        confirmar = drawer.locator("button").filter(has_text=re.compile("Confirmar|OK|Selecionar|Adicionar", re.I)).first
                        if confirmar.count():
                            confirmar.click(timeout=5000)
                            pg.wait_for_timeout(1000)
                    else:
                        # Sem drawer - pode ser typeahead inline
                        pg.keyboard.type("liderado")
                        pg.wait_for_timeout(1500)
                        snap(pg, "step1_typeahead_liderado")
                        opcao = pg.locator("[role='option']").filter(has_text="liderado").first
                        if opcao.count():
                            opcao.click(timeout=5000)
                            pg.wait_for_timeout(1000)
            else:
                log("  Campo Pessoas nao encontrado")
                snap(pg, "step1_sem_campo_pessoas")

            # Preencher Provedor (obrigatorio)
            provedor_input = pg.locator("#react-select-2-input, [id*='react-select'][id*='2']").first
            if provedor_input.count():
                provedor_input.fill("Alura")
                pg.wait_for_timeout(1000)
                op_prov = pg.locator("[id*='__option']").first
                if op_prov.count():
                    op_prov.click(timeout=3000)
                else:
                    # Criar novo provedor
                    criar = pg.locator("[class*='create']").first
                    if criar.count(): criar.click(timeout=3000)

            # Preencher Conteudo
            conteudo_input = pg.locator("#react-select-3-input, [id*='react-select'][id*='3']").first
            if conteudo_input.count():
                conteudo_input.fill("TC3-Pendente-Test")
                pg.wait_for_timeout(500)
                criar_cont = pg.locator("[class*='create']").first
                if criar_cont.count(): criar_cont.click(timeout=3000)

            # Carga horaria
            carga = pg.locator("#workload_seconds").first
            if carga.count():
                carga.fill("01:00:00")

            snap(pg, "step1_form_preenchido")

            # Salvar
            salvar_btn = pg.evaluate("""() => {
                const btns = [...document.querySelectorAll('button')];
                const s = btns.find(b => b.innerText.trim() === 'Salvar' && b.getBoundingClientRect().height > 0);
                if (s) { const box = s.getBoundingClientRect(); return {x: box.x+box.width/2, y: box.y+box.height/2}; }
                return null;
            }""")
            if salvar_btn:
                pg.mouse.click(salvar_btn['x'], salvar_btn['y'])
                pg.wait_for_timeout(3000)
                snap(pg, "step1_registro_salvo")
                log(f"  URL pos salvar: {pg.url}")
            else:
                log("  Botao Salvar nao encontrado")
    else:
        log("  Botao Adicionar nao encontrado")

    # Agora tentar capturar o endpoint de aprovacao
    # Procurar registro PENDENTE para clicar em rate_review
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    try: pg.wait_for_selector("tbody tr", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)

    busca2 = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca2.count():
        busca2.fill("liderado1")
        pg.wait_for_timeout(2000)

    # Capturar requests
    captured_reqs = []
    def captura_req(req):
        if req.method in ("POST", "PATCH", "PUT") and "record" in req.url.lower():
            captured_reqs.append({"method": req.method, "url": req.url, "body": req.post_data or ''})
            log(f"  [NET] {req.method} {req.url}")
    pg.on("request", captura_req)

    # Encontrar linha PENDENTE e clicar no kebab
    rows = pg.locator("tbody tr")
    pending_row = None
    for i in range(rows.count()):
        row = rows.nth(i)
        row_text = pg.evaluate("(r) => r.innerText", row.element_handle())
        if "Aprovado" not in row_text and "Emitido" not in row_text:
            pending_row = row
            break

    if not pending_row and rows.count() > 0:
        pending_row = rows.first  # usar o primeiro mesmo
        log("  Nenhum pendente encontrado, usando primeiro registro")

    if pending_row:
        row_text = pg.evaluate("(r) => r.innerText.replace(/\\n/g,' ').slice(0,80)", pending_row.element_handle())
        log(f"  Linha selecionada: {row_text}")

        kebab = pg.evaluate("""(row) => {
            const btns = [...row.querySelectorAll('button')].filter(b => b.getBoundingClientRect().height > 0);
            if (btns.length) {
                const last = btns[btns.length-1];
                const box = last.getBoundingClientRect();
                return {x: box.x+box.width/2, y: box.y+box.height/2};
            }
            return null;
        }""", pending_row.element_handle())
        if kebab:
            pg.mouse.click(kebab['x'], kebab['y'])
            pg.wait_for_timeout(1000)
            snap(pg, "step1_kebab_aberto")
            items = pg.evaluate("""() => {
                return [...document.querySelectorAll('[role="menuitem"]')].map(e => ({
                    text: (e.innerText||'').trim(), id: e.id,
                    visible: e.getBoundingClientRect().height > 0
                })).filter(i => i.visible);
            }""")
            log(f"  Menu items: {json.dumps(items, ensure_ascii=False)}")

            # Procurar o item de avaliacao/aprovacao (rate_review)
            avaliacao = pg.locator("[role='menuitem']").filter(
                has_text=re.compile("rate_review|Avaliar|Aprovar|Analisar|Emitir", re.I)).first
            if avaliacao.count():
                box_av = avaliacao.bounding_box()
                if box_av:
                    pg.mouse.click(box_av['x']+box_av['width']/2, box_av['y']+box_av['height']/2)
                    pg.wait_for_timeout(2000)
                    snap(pg, "step1_apos_clicar_rate_review")
                    log(f"  URL pos rate_review: {pg.url}")
            else:
                # rate_review e o icone; pode ser o primeiro item
                if items:
                    first_item_id = items[0]['id']
                    pg.locator(f"[id='{first_item_id}']").click(timeout=5000)
                    pg.wait_for_timeout(2000)
                    snap(pg, "step1_apos_primeiro_item")
                    log(f"  URL pos primeiro item: {pg.url}")

    pg.remove_listener("request", captura_req)
    log(f"\n  Requests capturados: {json.dumps(captured_reqs, ensure_ascii=False)}")

    if captured_reqs:
        approval_endpoint = captured_reqs[0]['url']
        log(f"  Endpoint aprovacao: {approval_endpoint}")
    else:
        log("  Nenhuma request capturada. Explorando URL atual...")
        current_url = pg.url
        if "/records/" in current_url:
            approval_endpoint = current_url
            log(f"  URL atual como endpoint: {approval_endpoint}")

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC1.3 - Clicar no campo CORRETO (Adicionar pessoas)")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    login_lider(pg)
    snap(pg, "tc1v3_lider_lista")

    # Capturar 401s na pagina de novo registro
    requests_401 = []
    def captura_401(resp):
        if resp.status == 401:
            requests_401.append({"url": resp.url, "status": resp.status})
            log(f"  [401] {resp.url}")
    pg.on("response", captura_401)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)
    snap(pg, "tc1v3_form_new")

    pg.remove_listener("response", captura_401)
    log(f"  401s capturados ao carregar form: {json.dumps(requests_401, ensure_ascii=False)}")

    # Clicar no campo Pessoas (icone de grupo / "Adicionar pessoas")
    # O campo e um div com texto "Adicionar pessoas" e icone de grupo
    pessoas_target = pg.evaluate("""() => {
        // Procurar o elemento que tem o texto "Adicionar pessoas"
        const all = [...document.querySelectorAll('*')];
        const el = all.find(e => e.children.length === 0 && e.innerText.trim() === 'Adicionar pessoas');
        if (el) {
            const container = el.closest('[class]') || el.parentElement;
            const box = container.getBoundingClientRect();
            return {x: box.x + box.width/2, y: box.y + box.height/2, found: 'texto'};
        }
        // Tentar pelo icone group
        const icons = all.filter(e => e.getAttribute && e.getAttribute('class') && /group|pessoas|person/i.test(e.className));
        if (icons.length) {
            const icon = icons[0];
            const box = icon.getBoundingClientRect();
            if (box.height > 0) return {x: box.x + box.width/2, y: box.y + box.height/2, found: 'icon'};
        }
        return null;
    }""")
    log(f"  Campo Pessoas: {pessoas_target}")

    if pessoas_target:
        pg.mouse.click(pessoas_target['x'], pessoas_target['y'])
        pg.wait_for_timeout(2000)
        snap(pg, "tc1v3_pessoas_clicado")

        # Ver se abriu algo (drawer, typeahead)
        log(f"  URL apos click Pessoas: {pg.url}")

        # Verificar inputs disponiveis apos o click
        inputs_pos = pg.evaluate("""() => {
            return [...document.querySelectorAll('input[type="text"], input[type="search"]')]
                .filter(i => i.getBoundingClientRect().height > 0)
                .map(i => ({id: i.id, placeholder: i.placeholder, visible: true}));
        }""")
        log(f"  Inputs possiveis: {json.dumps(inputs_pos, ensure_ascii=False)}")

        # Procurar input de busca no modal/drawer
        busca_pessoas = pg.locator("input[placeholder*='Pesquise' i], input[placeholder*='nome' i], input[placeholder*='email' i]").first
        if busca_pessoas.count():
            busca_pessoas.fill("liderado")
            pg.wait_for_timeout(1500)
            snap(pg, "tc1v3_busca_pessoas")

            # Coletar opcoes
            opcoes = pg.evaluate("""() => {
                return [...document.querySelectorAll('[role="option"], [class*="option"], [class*="item"]')]
                    .filter(o => o.getBoundingClientRect().height > 0)
                    .map(o => (o.innerText||'').trim()).filter(t => t).slice(0, 20);
            }""")
            log(f"  Opcoes de Pessoas: {opcoes}")
            results['tc1_opcoes_pessoas'] = opcoes

            tem_liderado = any("liderado" in o.lower() for o in opcoes)
            outros = [o for o in opcoes if "liderado" not in o.lower() and len(o) > 3]

            if tem_liderado and len(outros) == 0:
                results['tc1_scope'] = 'PASS'
                log("  TC1.3 PASS - Apenas liderado1 aparece (escopo correto)")
            elif tem_liderado and len(outros) > 0:
                results['tc1_scope'] = f'FAIL_escopo_largo:{opcoes}'
                log(f"  TC1.3 FAIL - {len(opcoes)} opcoes, esperado apenas liderado1")
            elif not tem_liderado and not opcoes:
                results['tc1_scope'] = 'INCONCLUSIVO_sem_resultados'
                log("  TC1.3 INCONCLUSIVO - sem resultados no dropdown")
            else:
                results['tc1_scope'] = f'FAIL_sem_liderado:{opcoes}'
                log(f"  TC1.3 FAIL - liderado1 nao aparece")
        else:
            # Talvez o drawer nao abriu
            snap(pg, "tc1v3_sem_busca_pessoas")
            log("  Input de busca nao encontrado apos click Pessoas")
            results['tc1_scope'] = 'INCONCLUSIVO_drawer_nao_abriu'
    else:
        log("  Campo Adicionar pessoas nao encontrado")
        results['tc1_scope'] = 'INCONCLUSIVO_campo_nao_encontrado'
        snap(pg, "tc1v3_sem_campo_pessoas")

    pg.keyboard.press("Escape")
    pg.wait_for_timeout(500)

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC1.4 - Admin Provedores (cross-check)")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    try: pg.wait_for_selector("tbody tr", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)

    # Clicar na aba Provedores
    tab_prov = pg.locator("[role='tab'], a, button").filter(has_text=re.compile("Provedores?", re.I)).first
    if tab_prov.count():
        box_tab = tab_prov.bounding_box()
        if box_tab:
            pg.mouse.click(box_tab['x']+box_tab['width']/2, box_tab['y']+box_tab['height']/2)
            pg.wait_for_timeout(2000)
            snap(pg, "tc1_admin_provedores")

            prov_count_admin = contar_linhas_reais(pg)
            log(f"  Admin - Provedores: {prov_count_admin}")
            results['tc1_admin_provedores'] = prov_count_admin

            if prov_count_admin == 0:
                results['tc1_provedores'] = 'INCONCLUSIVO_org_sem_provedores'
                log("  TC1.4 INCONCLUSIVO - admin tambem ve 0 provedores (org sem dados de massa)")
            else:
                # Comparar com o que o lider ve
                lider_prov = results.get('tc1_provedores_count', 0)
                if lider_prov >= prov_count_admin:
                    results['tc1_provedores'] = f'PASS_lider_ve_total (lider={lider_prov}, admin={prov_count_admin})'
                    log(f"  TC1.4 PASS - lider ve tantos quanto admin ({lider_prov}={prov_count_admin})")
                elif lider_prov == 0:
                    results['tc1_provedores'] = f'FAIL_lider_ve_0_admin_ve_{prov_count_admin}'
                    log(f"  TC1.4 FAIL - lider ve 0 provedores mas admin ve {prov_count_admin}")
                else:
                    results['tc1_provedores'] = f'PARCIAL (lider={lider_prov}, admin={prov_count_admin})'
    else:
        log("  Aba Provedores nao encontrada no admin")
        results['tc1_provedores'] = 'INCONCLUSIVO_aba_nao_encontrada'

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC5 - Cross-check bucket 'Aprovado' vs KPI 'Pendentes'")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    try: pg.wait_for_selector("tbody tr", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)

    busca = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca.count():
        busca.fill("liderado1")
        pg.wait_for_timeout(2000)
        snap(pg, "tc5_admin_busca_liderado1")

    # Ver a situacao do registro QA116-Liderado-Externo no admin
    rows = pg.locator("tbody tr")
    row_data = pg.evaluate("""() => {
        return [...document.querySelectorAll('tbody tr')].map(tr => {
            const cells = [...tr.querySelectorAll('td')];
            return cells.map(c => c.innerText.trim()).join(' | ');
        });
    }""")
    log(f"  Dados do registro de liderado1 no admin: {json.dumps(row_data, ensure_ascii=False)}")
    results['tc5_admin_registro_liderado1'] = row_data
    snap(pg, "tc5_admin_registro_situacao")

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC3 - Com endpoint real + aprovar pendente + remover organograma")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg_admin = tw.nova_pagina(p, slow_mo=400)
    ba2, ca2, pg_lider = tw.nova_pagina(p, slow_mo=400)

    tw.login(pg_admin, {"base_url": BASE_URL, "org_id": ORG_ID,
                         "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado para TC3")
    login_lider(pg_lider)
    log("[lider] logado para TC3")

    # Verificar o que o lider ve agora
    snap(pg_lider, "tc3v3_lider_lista")
    linhas_lider = contar_linhas_reais(pg_lider)
    log(f"  [TC3] Lider ve {linhas_lider} registros")

    # Ver KPIs do lider
    kpis_lider = pg_lider.evaluate("""() => {
        const labels = ['Emitidos', 'Expirados', 'Pendentes', 'Recusados'];
        const result = {};
        labels.forEach(lbl => {
            const labelEl = [...document.querySelectorAll('p, span, div')].find(e =>
                e.children.length === 0 && e.innerText.trim() === lbl
            );
            if (labelEl) {
                let card = labelEl.parentElement;
                for (let i = 0; i < 5; i++) {
                    if (!card) break;
                    const nums = [...card.querySelectorAll('p, span, h2, h3, h4')].filter(n =>
                        n !== labelEl && /^\\d+$/.test(n.innerText.trim())
                    );
                    if (nums.length) { result[lbl] = parseInt(nums[0].innerText.trim()); break; }
                    card = card.parentElement;
                }
                if (result[lbl] === undefined) result[lbl] = -1;
            } else { result[lbl] = -1; }
        });
        return result;
    }""")
    log(f"  [TC3] KPIs lider: {json.dumps(kpis_lider, ensure_ascii=False)}")
    results['tc3_kpis_lider'] = kpis_lider
    results['tc5_kpi_lider'] = kpis_lider

    # TC3 Passo 1: Lider aprova registro - clicar no kebab e rate_review
    if linhas_lider > 0:
        primeira = pg_lider.locator("tbody tr").first
        row_txt = pg_lider.evaluate("(r) => r.innerText.replace(/\\n/g,' ').slice(0,100)", primeira.element_handle())
        log(f"  [TC3] Linha do lider: {row_txt}")

        kebab_lider = pg_lider.evaluate("""(row) => {
            const btns = [...row.querySelectorAll('button')].filter(b => b.getBoundingClientRect().height > 0);
            if (btns.length) {
                const last = btns[btns.length-1];
                const box = last.getBoundingClientRect();
                return {x: box.x+box.width/2, y: box.y+box.height/2};
            }
            return null;
        }""", primeira.element_handle())
        if kebab_lider:
            pg_lider.mouse.click(kebab_lider['x'], kebab_lider['y'])
            pg_lider.wait_for_timeout(1000)
            snap(pg_lider, "tc3v3_kebab_lider")

            items_lider = pg_lider.evaluate("""() => {
                return [...document.querySelectorAll('[role="menuitem"]')].map(e => ({
                    text: (e.innerText||'').trim(),
                    id: e.id
                })).filter(i => i.text && i.text !== 'rate_review');
            }""")
            log(f"  [TC3] Items menu lider: {json.dumps(items_lider, ensure_ascii=False)}")
            results['tc3_menu_lider'] = [i['text'] for i in items_lider]

            # Clicar no primeiro item (rate_review = icone de avaliacao)
            first_item = pg_lider.locator("[role='menuitem']").first
            if first_item.count():
                box_fi = first_item.bounding_box()
                if box_fi:
                    pg_lider.mouse.click(box_fi['x']+box_fi['width']/2, box_fi['y']+box_fi['height']/2)
                    pg_lider.wait_for_timeout(2000)
                    snap(pg_lider, "tc3v3_apos_rate_review")
                    log(f"  [TC3] URL apos rate_review: {pg_lider.url}")
                    results['tc3_url_apos_aprovacao'] = pg_lider.url
    else:
        log("  [TC3] Lider nao ve registros - verificar se setup esta correto")
        results['tc3'] = 'INCONCLUSIVO_lider_sem_registros'

    # TC3 Passo 2: Admin remove liderado1 do campo Responsavel via edicao do usuario
    log("\n  [TC3] Removendo Responsavel do liderado1 via edicao de usuario...")
    pg_admin.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
                  wait_until="domcontentloaded", timeout=30000)
    try: pg_admin.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg_admin.wait_for_timeout(2000)
    snap(pg_admin, "tc3v3_edit_liderado1")

    # Ver todos os inputs para encontrar o campo Responsavel
    inputs_form = pg_admin.evaluate("""() => {
        return [...document.querySelectorAll('input, select')].filter(i => i.getBoundingClientRect().height > 0).map(i => ({
            id: i.id, name: i.name, type: i.type, value: i.value.slice(0,30), placeholder: (i.placeholder||'').slice(0,30)
        }));
    }""")
    log(f"  Inputs no form liderado1: {json.dumps(inputs_form, ensure_ascii=False)}")

    # Procurar o campo Responsavel - pode ser um campo de busca com nome do lider atual
    # Ou um select com o ID do lider
    responsavel_field = pg_admin.evaluate("""() => {
        // Procurar label "Responsavel" ou "Responsável"
        const labels = [...document.querySelectorAll('label')];
        const l = labels.find(lb => /respons/i.test(lb.innerText));
        if (l) {
            const forId = l.getAttribute('for');
            if (forId) {
                const field = document.getElementById(forId);
                if (field) {
                    const box = field.getBoundingClientRect();
                    return {type: field.tagName, id: forId, value: field.value, visible: box.height > 0, x: box.x + box.width/2, y: box.y + box.height/2};
                }
            }
            // Tentar o elemento logo depois do label
            const sibling = l.nextElementSibling || l.closest('div')?.querySelector('input, select');
            if (sibling) {
                const box = sibling.getBoundingClientRect();
                return {type: sibling.tagName, id: sibling.id, value: sibling.value, visible: box.height > 0, x: box.x + box.width/2, y: box.y + box.height/2};
            }
        }
        return null;
    }""")
    log(f"  Campo Responsavel: {responsavel_field}")

    # Scrollar para ver a secao Lideranca
    pg_admin.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    pg_admin.wait_for_timeout(500)
    snap(pg_admin, "tc3v3_lideranca_section")

    # Ver o que esta na secao Lideranca
    lideranca = pg_admin.evaluate("""() => {
        const h = [...document.querySelectorAll('h2, h3, h4, label, legend, p')].find(e => /lideran/i.test(e.innerText));
        if (h) {
            const section = h.closest('section, div.card, div.form-group, fieldset') || h.parentElement;
            return section ? section.innerText.slice(0, 300) : h.innerText;
        }
        return 'secao nao encontrada';
    }""")
    log(f"  Secao Lideranca: {lideranca[:200]}")

    # Procurar o input de Responsavel (search field)
    resp_input = pg_admin.evaluate("""() => {
        // Procurar input visible proxima a "Responsavel" label
        const inputs = [...document.querySelectorAll('input[type="text"], input[type="search"]')].filter(i => {
            const box = i.getBoundingClientRect();
            return box.height > 0;
        });
        // Ver qual tem valor relacionado ao lider
        for (const inp of inputs) {
            if (/qaliderpuro|lider|responsavel/i.test(inp.value) || inp.id.includes('manager')) {
                const box = inp.getBoundingClientRect();
                return {id: inp.id, value: inp.value, x: box.x + box.width/2, y: box.y + box.height/2};
            }
        }
        return null;
    }""")
    log(f"  Input responsavel com valor: {resp_input}")

    # Tentar limpar o campo Responsavel
    # O campo pode ser um seletor de usuario - procurar o botao de remover (X) proxima ao lider
    remove_responsavel = pg_admin.evaluate("""() => {
        // Procurar botao X ou "remover" proximo ao nome do lider responsavel
        const all = [...document.querySelectorAll('button, [class*="clear"], [class*="remove"], [class*="delete"]')];
        for (const el of all) {
            const parent = el.closest('[class]');
            if (parent && /(qaliderpuro|responsavel|lider)/i.test(parent.innerText)) {
                const box = el.getBoundingClientRect();
                if (box.height > 0) return {x: box.x + box.width/2, y: box.y + box.height/2, text: el.innerText};
            }
        }
        return null;
    }""")
    log(f"  Botao remover responsavel: {remove_responsavel}")

    if remove_responsavel:
        pg_admin.mouse.click(remove_responsavel['x'], remove_responsavel['y'])
        pg_admin.wait_for_timeout(1000)
        snap(pg_admin, "tc3v3_responsavel_removido")
        log("  Responsavel removido!")

    # Tentar via JS: encontrar o input de busca da secao Responsavel e limpar
    # O campo pode ser um search input oculto com valor do ID do lider
    # Tentar encontrar o "x" para limpar a selecao atual
    clear_btn = pg_admin.locator("[class*='clear-indicator'], [aria-label*='clear' i], [aria-label*='remove' i]").first
    if clear_btn.count():
        clear_btn.click(timeout=3000)
        pg_admin.wait_for_timeout(1000)
        snap(pg_admin, "tc3v3_clear_responsavel")
        log("  Responsavel limpo via clear button!")

    # Salvar as alteracoes
    save_tc3 = pg_admin.evaluate("""() => {
        const btns = [...document.querySelectorAll('button, input[type=submit]')];
        const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
        if (s) { const box = s.getBoundingClientRect(); return {x: box.x+box.width/2, y: box.y+box.height/2}; }
        return null;
    }""")
    if save_tc3:
        pg_admin.mouse.click(save_tc3['x'], save_tc3['y'])
        pg_admin.wait_for_timeout(3000)
        snap(pg_admin, "tc3v3_salvo")
        log(f"  [TC3] Salvo. URL: {pg_admin.url}")

    # TC3 Passo 3: Admin verifica que registro ainda existe
    pg_admin.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg_admin.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    try: pg_admin.wait_for_selector("tbody tr", timeout=8000)
    except: pass
    pg_admin.wait_for_timeout(3000)

    busca_admin_tc3 = pg_admin.locator("input[placeholder*='Pesquise' i]").first
    if busca_admin_tc3.count():
        busca_admin_tc3.fill("liderado1")
        pg_admin.wait_for_timeout(2000)

    snap(pg_admin, "tc3v3_admin_registros_liderado1")
    linhas_admin_tc3 = contar_linhas_reais(pg_admin)
    log(f"  [TC3] Admin ve {linhas_admin_tc3} registros de liderado1")
    results['tc3_admin_registros'] = linhas_admin_tc3

    # TC3 Passo 4: Lider nao deve ver mais o registro
    pg_lider.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg_lider.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    try: pg_lider.wait_for_selector("tbody tr, [class*='stat']", timeout=8000)
    except: pass
    pg_lider.wait_for_timeout(5000)
    snap(pg_lider, "tc3v3_lider_apos_remocao")
    linhas_lider_tc3 = contar_linhas_reais(pg_lider)
    log(f"  [TC3] Lider ve {linhas_lider_tc3} registros apos remocao do responsavel")
    results['tc3_lider_apos_remocao'] = linhas_lider_tc3

    # VEREDITO TC3
    if results.get('tc3') != 'INCONCLUSIVO_lider_sem_registros':
        if linhas_admin_tc3 > 0 and linhas_lider_tc3 == 0:
            results['tc3'] = 'PASS'
            log("  TC3 PASS - Admin ve registro; lider nao ve mais apos remocao do time")
        elif linhas_admin_tc3 == 0:
            results['tc3'] = 'FAIL_registro_sumiu_do_admin'
            log("  TC3 FAIL - Registro sumiu do admin tambem")
        elif linhas_lider_tc3 > 0:
            results['tc3'] = f'FAIL_lider_ainda_ve:{linhas_lider_tc3}'
            log(f"  TC3 FAIL - Lider ainda ve {linhas_lider_tc3} registros apos sair do time")
        else:
            results['tc3'] = 'INCONCLUSIVO'

    # Restaurar responsavel do liderado1 (qaliderpuro como responsavel)
    log("\n  [TC3] Restaurando responsavel do liderado1...")
    pg_admin.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
                  wait_until="domcontentloaded", timeout=30000)
    try: pg_admin.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg_admin.wait_for_timeout(2000)
    snap(pg_admin, "tc3v3_restaurar_form")

    # Tentar preencher o campo responsavel via icone de lupa/busca
    lupa = pg_admin.locator("button[class*='search'], button[aria-label*='search' i], button[aria-label*='buscar' i], a[class*='search']").first
    if not lupa.count():
        # Tentar pelo contexto da label Responsavel
        responsavel_area = pg_admin.evaluate("""() => {
            const labels = [...document.querySelectorAll('label')];
            const l = labels.find(lb => /respons/i.test(lb.innerText));
            if (!l) return null;
            const container = l.closest('div, section, fieldset');
            if (!container) return null;
            const searchBtn = container.querySelector('button, input[type="search"]');
            if (searchBtn) {
                const box = searchBtn.getBoundingClientRect();
                return {x: box.x + box.width/2, y: box.y + box.height/2};
            }
            return null;
        }""")
        log(f"  Area responsavel: {responsavel_area}")
        if responsavel_area:
            pg_admin.mouse.click(responsavel_area['x'], responsavel_area['y'])
            pg_admin.wait_for_timeout(1500)
            snap(pg_admin, "tc3v3_responsavel_area_clicado")

            # Procurar e preencher input de busca
            busca_resp = pg_admin.locator("input[type='text'], input[type='search']").filter(
                has_text="").first
            if busca_resp.count():
                busca_resp.fill("qaliderpuro")
                pg_admin.wait_for_timeout(1500)
                opcao_lider = pg_admin.locator("[role='option']").filter(
                    has_text=re.compile("qaliderpuro|QALider", re.I)).first
                if opcao_lider.count():
                    opcao_lider.click(timeout=5000)
                    pg_admin.wait_for_timeout(1000)
                    log("  Responsavel preenchido!")

    # Salvar restauracao
    save_rest = pg_admin.evaluate("""() => {
        const btns = [...document.querySelectorAll('button, input[type=submit]')];
        const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
        if (s) { s.click(); return true; }
        return false;
    }""")
    pg_admin.wait_for_timeout(3000)
    snap(pg_admin, "tc3v3_restaurado")
    log(f"  Restaurado: {save_rest}, URL: {pg_admin.url}")

    pg_admin.close(); ca.close(); ba.close()
    pg_lider.close(); ca2.close(); ba2.close()


# SUMARIO
log("\n" + "="*60)
log("SUMARIO TC1/TC3/TC5 + EXTRA")
for k, v in results.items():
    log(f"  {k}: {v}")
log("\n  VEREDITOS:")
log(f"  TC1.3 Pessoas scope: {results.get('tc1_scope','?')}")
log(f"  TC1.4 Provedores:    {results.get('tc1_provedores','?')}")
log(f"  TC3 (RN95):          {results.get('tc3','?')}")
log(f"  TC5 KPIs lider:      {results.get('tc5_kpi_lider','?')}")
