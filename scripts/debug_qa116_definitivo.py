# -*- coding: utf-8 -*-
"""
Script definitivo QA116
TC1.3 - Campo Pessoas (clicar na area "Adicionar pessoas")
TC1.4 - Provedores admin cross-check
TC3   - Remover "QALider Puro116" do campo Responsavel do liderado1 via X
TC5   - Cross-check KPI Pendentes vs situacao no admin
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

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log = lambda *a: print(*a, flush=True)
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


def extrair_kpis(pg):
    return pg.evaluate("""() => {
        const labels = ['Emitidos', 'Expirados', 'Pendentes', 'Recusados'];
        const result = {};
        labels.forEach(lbl => {
            const labelEl = [...document.querySelectorAll('p, span, div')].find(e =>
                e.children.length === 0 && e.innerText && e.innerText.trim() === lbl
            );
            if (labelEl) {
                let card = labelEl.parentElement;
                for (let i = 0; i < 5; i++) {
                    if (!card) break;
                    const nums = [...card.querySelectorAll('p, span, h2, h3, h4')].filter(n =>
                        n !== labelEl && n.innerText && /^\\d+$/.test(n.innerText.trim())
                    );
                    if (nums.length) { result[lbl] = parseInt(nums[0].innerText.trim()); break; }
                    card = card.parentElement;
                }
                if (result[lbl] === undefined) result[lbl] = -1;
            } else { result[lbl] = -1; }
        });
        return result;
    }""")


def contar_linhas_reais(pg):
    count = pg.locator("tbody tr").count()
    if count == 0:
        return 0
    vazio = pg.evaluate("""() => {
        const rows = [...document.querySelectorAll('tbody tr')];
        return rows.every(r => r.innerText && /nenhum|nao ha|não há|no data|sem registro/i.test(r.innerText));
    }""")
    return 0 if vazio else count


# ==============================================================================
log("\n" + "="*60)
log("TC1.3 - Lider: Clicar no campo 'Adicionar pessoas'")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    login_lider(pg)
    log("  [lider] logado em /records")

    # Ir para o form de adicionar
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)
    snap(pg, "tc1v4_form_lider")

    # Estrategia: clicar na area do campo "Pessoas" usando coordenadas da div
    # A div tem placeholder "Adicionar pessoas" e fica logo abaixo da secao de arquivo
    # Baseado no screenshot anterior, o campo fica em y≈422 (campo "Pessoas")
    # Vamos clicar pelo texto placeholder via Playwright locator
    pessoas_locator = pg.locator("text=Adicionar pessoas").first
    if pessoas_locator.count():
        box = pessoas_locator.bounding_box()
        log(f"  Bounding box 'Adicionar pessoas': {box}")
        if box:
            pg.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
            pg.wait_for_timeout(2000)
            snap(pg, "tc1v4_apos_click_pessoas")
            log(f"  URL apos click: {pg.url}")

            # Verificar se algo abriu
            modal_info = pg.evaluate("""() => {
                const modals = [...document.querySelectorAll('[role=dialog], [class*=drawer], [class*=modal], [class*=Drawer], [class*=Modal]')].filter(m => {
                    const box = m.getBoundingClientRect();
                    return box.height > 10;
                });
                const visible_inputs = [...document.querySelectorAll('input')].filter(i => i.getBoundingClientRect().height > 0).map(i => ({
                    id: i.id, placeholder: i.placeholder || '', value: i.value || ''
                }));
                return {
                    modals: modals.length,
                    modal_text: modals.map(m => m.innerText && m.innerText.slice(0, 100)),
                    inputs: visible_inputs
                };
            }""")
            log(f"  Modal info: {json.dumps(modal_info, ensure_ascii=False)}")

            if modal_info.get('modals', 0) > 0:
                log("  Modal/Drawer aberto!")
                snap(pg, "tc1v4_modal_pessoas")

                # Tentar digitar no input do modal
                inp = pg.locator("input").filter(has_text="").last
                if not inp.count():
                    # Pegar o ultimo input visivel
                    all_inputs = modal_info.get('inputs', [])
                    if all_inputs:
                        last = all_inputs[-1]
                        if last.get('id'):
                            pg.fill(f"#{last['id']}", "liderado")
                        else:
                            pg.keyboard.type("liderado")
                    else:
                        pg.keyboard.type("liderado")
                else:
                    inp.fill("liderado")
                pg.wait_for_timeout(1500)
                snap(pg, "tc1v4_modal_busca")

                opcoes = pg.evaluate("""() => {
                    return [...document.querySelectorAll('[role=option], [class*=option], li, [data-testid*=option]')].filter(el => {
                        const box = el.getBoundingClientRect();
                        return box.height > 0 && el.innerText && el.innerText.trim().length > 0;
                    }).map(el => el.innerText && el.innerText.trim()).filter(t => t).slice(0, 20);
                }""")
                log(f"  Opcoes modal: {opcoes}")
                results['tc1_3_opcoes'] = opcoes
            else:
                log("  Nenhum modal. Verificar se e typeahead inline...")
                # Tentar digitar diretamente
                pg.keyboard.type("liderado")
                pg.wait_for_timeout(1500)
                snap(pg, "tc1v4_typeahead")

                opcoes = pg.evaluate("""() => {
                    return [...document.querySelectorAll('[role=option], [class*=option]')].filter(el => {
                        const box = el.getBoundingClientRect();
                        return box.height > 0;
                    }).map(el => el.innerText && el.innerText.trim()).filter(t => t).slice(0, 20);
                }""")
                log(f"  Opcoes typeahead: {opcoes}")
                results['tc1_3_opcoes'] = opcoes

            # Analisar resultado
            opcoes = results.get('tc1_3_opcoes', [])
            tem_liderado = any("liderado" in str(o).lower() or "puro" in str(o).lower() for o in opcoes)
            outros = [o for o in opcoes if o and "liderado" not in str(o).lower() and "puro" not in str(o).lower() and len(str(o)) > 3]

            if tem_liderado and len(outros) == 0:
                results['tc1_3'] = 'PASS'
                log("  TC1.3 PASS - Apenas liderado1 nas opcoes (escopo correto)")
            elif not opcoes or all("nenhum" in str(o).lower() for o in opcoes if o):
                results['tc1_3'] = 'INCONCLUSIVO_sem_resultados'
                log("  TC1.3 INCONCLUSIVO - Nenhuma opcao visivel (401 no carregamento)")
            elif tem_liderado and len(outros) > 0:
                results['tc1_3'] = f'FAIL_escopo_largo: {len(opcoes)} opcoes'
                log(f"  TC1.3 FAIL - {len(opcoes)} opcoes (escopo nao filtrado)")
            else:
                results['tc1_3'] = f'INCONCLUSIVO: {opcoes}'
    else:
        log("  Locator 'Adicionar pessoas' nao encontrado")
        results['tc1_3'] = 'INCONCLUSIVO_campo_nao_encontrado'
        snap(pg, "tc1v4_sem_campo")

    pg.keyboard.press("Escape")
    pg.wait_for_timeout(500)

    # TC1.4 - Aba Provedores pelo lider
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)

    tab_prov = pg.locator("[role='tab'], a").filter(has_text=re.compile("Provedores?", re.I)).first
    if tab_prov.count():
        tab_prov.click(timeout=5000)
        pg.wait_for_timeout(2000)
        snap(pg, "tc14_lider_provedores")
        results['tc1_lider_provedores'] = contar_linhas_reais(pg)
        log(f"  Lider - Provedores: {results['tc1_lider_provedores']}")
    else:
        results['tc1_lider_provedores'] = -1

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC1.4 - Admin Provedores cross-check")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)

    tab_prov = pg.locator("[role='tab'], a").filter(has_text=re.compile("Provedores?", re.I)).first
    if tab_prov.count():
        tab_prov.click(timeout=5000)
        pg.wait_for_timeout(2000)
        snap(pg, "tc14_admin_provedores")
        prov_admin = contar_linhas_reais(pg)
        results['tc1_admin_provedores'] = prov_admin
        log(f"  Admin - Provedores: {prov_admin}")

        lider_prov = results.get('tc1_lider_provedores', -1)
        if prov_admin == 0:
            results['tc1_4'] = 'INCONCLUSIVO_org_sem_provedores'
            log("  TC1.4 INCONCLUSIVO - org nao tem provedores cadastrados")
        elif lider_prov >= prov_admin:
            results['tc1_4'] = f'PASS (lider={lider_prov}, admin={prov_admin})'
            log("  TC1.4 PASS")
        elif lider_prov == 0:
            results['tc1_4'] = f'FAIL_lider_0_admin_{prov_admin}'
        else:
            results['tc1_4'] = f'PARCIAL (lider={lider_prov}, admin={prov_admin})'
    else:
        results['tc1_4'] = 'INCONCLUSIVO_aba_nao_encontrada'

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC5 - Cross-check: situacao do registro no admin")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    try: pg.wait_for_selector("tbody tr", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)

    # Buscar pelo nome do lider (qaliderpuro) para ver o registro que ele possui
    busca = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca.count():
        busca.fill("QALider")
        pg.wait_for_timeout(2000)
        snap(pg, "tc5_admin_busca_QALider")
        rows = pg.evaluate("""() => {
            return [...document.querySelectorAll('tbody tr')].map(tr => tr.innerText && tr.innerText.replace(/\\n/g,' ').slice(0, 150));
        }""")
        log(f"  Registros QALider no admin: {rows}")
        results['tc5_registros_QALider'] = rows

        busca.fill("")
        pg.wait_for_timeout(500)
        # Buscar pelo conteudo do registro que o lider tem
        busca.fill("QA116-Liderado-Externo")
        pg.wait_for_timeout(2000)
        snap(pg, "tc5_admin_busca_conteudo")
        rows2 = pg.evaluate("""() => {
            return [...document.querySelectorAll('tbody tr')].map(tr => tr.innerText && tr.innerText.replace(/\\n/g,' ').slice(0, 150));
        }""")
        log(f"  Registros 'QA116-Liderado-Externo' no admin: {rows2}")
        results['tc5_registros_conteudo'] = rows2

    snap(pg, "tc5_admin_kpis")
    kpis_admin = extrair_kpis(pg)
    log(f"  KPIs admin: {json.dumps(kpis_admin, ensure_ascii=False)}")
    results['tc5_kpis_admin'] = kpis_admin

    ca.close(); ba.close()

# TC5 - Verificar KPIs do lider novamente
with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    login_lider(pg)

    kpis_lider = extrair_kpis(pg)
    log(f"  KPIs lider: {json.dumps(kpis_lider, ensure_ascii=False)}")
    results['tc5_kpis_lider'] = kpis_lider
    snap(pg, "tc5_lider_kpis")

    # Ver a linha visivel do lider
    rows_lider = pg.evaluate("""() => {
        return [...document.querySelectorAll('tbody tr')].map(tr => tr.innerText && tr.innerText.replace(/\\n/g,' ').slice(0, 150));
    }""")
    log(f"  Linhas lider: {rows_lider}")
    results['tc5_linhas_lider'] = rows_lider
    n_linhas = contar_linhas_reais(pg)
    results['tc5_n_linhas'] = n_linhas
    log(f"  N linhas reais lider: {n_linhas}")

    ca.close(); ba.close()

# Analisar TC5
kpis_l = results.get('tc5_kpis_lider', {})
n = results.get('tc5_n_linhas', 0)
pendentes = kpis_l.get('Pendentes', -1)
emitidos = kpis_l.get('Emitidos', -1)

total_kpi = sum(v for v in kpis_l.values() if v > 0)
if total_kpi == n:
    results['tc5'] = f'PASS (total KPIs={total_kpi} = linhas={n})'
    log(f"  TC5 PASS - KPIs somam {total_kpi} = {n} linhas")
else:
    results['tc5'] = f'INVESTIGAR (total_kpi={total_kpi}, linhas={n}, kpis={kpis_l})'
    log(f"  TC5 INVESTIGAR - KPIs somam {total_kpi} mas ha {n} linhas")


# ==============================================================================
log("\n" + "="*60)
log("TC3 - Remover Responsavel do liderado1 (clicar no X)")
log("="*60)

# Para TC3 precisamos:
# 1. Verificar o estado atual: lider ve 1 registro de liderado1
# 2. Admin remove QALider como responsavel do liderado1 (clicar no X da pill "QALider Puro116")
# 3. Verificar que admin ainda ve o registro (persistencia)
# 4. Verificar que lider NAO ve mais o registro
# 5. Restaurar o responsavel

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    # Verificar estado ANTES: lider vendo registro
    # (ja sabemos que sim, do screenshot anterior)
    log("  [TC3] Admin editando liderado1 para remover responsavel...")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "tc3_before_remove_resp")

    # Encontrar e clicar no X da pill "QALider Puro116"
    # O X e um span/button dentro do container do responsavel
    # Baseado no screenshot: ha um avatar + "QALider Puro116" + "x" button
    x_responsavel = pg.evaluate("""() => {
        // Procurar o botao X ou close dentro do container do responsavel
        const all = [...document.querySelectorAll('button, [class*=close], [class*=remove], [class*=delete], [class*=clear]')];
        for (const el of all) {
            const parent = el.closest('[class]') || el.parentElement;
            if (parent && parent.innerText && /qaliderpuro|QALider|Puro116/i.test(parent.innerText)) {
                const box = el.getBoundingClientRect();
                if (box.height > 0) {
                    return {x: box.x + box.width/2, y: box.y + box.height/2, text: el.innerText || el.getAttribute('aria-label') || 'X'};
                }
            }
        }
        // Fallback: procurar por svg ou icone dentro da area do responsavel
        const svgs = [...document.querySelectorAll('svg')];
        for (const svg of svgs) {
            const parent = svg.closest('[class]') || svg.parentElement;
            if (parent && parent.innerText && /qaliderpuro|QALider|Puro116/i.test(parent.innerText)) {
                const box = svg.getBoundingClientRect();
                if (box.height > 0) {
                    return {x: box.x + box.width/2, y: box.y + box.height/2, text: 'svg-X'};
                }
            }
        }
        return null;
    }""")
    log(f"  X responsavel: {x_responsavel}")

    if x_responsavel:
        pg.mouse.click(x_responsavel['x'], x_responsavel['y'])
        pg.wait_for_timeout(1500)
        snap(pg, "tc3_apos_remover_responsavel")

        # Verificar se o campo agora esta vazio
        responsavel_vazio = pg.evaluate("""() => {
            const all = [...document.querySelectorAll('*')];
            const lideEl = all.find(e => e.innerText && /QALider|Puro116/i.test(e.innerText) && e.getBoundingClientRect().height > 0);
            return !lideEl;
        }""")
        log(f"  Responsavel removido do form: {responsavel_vazio}")
        results['tc3_responsavel_removido'] = responsavel_vazio

        # Salvar
        save_btn = pg.evaluate("""() => {
            const btns = [...document.querySelectorAll('button, input[type=submit]')];
            const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
            if (s) { const box = s.getBoundingClientRect(); return {x: box.x+box.width/2, y: box.y+box.height/2}; }
            return null;
        }""")
        if save_btn:
            pg.mouse.click(save_btn['x'], save_btn['y'])
            pg.wait_for_timeout(3000)
            snap(pg, "tc3_salvo")
            log(f"  Salvo. URL: {pg.url}")
        else:
            log("  Botao Salvar nao encontrado!")
    else:
        log("  X do responsavel nao encontrado - verificar screenshot")
        results['tc3'] = 'INCONCLUSIVO_X_nao_encontrado'
        snap(pg, "tc3_sem_x")

    ca.close(); ba.close()

# Aguardar um momento para o servidor processar
import time
log("  Aguardando 3s para o servidor processar...")
time.sleep(3)

# Verificar se o admin ainda ve o registro do liderado1
if results.get('tc3') != 'INCONCLUSIVO_X_nao_encontrado':
    with tw.sync_playwright() as p:
        ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
        tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                       "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

        pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
        try: pg.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        try: pg.wait_for_selector("tbody tr", timeout=8000)
        except: pass
        pg.wait_for_timeout(3000)

        busca = pg.locator("input[placeholder*='Pesquise' i]").first
        if busca.count():
            busca.fill("liderado")
            pg.wait_for_timeout(2000)

        snap(pg, "tc3_admin_apos_remocao")
        n_admin = contar_linhas_reais(pg)
        rows_admin = pg.evaluate("""() => {
            return [...document.querySelectorAll('tbody tr')].map(tr => tr.innerText && tr.innerText.replace(/\\n/g,' ').slice(0, 120));
        }""")
        log(f"  [TC3] Admin ve {n_admin} registros de liderado1 apos remocao responsavel")
        log(f"  Rows: {rows_admin}")
        results['tc3_n_admin_pos'] = n_admin
        results['tc3_rows_admin_pos'] = rows_admin

        ca.close(); ba.close()

    # Verificar se o lider ve o registro
    with tw.sync_playwright() as p:
        ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
        login_lider(pg)

        snap(pg, "tc3_lider_apos_remocao")
        n_lider = contar_linhas_reais(pg)
        rows_lider = pg.evaluate("""() => {
            return [...document.querySelectorAll('tbody tr')].map(tr => tr.innerText && tr.innerText.replace(/\\n/g,' ').slice(0, 120));
        }""")
        log(f"  [TC3] Lider ve {n_lider} registros apos remocao responsavel")
        log(f"  Rows: {rows_lider}")
        results['tc3_n_lider_pos'] = n_lider

        # Determinar veredito TC3
        n_admin = results.get('tc3_n_admin_pos', 0)
        if n_admin > 0 and n_lider == 0:
            results['tc3'] = 'PASS'
            log("  TC3 PASS - Admin ve registro (persistencia), lider nao ve mais (escopo)")
        elif n_admin == 0:
            results['tc3'] = 'FAIL_registro_sumiu_do_admin'
            log("  TC3 FAIL - Registro sumiu do admin (nao deveria sumir)")
        elif n_lider > 0:
            results['tc3'] = f'FAIL_lider_ainda_ve_{n_lider}'
            log(f"  TC3 FAIL - Lider ainda ve {n_lider} registros apos sair do time")
        else:
            results['tc3'] = 'INCONCLUSIVO'

        ca.close(); ba.close()

# RESTAURAR o responsavel do liderado1 (desfazer a alteracao do TC3)
log("\n  [RESTORE] Restaurando responsavel do liderado1...")
with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "restore_before")

    # O campo Responsavel deve estar vazio agora - precisamos clicar nele para adicionar
    # Baseado no form: o campo Responsavel fica na secao "Lideranca"
    # Identificar o container do responsavel e clicar para buscar
    resp_container = pg.evaluate("""() => {
        // Procurar container que contem "Responsavel" como texto
        const all = [...document.querySelectorAll('*')];
        const el = all.find(e => e.children.length === 0 && e.innerText && e.innerText.trim() === 'Responsável');
        if (el) {
            const container = el.closest('[class]') || el.parentElement;
            // Encontrar o campo de input dentro do container
            const box = container.getBoundingClientRect();
            return {x: box.x + box.width/2, y: box.y + box.height/2, w: box.width, h: box.height};
        }
        return null;
    }""")
    log(f"  Container responsavel: {resp_container}")

    if resp_container:
        # Clicar no container para ativar busca
        pg.mouse.click(resp_container['x'], resp_container['y'])
        pg.wait_for_timeout(1500)
        snap(pg, "restore_click_resp")

        # Verificar se algum input ficou disponivel
        input_resp = pg.evaluate("""() => {
            const visible = [...document.querySelectorAll('input')].filter(i => i.getBoundingClientRect().height > 0 && !i.readOnly && !i.disabled);
            return visible.map(i => ({id: i.id, placeholder: i.placeholder || ''}));
        }""")
        log(f"  Inputs visiveis apos click: {input_resp}")

        # Procurar pelo input de busca de pessoas (typeahead)
        if input_resp:
            # Usar o ultimo input visivel (provavelmente e o de busca)
            last_input = input_resp[-1]
            if last_input.get('id'):
                pg.fill(f"#{last_input['id']}", "qaliderpuro")
            else:
                pg.keyboard.type("qaliderpuro")
            pg.wait_for_timeout(1500)
            snap(pg, "restore_busca_lider")

            opcao = pg.locator("[role='option']").filter(has_text=re.compile("qaliderpuro|QALider", re.I)).first
            if opcao.count():
                opcao.click(timeout=5000)
                pg.wait_for_timeout(1000)
                log("  Responsavel restaurado!")
            else:
                log("  Opcao do lider nao encontrada no dropdown")
    else:
        log("  Container 'Responsavel' nao encontrado")

    # Salvar restauracao
    save_rest = pg.evaluate("""() => {
        const btns = [...document.querySelectorAll('button, input[type=submit]')];
        const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
        if (s) { s.click(); return true; }
        return false;
    }""")
    pg.wait_for_timeout(3000)
    snap(pg, "restore_salvo")
    log(f"  Restaurado: {save_rest}, URL: {pg.url}")

    ca.close(); ba.close()


# RESUMO FINAL
log("\n" + "="*60)
log("RESUMO FINAL DE TODOS OS TCs")
log("="*60)
for k, v in results.items():
    log(f"  {k}: {v}")

log("\n  === VEREDITOS ===")
log(f"  TC1.3 Pessoas scope: {results.get('tc1_3','?')}")
log(f"  TC1.4 Provedores:    {results.get('tc1_4','?')}")
log(f"  TC3 (RN95):          {results.get('tc3','?')}")
log(f"  TC5 (RN96.5):        {results.get('tc5','?')}")
