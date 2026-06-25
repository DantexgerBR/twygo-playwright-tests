# -*- coding: utf-8 -*-
"""
TC3 - Remover QALider como Responsavel do liderado1 e verificar
TC5 - Esclarecimento do KPI "Pendentes" vs situacao "Aprovado"
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
log("TC5 - Esclarecer semantica do KPI 'Pendentes' vs 'Aprovado'")
log("="*60)

# Verificar: admin vê o mesmo registro como "Aprovado" mas o KPI do lider diz "Pendentes"
# Isso pode ser diferenca semantica (pendente de emissao de certificado != aprovacao)
# Ou o KPI conta de forma diferente

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

    # Filtrar pelo conteudo do registro do lider
    busca = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca.count():
        busca.fill("QA116-Liderado-Externo")
        pg.wait_for_timeout(2000)

    # Capturar todos os dados da linha
    row_completo = pg.evaluate("""() => {
        const rows = [...document.querySelectorAll('tbody tr')];
        return rows.map(tr => {
            const cells = [...tr.querySelectorAll('td')];
            return cells.map(td => ({
                class: td.className.slice(0, 40),
                text: td.innerText.trim().replace(/\\n/g,' ').slice(0, 80)
            }));
        });
    }""")
    log(f"  Linha completa no admin: {json.dumps(row_completo, ensure_ascii=False)}")

    # Ver colunas do cabecalho
    headers = pg.evaluate("""() => {
        return [...document.querySelectorAll('thead th')].map(th => th.innerText.trim().replace(/\\n/g,' ')).filter(t => t);
    }""")
    log(f"  Cabecalhos: {headers}")
    snap(pg, "tc5_admin_linha_completa")

    # KPIs admin
    kpis_admin = extrair_kpis(pg)
    log(f"  KPIs admin: {kpis_admin}")

    # Clicar no kebab da linha para ver o menu (para identificar a situacao real)
    row = pg.locator("tbody tr").first
    if row.count():
        situacao_text = row.evaluate("""(tr) => {
            // Verificar o badge de situacao
            const badges = [...tr.querySelectorAll('[class*=badge], [class*=tag], [class*=status], [class*=chip]')];
            return badges.map(b => b.innerText.trim());
        }""")
        log(f"  Badges de situacao: {situacao_text}")

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*60)
log("TC3 - Identificar e clicar no X da pill do Responsavel")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    # Estado ANTES: confirmar que lider ve 1 registro
    log("  [TC3] Estado ANTES...")
    snap_lider_antes = None

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)

    # Fechar o chatbot se abrir
    chatbot = pg.locator("[class*=chat], [class*=support]").filter(
        has_text=re.compile("pronto|atender", re.I)).first
    if chatbot.count():
        close_chat = chatbot.locator("button").first
        if close_chat.count():
            try: close_chat.click(timeout=2000)
            except: pass
    pg.wait_for_timeout(500)

    snap(pg, "tc3v4_before_edit")

    # Inspecionar o elemento X da pill "QALider Puro116"
    # O screenshot mostra: pill com avatar + "QALider Puro116" + x no canto superior direito
    # Baseado na estrutura Chakra UI, o X costuma ser um button com [data-testid="dismiss-badge"]
    # ou um span com classe "chakra-tag__close-button"

    pill_info = pg.evaluate("""() => {
        // Abordagem 1: chakra tag close button
        const closeButtons = [...document.querySelectorAll('[class*=tag][class*=close], button[class*=close], [aria-label*=remove i], [aria-label*=remover i]')];
        if (closeButtons.length) {
            return closeButtons.map(b => {
                const box = b.getBoundingClientRect();
                return {strategy: 'close-button', x: box.x + box.width/2, y: box.y + box.height/2, text: b.innerText, class: b.className};
            }).filter(b => b.x > 0 && b.y > 0);
        }

        // Abordagem 2: encontrar o container da pill do responsavel e localizar o ultimo filho
        const all = [...document.querySelectorAll('[class]')];
        const pill = all.find(e => {
            const box = e.getBoundingClientRect();
            return box.height > 0 && e.innerText && e.innerText.trim().includes('QALider') && box.height < 60 && box.width < 400;
        });
        if (pill) {
            const children = [...pill.querySelectorAll('*')];
            const lastInteractive = children.reverse().find(c => {
                const box = c.getBoundingClientRect();
                return box.height > 0 && c.tagName !== 'IMG';
            });
            if (lastInteractive) {
                const box = lastInteractive.getBoundingClientRect();
                return [{strategy: 'pill-last-child', x: box.x + box.width/2, y: box.y + box.height/2, text: lastInteractive.innerText, class: lastInteractive.className, tag: lastInteractive.tagName}];
            }
            // Retornar info da pill inteira
            const pbox = pill.getBoundingClientRect();
            return [{strategy: 'pill-right-edge', x: pbox.x + pbox.width - 8, y: pbox.y + pbox.height/2, text: pill.innerText, class: pill.className}];
        }

        return [{strategy: 'nao-encontrado'}];
    }""")
    log(f"  Pill info: {json.dumps(pill_info, ensure_ascii=False)}")

    # Verificar se a secao Lideranca esta visivel (precisa scrollar)
    pg.evaluate("document.querySelector('[class]')?.scrollTo ? null : window.scrollTo(0, 800)")
    pg.wait_for_timeout(500)
    snap(pg, "tc3v4_scroll_lideranca")

    # Usar outra abordagem: capturar HTML da secao Lideranca
    lideranca_html = pg.evaluate("""() => {
        const all = [...document.querySelectorAll('*')];
        const h = all.find(e => e.children.length === 0 && e.innerText && e.innerText.trim() === 'Liderança');
        if (!h) return 'header nao encontrado';
        const section = h.closest('[class]') || h.parentElement;
        return section ? section.outerHTML.slice(0, 500) : 'section nao encontrada';
    }""")
    log(f"  Lideranca HTML: {lideranca_html}")

    # Tentar clicar com coordenadas do JS
    if pill_info and pill_info[0].get('strategy') != 'nao-encontrado':
        target = pill_info[0]
        log(f"  Clicando em: {target}")
        pg.mouse.click(target['x'], target['y'])
        pg.wait_for_timeout(1500)
        snap(pg, "tc3v4_apos_click_x")

        # Verificar se o responsavel foi removido
        responsavel_presente = pg.evaluate("""() => {
            const all = [...document.querySelectorAll('*')];
            return all.some(e => e.innerText && /QALider|Puro116/i.test(e.innerText) && e.getBoundingClientRect().height > 0 && e.children.length === 0);
        }""")
        log(f"  Responsavel ainda presente: {responsavel_presente}")

        if not responsavel_presente:
            log("  Responsavel removido com sucesso!")
        else:
            log("  Responsavel ainda presente - tentando via keyboard")
            # Tentar tab para o X e Enter
            # Ou usar evaluate para invocar o click
            clicked = pg.evaluate("""() => {
                // Procurar button mais proximo da pill com QALider
                const all = [...document.querySelectorAll('button, [role=button]')];
                for (const btn of all) {
                    const parent = btn.closest('[class]');
                    if (parent && parent.innerText && /QALider|Puro116/i.test(parent.innerText)) {
                        const box = btn.getBoundingClientRect();
                        if (box.height > 0) { btn.click(); return {clicked: true, text: btn.innerText}; }
                    }
                }
                return {clicked: false};
            }""")
            log(f"  Clique via evaluate: {clicked}")
            pg.wait_for_timeout(1000)
            snap(pg, "tc3v4_apos_evaluate_click")
    else:
        log("  Pill nao encontrada, tentando coordenadas absolutas baseadas no screenshot...")
        # Do screenshot anterior, a pill "QALider Puro116" fica em y≈870 e o X em x≈787, y≈862
        # (valores para viewport 1366x768)
        # Scrollar primeiro para garantir visibilidade
        pg.evaluate("window.scrollBy(0, 600)")
        pg.wait_for_timeout(1000)
        snap(pg, "tc3v4_scrolled")

        # Tentar click em posicao da pill
        pg.mouse.click(787, 862)
        pg.wait_for_timeout(1000)
        snap(pg, "tc3v4_click_coord")

    # Verificar estado final e salvar
    responsavel_final = pg.evaluate("""() => {
        return [...document.querySelectorAll('*')].some(e => e.innerText && /QALider|Puro116/i.test(e.innerText) && e.getBoundingClientRect().height > 0 && e.children.length === 0);
    }""")
    log(f"  Responsavel apos tentativas: {responsavel_final}")
    results['tc3_responsavel_presente'] = responsavel_final

    if not responsavel_final:
        # Salvar
        save_btn = pg.evaluate("""() => {
            const btns = [...document.querySelectorAll('button, input[type=submit]')];
            const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
            if (s) { const box = s.getBoundingClientRect(); return {x: box.x+box.width/2, y: box.y+box.height/2}; }
            return null;
        }""")
        if save_btn:
            pg.mouse.click(save_btn['x'], save_btn['y'])
            pg.wait_for_timeout(4000)
            snap(pg, "tc3v4_salvo")
            log(f"  URL pos salvar: {pg.url}")
            results['tc3_salvo'] = True
        else:
            log("  Botao Salvar nao encontrado!")
    else:
        log("  Nao foi possivel remover o responsavel - TC3 INCONCLUSIVO")
        results['tc3'] = 'INCONCLUSIVO_X_nao_removivel'

    ca.close(); ba.close()


# Apenas continuar se conseguiu remover
if results.get('tc3') != 'INCONCLUSIVO_X_nao_removivel' and not results.get('tc3_responsavel_presente', True):
    log("\n  [TC3] Verificando persistencia do registro (admin) e invisibilidade (lider)...")
    time.sleep(3)

    with tw.sync_playwright() as p:
        ba, ca, pg_admin = tw.nova_pagina(p, slow_mo=300)
        ba2, ca2, pg_lider = tw.nova_pagina(p, slow_mo=300)

        tw.login(pg_admin, {"base_url": BASE_URL, "org_id": ORG_ID,
                             "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
        pg_admin.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
        try: pg_admin.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        try: pg_admin.wait_for_selector("tbody tr", timeout=8000)
        except: pass
        pg_admin.wait_for_timeout(3000)

        busca = pg_admin.locator("input[placeholder*='Pesquise' i]").first
        if busca.count():
            busca.fill("liderado")
            pg_admin.wait_for_timeout(2000)

        snap(pg_admin, "tc3v4_admin_pos_remocao")
        n_admin = contar_linhas_reais(pg_admin)
        log(f"  Admin ve {n_admin} registros de liderado")
        results['tc3_n_admin_pos'] = n_admin

        login_lider(pg_lider)
        snap(pg_lider, "tc3v4_lider_pos_remocao")
        n_lider = contar_linhas_reais(pg_lider)
        kpis = extrair_kpis(pg_lider)
        log(f"  Lider ve {n_lider} registros, KPIs: {kpis}")
        results['tc3_n_lider_pos'] = n_lider
        results['tc3_kpis_lider_pos'] = kpis

        if n_admin > 0 and n_lider == 0:
            results['tc3'] = 'PASS'
            log("  TC3 PASS - Registro persiste para admin; lider nao ve mais")
        elif n_admin == 0:
            results['tc3'] = 'FAIL_registro_sumiu_do_admin'
        else:
            results['tc3'] = f'FAIL_lider_ainda_ve_{n_lider}'
            log(f"  TC3 FAIL - Lider ainda ve {n_lider} registros")

        ca.close(); ba.close()
        ca2.close(); ba2.close()

    # RESTAURAR responsavel
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
        snap(pg, "restore_v4_before")

        # Verificar se o campo responsavel esta vazio agora
        resp_status = pg.evaluate("""() => {
            const all = [...document.querySelectorAll('*')];
            const qaEl = all.find(e => e.innerText && /QALider|Puro116/i.test(e.innerText) && e.getBoundingClientRect().height > 0 && e.children.length === 0);
            return {qaLiderPresente: !!qaEl};
        }""")
        log(f"  Estado responsavel: {resp_status}")

        if not resp_status.get('qaLiderPresente'):
            # Clicar na area do responsavel para buscar
            resp_area = pg.evaluate("""() => {
                const h = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && e.innerText && e.innerText.trim() === 'Responsável');
                if (!h) return null;
                const section = h.closest('[class]') || h.parentElement;
                if (section) {
                    const box = section.getBoundingClientRect();
                    return {x: box.x + box.width/2, y: box.y + box.height/2};
                }
                return null;
            }""")
            if resp_area:
                pg.mouse.click(resp_area['x'], resp_area['y'])
                pg.wait_for_timeout(1500)
                snap(pg, "restore_v4_click_area")

            # Ver o que apareceu (typeahead ou input)
            new_inputs = pg.evaluate("""() => {
                return [...document.querySelectorAll('input')].filter(i => {
                    const box = i.getBoundingClientRect();
                    return box.height > 0 && i.type !== 'checkbox' && i.type !== 'radio' && i.type !== 'hidden' && i.type !== 'date';
                }).map(i => ({id: i.id, placeholder: i.placeholder, value: i.value}));
            }""")
            log(f"  Inputs disponiveis: {json.dumps(new_inputs, ensure_ascii=False)}")

            # Usar o input de busca se houver um novo (sem ID bem definido)
            # Tipico: o input de busca do responsavel aparece como input vazio após o click
            for inp in new_inputs:
                if not inp.get('value') and inp.get('id', '').startswith('react-select'):
                    pg.fill(f"#{inp['id']}", "qaliderpuro")
                    pg.wait_for_timeout(1500)
                    snap(pg, "restore_v4_busca")

                    opcao = pg.locator("[role='option']").filter(has_text=re.compile("qaliderpuro|QALider", re.I)).first
                    if opcao.count():
                        opcao.click(timeout=5000)
                        pg.wait_for_timeout(1000)
                        log("  Responsavel restaurado!")
                    break

        # Salvar
        save_btn = pg.evaluate("""() => {
            const btns = [...document.querySelectorAll('button, input[type=submit]')];
            const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
            if (s) { s.click(); return true; }
            return false;
        }""")
        pg.wait_for_timeout(3000)
        snap(pg, "restore_v4_salvo")
        log(f"  Salvar: {save_btn}, URL: {pg.url}")

        ca.close(); ba.close()


# SUMARIO
log("\n" + "="*60)
log("SUMARIO FINAL TC3 + TC5")
for k, v in results.items():
    log(f"  {k}: {v}")
