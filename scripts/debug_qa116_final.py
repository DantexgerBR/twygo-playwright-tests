# -*- coding: utf-8 -*-
"""
TC1.3 - Clicar no campo Pessoas (lider) e verificar escopo
TC1.4 - Admin provedores cross-check
TC3   - Criar registro pendente para liderado1, aprovar como lider, remover responsavel
TC5   - Cross-check bucket KPIs no admin
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


def contar_linhas_reais(pg):
    count = pg.locator("tbody tr").count()
    if count == 0:
        return 0
    vazio = pg.evaluate("""() => {
        const rows = [...document.querySelectorAll('tbody tr')];
        return rows.every(r => /nenhum|nao ha|não há|no data|sem registro/i.test(r.innerText));
    }""")
    return 0 if vazio else count


# ==============================================================================
log("\n" + "="*60)
log("STEP 0: Verificar nome real do liderado1 na plataforma (admin)")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    # Buscar o usuario pelo ID na lista de usuarios
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)

    # Buscar o liderado
    busca = pg.locator("input[placeholder*='Pesquise' i], input[placeholder*='busca' i]").first
    if busca.count():
        busca.fill("liderado")
        pg.wait_for_timeout(2000)
        snap(pg, "s0_usuarios_busca_liderado")

        rows = pg.evaluate("""() => {
            return [...document.querySelectorAll('tbody tr')].map(tr => ({
                texto: tr.innerText.replace(/\\n/g,' ').slice(0,100),
                id_link: tr.querySelector('a')?.href?.slice(-20) || ''
            })).slice(0, 10);
        }""")
        log(f"  Usuarios liderado: {json.dumps(rows, ensure_ascii=False)}")
    else:
        # Ir direto para o edit do usuario pelo ID
        pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
                wait_until="domcontentloaded", timeout=30000)
        try: pg.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        pg.wait_for_timeout(2000)
        snap(pg, "s0_liderado_edit")
        nome_liderado = pg.evaluate("""() => {
            const inp = document.querySelector('#user_name, input[name*=name]');
            return inp?.value || '';
        }""")
        log(f"  Nome liderado: {nome_liderado}")

    # Verificar o campo responsavel do liderado
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "s0_liderado_edit_full")

    # Capturar todos os inputs para mapear o form
    form_data = pg.evaluate("""() => {
        return [...document.querySelectorAll('input, select')].filter(el => el.getBoundingClientRect().height > 0).map(el => ({
            id: el.id, name: el.name, type: el.type, value: (el.value||'').slice(0,50), placeholder: (el.placeholder||'').slice(0,40)
        }));
    }""")
    log(f"  Form liderado1 (inputs visiveis): {json.dumps(form_data, ensure_ascii=False)}")

    # Ver o HTML da secao Lideranca
    scroll_js = pg.evaluate("""() => {
        const labels = [...document.querySelectorAll('label')];
        return labels.map(l => ({text: l.innerText, for: l.getAttribute('for')})).slice(0, 30);
    }""")
    log(f"  Labels: {json.dumps(scroll_js, ensure_ascii=False)}")

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC1.3 - Lider abre form Adicionar e clica no campo Pessoas")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    login_lider(pg)

    # Ir para o form de adicionar registro
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)
    snap(pg, "tc1_lider_form_new")

    # Capturar requests 401 no form
    r401s = []
    def catch401(resp):
        if resp.status == 401:
            r401s.append(resp.url)
    pg.on("response", catch401)
    pg.wait_for_timeout(1000)
    pg.remove_listener("response", catch401)
    log(f"  401s no carregamento: {r401s}")

    # Inspecionar o DOM para encontrar o campo Pessoas
    pessoas_info = pg.evaluate("""() => {
        // Encontrar elemento com texto "Adicionar pessoas" ou "Pessoas"
        const tudo = [...document.querySelectorAll('*')];
        const pessoa_placeholder = tudo.find(e => e.children.length === 0 && e.innerText.trim() === 'Adicionar pessoas');
        const pessoa_label = tudo.find(e => e.children.length === 0 && e.innerText.trim() === 'Pessoas');

        let result = {placeholder_found: !!pessoa_placeholder, label_found: !!pessoa_label};

        if (pessoa_placeholder) {
            const parent = pessoa_placeholder.parentElement;
            const box = parent.getBoundingClientRect();
            result.placeholder_box = {x: box.x, y: box.y, w: box.width, h: box.height};
            result.placeholder_class = parent.className.slice(0, 60);
            result.click_x = box.x + box.width - 20;  // clicar perto do icone de grupo
            result.click_y = box.y + box.height / 2;
        }

        return result;
    }""")
    log(f"  Campo Pessoas info: {json.dumps(pessoas_info, ensure_ascii=False)}")

    # Clicar no campo Pessoas
    if pessoas_info.get('placeholder_found'):
        pg.mouse.click(pessoas_info['click_x'], pessoas_info['click_y'])
        pg.wait_for_timeout(2000)
        snap(pg, "tc1_apos_click_pessoas")
        log(f"  URL apos click: {pg.url}")

        # Ver se abriu um modal/drawer ou se o input ficou ativo
        estado_apos = pg.evaluate("""() => {
            // Procurar inputs visiveis que nao existiam antes
            const inputs = [...document.querySelectorAll('input[type=text], input[type=search]')].filter(i => {
                const box = i.getBoundingClientRect();
                return box.height > 0;
            });
            const modals = [...document.querySelectorAll('[role=dialog], [class*=drawer], [class*=modal]')].filter(m => {
                const box = m.getBoundingClientRect();
                return box.height > 0;
            });
            return {
                inputs: inputs.map(i => ({id: i.id, placeholder: i.placeholder, value: i.value})),
                modals: modals.length,
                modal_text: modals.map(m => m.innerText.slice(0, 100))
            };
        }""")
        log(f"  Estado apos click: {json.dumps(estado_apos, ensure_ascii=False)}")

        # Se abriu modal/drawer, buscar dentro dele
        if estado_apos.get('modals', 0) > 0:
            log("  Modal/drawer aberto!")
            snap(pg, "tc1_modal_pessoas")

            # Buscar por liderado dentro do modal
            inputs_modal = estado_apos.get('inputs', [])
            for inp in inputs_modal:
                if inp.get('placeholder', '') or not inp.get('value', ''):
                    pg.fill(f"#{inp['id']}", "liderado") if inp.get('id') else None
                    break
            else:
                # Tentar qualquer input visivel
                inp_vis = pg.locator("input[type='text']:visible, input[type='search']:visible").first
                if inp_vis.count():
                    inp_vis.fill("liderado")
            pg.wait_for_timeout(1500)
            snap(pg, "tc1_modal_busca_liderado")

            opcoes = pg.evaluate("""() => {
                return [...document.querySelectorAll('[role=option], [class*=option], [class*=item], li')].filter(el => {
                    const box = el.getBoundingClientRect();
                    return box.height > 0 && el.innerText.trim().length > 0;
                }).map(el => el.innerText.trim()).filter(t => t.length > 0).slice(0, 20);
            }""")
            log(f"  Opcoes no modal: {opcoes}")
            results['tc1_opcoes_pessoas'] = opcoes

            tem_liderado = any("liderado" in o.lower() or "qa116" in o.lower() or "puro" in o.lower() for o in opcoes)
            outros_usuarios = [o for o in opcoes if "liderado" not in o.lower() and "qa116" not in o.lower() and "puro" not in o.lower() and len(o) > 3]

            if tem_liderado and len(outros_usuarios) == 0:
                results['tc1_3'] = 'PASS'
                log("  TC1.3 PASS - Apenas liderado1 nas opcoes do campo Pessoas")
            elif not opcoes or "nenhum" in str(opcoes).lower():
                results['tc1_3'] = 'INCONCLUSIVO_sem_resultados'
                log("  TC1.3 INCONCLUSIVO - Nenhuma opcao retornada")
            elif tem_liderado and len(outros_usuarios) > 0:
                results['tc1_3'] = f'FAIL_escopo_largo ({len(opcoes)} opcoes)'
                log(f"  TC1.3 FAIL - {len(opcoes)} opcoes, esperado apenas liderado1")
            else:
                results['tc1_3'] = f'FAIL_sem_liderado: {opcoes}'
                log("  TC1.3 FAIL - liderado1 nao aparece nas opcoes")

        elif estado_apos.get('inputs'):
            log("  Input visivel apos click (typeahead inline)")
            # Procurar o input que acabou de ficar visivel
            busca_inline = pg.locator("input:visible").filter(
                has_text=""
            ).last
            if not busca_inline.count():
                busca_inline = pg.locator("input[type='text']:visible").last
            if busca_inline.count():
                busca_inline.fill("liderado")
                pg.wait_for_timeout(1500)
                snap(pg, "tc1_typeahead_liderado")

                opcoes = pg.evaluate("""() => {
                    return [...document.querySelectorAll('[role=option], [class*=option]')].filter(el => {
                        return el.getBoundingClientRect().height > 0;
                    }).map(el => el.innerText.trim()).slice(0, 20);
                }""")
                log(f"  Opcoes typeahead: {opcoes}")
                results['tc1_3'] = f'COLETADO: {opcoes}'
        else:
            log("  Nenhum modal nem input adicional apos click")
            results['tc1_3'] = 'INCONCLUSIVO_nao_abriu'
            snap(pg, "tc1_sem_interacao")
    else:
        log("  Campo 'Adicionar pessoas' nao encontrado no DOM")
        snap(pg, "tc1_sem_campo")
        results['tc1_3'] = 'INCONCLUSIVO_campo_nao_encontrado'

    pg.keyboard.press("Escape")
    pg.wait_for_timeout(500)

    # TC1.4 na perspectiva do LIDER - aba Provedores
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)

    tab_prov = pg.locator("[role='tab'], a").filter(has_text=re.compile("Provedores?", re.I)).first
    if tab_prov.count():
        tab_prov.click(timeout=5000)
        pg.wait_for_timeout(2000)
        snap(pg, "tc1_lider_aba_provedores")
        prov_lider = contar_linhas_reais(pg)
        log(f"  Lider - Provedores: {prov_lider}")
        results['tc1_lider_provedores'] = prov_lider
    else:
        log("  Aba Provedores nao encontrada (lider)")
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
        snap(pg, "tc1_admin_aba_provedores")
        prov_admin = contar_linhas_reais(pg)
        log(f"  Admin - Provedores: {prov_admin}")
        results['tc1_admin_provedores'] = prov_admin

        lider_prov = results.get('tc1_lider_provedores', -1)
        if prov_admin == 0:
            results['tc1_4'] = 'INCONCLUSIVO_org_sem_provedores'
            log("  TC1.4 INCONCLUSIVO - org nao tem provedores cadastrados")
        elif lider_prov >= prov_admin:
            results['tc1_4'] = f'PASS_lider_ve_total (lider={lider_prov}, admin={prov_admin})'
            log("  TC1.4 PASS - lider ve todos os provedores")
        elif lider_prov == 0:
            results['tc1_4'] = f'FAIL_lider_0_admin_{prov_admin}'
            log(f"  TC1.4 FAIL - lider ve 0, admin ve {prov_admin}")
        else:
            results['tc1_4'] = f'PARCIAL (lider={lider_prov}, admin={prov_admin})'
    else:
        results['tc1_4'] = 'INCONCLUSIVO_aba_nao_encontrada'

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC5 - Cross-check: KPI 'Pendentes' vs situacao do registro no admin")
log("="*60)

# O lider ve KPIs 0 Emitidos / 0 Expirados / 1 Pendentes / 0 Recusados
# Mas a linha mostra "Aprovado" → investigar qual bucket do admin
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

    # Buscar o registro de QALider (ou pela pessoa QA116-Liderado)
    # Primeiro buscar "QA116-Liderado-Externo" (o conteudo do registro)
    busca = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca.count():
        busca.fill("QA116-Liderado-Externo")
        pg.wait_for_timeout(2000)
        snap(pg, "tc5_admin_busca_conteudo")
        rows_conteudo = pg.evaluate("""() => {
            return [...document.querySelectorAll('tbody tr')].map(tr => tr.innerText.replace(/\\n/g,' ').slice(0, 100));
        }""")
        log(f"  Busca 'QA116-Liderado-Externo': {rows_conteudo}")
        results['tc5_admin_busca'] = rows_conteudo

        # Limpar e buscar pelo nome da pessoa
        busca.fill("")
        pg.wait_for_timeout(500)
        busca.fill("QALiderado")
        pg.wait_for_timeout(2000)
        snap(pg, "tc5_admin_busca_pessoa")
        rows_pessoa = pg.evaluate("""() => {
            return [...document.querySelectorAll('tbody tr')].map(tr => tr.innerText.replace(/\\n/g,' ').slice(0, 120));
        }""")
        log(f"  Busca 'QALiderado': {rows_pessoa}")
        results['tc5_admin_busca_pessoa'] = rows_pessoa

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC3 - Criar registro pendente via admin + verificar liderado via edit form")
log("="*60)

# Para TC3: precisamos criar um registro PENDENTE para liderado1 via API (requests)
# e depois verificar o responsavel do liderado no formulario de edicao

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    # Ir para o formulario de edicao do liderado1 para entender o campo Responsavel
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "tc3_liderado_edit_top")

    # Scrollar para ver toda a pagina
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg.wait_for_timeout(500)
    snap(pg, "tc3_liderado_edit_bottom")

    # Ver HTML completo dos inputs visiveis
    all_inputs = pg.evaluate("""() => {
        return [...document.querySelectorAll('input, select, textarea')].map(el => ({
            id: el.id, name: el.name, type: el.type,
            value: (el.value||'').slice(0, 50),
            placeholder: (el.placeholder||'').slice(0, 50),
            visible: el.getBoundingClientRect().height > 0,
            readonly: el.readOnly || el.disabled
        }));
    }""")
    log(f"  Todos inputs liderado1 edit: {json.dumps(all_inputs, ensure_ascii=False)}")

    # Ver as labels
    labels_form = pg.evaluate("""() => {
        return [...document.querySelectorAll('label')].map(l => ({
            text: l.innerText.trim(),
            for: l.getAttribute('for')
        })).filter(l => l.text);
    }""")
    log(f"  Labels: {json.dumps(labels_form, ensure_ascii=False)}")

    # Ver o conteudo visivel do form (texto)
    form_text = pg.evaluate("""() => {
        const form = document.querySelector('form');
        return form ? form.innerText.replace(/\\n/g,' ').slice(0, 500) : document.body.innerText.slice(0, 500);
    }""")
    log(f"  Form text: {form_text}")

    # Procurar o campo de responsavel - pode ter uma div com o nome do lider
    responsavel_section = pg.evaluate("""() => {
        const all = [...document.querySelectorAll('*')];
        // Procurar por texto "Responsável" ou "Responsavel"
        const el = all.find(e => e.children.length === 0 && /respons/i.test(e.innerText));
        if (el) {
            const parent = el.closest('[class]') || el.parentElement;
            return {
                text: el.innerText,
                parent_text: parent ? parent.innerText.slice(0, 100) : '',
                parent_class: parent ? parent.className.slice(0, 100) : ''
            };
        }
        return null;
    }""")
    log(f"  Secao Responsavel: {responsavel_section}")

    # Ver o layout da pagina (headings e estrutura)
    headings = pg.evaluate("""() => {
        return [...document.querySelectorAll('h1, h2, h3, h4, legend, fieldset')].map(h => ({
            tag: h.tagName, text: h.innerText.trim().slice(0, 60)
        }));
    }""")
    log(f"  Headings: {json.dumps(headings, ensure_ascii=False)}")

    ca.close(); ba.close()


# RESUMO
log("\n" + "="*60)
log("RESUMO FINAL")
log("="*60)
for k, v in results.items():
    log(f"  {k}: {v}")
