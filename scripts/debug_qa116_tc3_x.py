# -*- coding: utf-8 -*-
"""Encontrar e clicar no X da pill QALider no form de edicao do liderado1."""
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


with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)

    # Fechar chatbot se existir
    try:
        chatbot_close = pg.locator("[class*=popover][class*=close], button.chakra-popover__close-btn").first
        if chatbot_close.count() and chatbot_close.is_visible():
            chatbot_close.click(timeout=2000)
            pg.wait_for_timeout(500)
    except:
        pass

    snap(pg, "tc3_x_before")

    # Obter HTML completo da secao Lideranca
    lideranca_html = pg.evaluate("""() => {
        // Encontrar o container pai da secao Lideranca
        const all = [...document.querySelectorAll('*')];
        const h3 = all.find(e => e.tagName === 'H3' && e.innerText && e.innerText.trim() === 'Liderança');
        if (!h3) return 'H3 nao encontrado';

        // Subir ate encontrar um container relevante
        let container = h3.closest('.form-group, section, fieldset, [class*=section], [class*=panel]');
        if (!container) container = h3.parentElement?.parentElement?.parentElement;
        if (!container) return 'container nao encontrado';

        return container.outerHTML.slice(0, 2000);
    }""")
    log(f"  HTML Lideranca: {lideranca_html[:1000]}")

    # Encontrar todos os elementos dentro da secao Lideranca
    elementos_lideranca = pg.evaluate("""() => {
        const all = [...document.querySelectorAll('*')];
        const h3 = all.find(e => e.tagName === 'H3' && e.innerText && e.innerText.trim() === 'Liderança');
        if (!h3) return [];

        let container = h3.closest('.form-group, section, fieldset') || h3.parentElement?.parentElement?.parentElement;
        if (!container) return [];

        return [...container.querySelectorAll('button, [role=button], svg, [class*=close], [class*=remove], [class*=delete], [class*=clear]')].map(el => {
            const box = el.getBoundingClientRect();
            return {
                tag: el.tagName,
                class: el.className.slice(0, 80),
                innerText: (el.innerText||'').slice(0, 30),
                x: Math.round(box.x),
                y: Math.round(box.y),
                w: Math.round(box.width),
                h: Math.round(box.height),
                visible: box.height > 0
            };
        });
    }""")
    log(f"  Elementos na secao Lideranca: {json.dumps(elementos_lideranca, ensure_ascii=False)}")

    # Encontrar especificamente a pill do responsavel e o X dela
    x_pill = pg.evaluate("""() => {
        const all = [...document.querySelectorAll('*')];

        // Encontrar o container com "QALider" no texto
        const qaEl = all.find(e => e.children.length === 0 && e.innerText && e.innerText.trim() === 'QALider Puro116');
        if (!qaEl) {
            // Buscar mais amplo
            const qaElAmplo = all.find(e => e.innerText && e.innerText.trim().includes('QALider Puro116'));
            if (!qaElAmplo) return null;
        }

        const el = qaEl || all.find(e => e.innerText && e.innerText.trim().includes('QALider Puro116'));
        const pill = el.closest('[class]');

        // Capturar HTML da pill
        const pillHtml = pill ? pill.outerHTML.slice(0, 300) : 'no pill';

        // Procurar buttons e elementos clicaveis dentro da pill
        const clickables = pill ? [...pill.querySelectorAll('button, [role=button], span[class*=close], span[class*=remove]')] : [];
        const clickableInfo = clickables.map(c => {
            const box = c.getBoundingClientRect();
            return {tag: c.tagName, class: c.className.slice(0,60), text: c.innerText, x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width), h: Math.round(box.height)};
        });

        // Também verificar elementos irmãos (o X pode estar fora da pill mas relacionado)
        const parent = pill.parentElement;
        const siblings = parent ? [...parent.querySelectorAll('button, [role=button], [class*=close], svg')] : [];
        const siblingInfo = siblings.map(s => {
            const box = s.getBoundingClientRect();
            return {tag: s.tagName, class: s.className.slice(0,60), text: s.innerText, x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.width), h: Math.round(box.height)};
        }).filter(s => s.x > 0 && s.y > 0);

        return {pillHtml, clickables: clickableInfo, siblings: siblingInfo};
    }""")
    log(f"  X pill info: {json.dumps(x_pill, ensure_ascii=False)}")

    if x_pill:
        clickables = x_pill.get('clickables', [])
        siblings = x_pill.get('siblings', [])
        all_candidates = clickables + siblings
        visibles = [c for c in all_candidates if c.get('h', 0) > 0 and c.get('w', 0) > 0]

        if visibles:
            # Usar o primeiro elemento clicavel (ou o que parecer mais o X)
            target = visibles[0]
            log(f"  Clicando em: {target}")
            pg.mouse.click(target['x'] + target['w']//2, target['y'] + target['h']//2)
            pg.wait_for_timeout(1500)
            snap(pg, "tc3_x_apos_click")

            # Verificar se removeu
            qa_presente = pg.evaluate("""() => {
                return [...document.querySelectorAll('*')].some(e => e.children.length === 0 && e.innerText && e.innerText.trim().includes('QALider'));
            }""")
            log(f"  QALider ainda presente: {qa_presente}")
            results['qa_presente_apos_click'] = qa_presente
        else:
            log("  Nenhum elemento clicavel encontrado na pill")
            # Fallback: usar coordenadas absolutas do X visivel no screenshot
            # Com viewport 1366x768, a pill fica em area y≈870. O X fica mais a direita
            # Verificar tamanho da janela
            viewport = pg.evaluate("() => ({w: window.innerWidth, h: window.innerHeight})")
            log(f"  Viewport: {viewport}")
            # X da pill provavelmente em: x=790, y=870
            pg.mouse.click(790, 870)
            pg.wait_for_timeout(1000)
            snap(pg, "tc3_x_coord_click")
    else:
        log("  x_pill retornou null - QALider nao encontrado no DOM")
        results['tc3'] = 'INCONCLUSIVO_pill_nao_encontrada'

    # Verificar estado atual
    qa_presente = pg.evaluate("""() => {
        return [...document.querySelectorAll('*')].some(e => e.children.length === 0 && e.innerText && e.innerText.trim().includes('QALider'));
    }""")
    log(f"  QALider presente apos todas as tentativas: {qa_presente}")
    results['qa_presente_final'] = qa_presente

    if not qa_presente:
        # Salvar
        log("  Responsavel removido! Salvando...")
        save_btn = pg.evaluate("""() => {
            const btns = [...document.querySelectorAll('button, input[type=submit]')];
            const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
            if (s) { const box = s.getBoundingClientRect(); return {x: box.x+box.width/2, y: box.y+box.height/2}; }
            return null;
        }""")
        if save_btn:
            pg.mouse.click(save_btn['x'], save_btn['y'])
            pg.wait_for_timeout(4000)
            snap(pg, "tc3_x_salvo")
            results['tc3_salvo'] = True
    else:
        log("  Nao foi possivel remover o responsavel via UI. TC3 = INCONCLUSIVO")
        results['tc3'] = 'INCONCLUSIVO_X_nao_clicavel'

    ca.close(); ba.close()


# Verificar resultado
if results.get('tc3_salvo'):
    log("\n  Verificando admin e lider pos-remocao...")
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

        snap(pg_admin, "tc3_x_admin_pos")
        n_admin = contar_linhas_reais(pg_admin)
        log(f"  Admin ve {n_admin} registros de liderado")
        results['tc3_n_admin'] = n_admin

        login_lider(pg_lider)
        snap(pg_lider, "tc3_x_lider_pos")
        n_lider = contar_linhas_reais(pg_lider)
        kpis = extrair_kpis(pg_lider)
        log(f"  Lider ve {n_lider} registros, KPIs: {kpis}")
        results['tc3_n_lider'] = n_lider

        if n_admin > 0 and n_lider == 0:
            results['tc3'] = 'PASS'
            log("  TC3 PASS!")
        elif n_admin == 0:
            results['tc3'] = 'FAIL_registro_sumiu_do_admin'
        elif n_lider > 0:
            results['tc3'] = f'FAIL_lider_ainda_ve_{n_lider}'

        ca.close(); ba.close()
        ca2.close(); ba2.close()

    # RESTAURAR
    log("\n  RESTAURANDO responsavel do liderado1...")
    with tw.sync_playwright() as p:
        ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
        tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                       "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

        pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
                wait_until="domcontentloaded", timeout=30000)
        try: pg.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        pg.wait_for_timeout(2000)
        snap(pg, "restore_x_before")

        # Clicar na area responsavel para ativar busca
        resp_area = pg.evaluate("""() => {
            const all = [...document.querySelectorAll('*')];
            const label = all.find(e => e.children.length === 0 && e.innerText && e.innerText.trim() === 'Responsável');
            if (!label) return null;
            // Pegar o container mais proximo que contenha o campo de selecao
            const container = label.closest('[class]') || label.parentElement;
            const box = container.getBoundingClientRect();
            return {x: box.x + box.width/2, y: box.y + box.height + 10};  // clicar logo abaixo do label
        }""")
        log(f"  Area responsavel: {resp_area}")

        if resp_area:
            pg.mouse.click(resp_area['x'], resp_area['y'])
            pg.wait_for_timeout(1500)
            snap(pg, "restore_x_click")

            # Agora digitar o nome do lider
            pg.keyboard.type("qaliderpuro")
            pg.wait_for_timeout(1500)
            snap(pg, "restore_x_busca")

            opcao = pg.locator("[role='option']").filter(has_text=re.compile("qaliderpuro|QALider", re.I)).first
            if opcao.count():
                opcao.click(timeout=5000)
                pg.wait_for_timeout(1000)
                log("  Responsavel restaurado!")
            else:
                log("  Opcao do lider nao encontrada!")

        # Salvar
        save = pg.evaluate("""() => {
            const btns = [...document.querySelectorAll('button, input[type=submit]')];
            const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
            if (s) { s.click(); return true; }
            return false;
        }""")
        pg.wait_for_timeout(3000)
        snap(pg, "restore_x_salvo")
        log(f"  Salvo: {save}, URL: {pg.url}")

        ca.close(); ba.close()


log("\n" + "="*60)
log("SUMARIO")
for k, v in results.items():
    log(f"  {k}: {v}")
