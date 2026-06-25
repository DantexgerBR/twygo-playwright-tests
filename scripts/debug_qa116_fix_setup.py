# -*- coding: utf-8 -*-
"""
Diagnotico e correcao do setup para QA 1.16:
1. Verificar/resetar senha do lider qaliderpuro
2. Verificar como funciona inativacao de usuario nesta org
3. Aguardar carregamento completo de Registros
"""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
LIDER_ID       = 4299626
INATIVO_ID     = 4299629

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log  = lambda *a: print(*a, flush=True)

def snap(pg, nome):
    pg.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True)
    log(f"  [snap] {nome}.png")

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # 1. Resetar senha do lider para 123456 (senha padrao de teste)
    log("\n--- 1. Resetar senha do lider ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDER_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "fix_lider_edit_form")

    # Procurar campo de senha
    senha_fields = pg.evaluate("""() => {
        return [...document.querySelectorAll('input[type="password"]')].map(i => ({
            id: i.id, name: i.name, placeholder: i.placeholder
        }));
    }""")
    log(f"  Campos password: {json.dumps(senha_fields, ensure_ascii=False)}")

    if senha_fields:
        # Preencher nova senha
        pg.locator("input[type='password']").nth(0).fill("123456")
        if len(senha_fields) > 1:
            pg.locator("input[type='password']").nth(1).fill("123456")
        pg.wait_for_timeout(500)

        # Salvar
        save = pg.evaluate("""() => {
            const btns = [...document.querySelectorAll('button, input[type=submit]')];
            const salvar = btns.find(b => /salvar|save|atualizar/i.test(b.innerText || b.value || ''));
            if (salvar) { const box = salvar.getBoundingClientRect(); return {x: box.x + box.width/2, y: box.y + box.height/2}; }
            return null;
        }""")
        if save:
            pg.mouse.click(save['x'], save['y'])
            pg.wait_for_timeout(3000)
            snap(pg, "fix_lider_senha_salva")
            log(f"  Senha salva. URL: {pg.url}")
    else:
        log("  ATENCAO: nao encontrou campos de senha")

    # 2. Ver como funciona inativacao nessa org - explorar a tela de lista de usuarios
    log("\n--- 2. Explorar inativacao de usuario ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)
    snap(pg, "fix_lista_usuarios")

    # Procurar o usuario inativo na lista
    busca = pg.locator("input[placeholder*='Pesquise' i], input[type='search']").first
    if busca.count():
        busca.fill("qainativo_tc4")
        pg.wait_for_timeout(2000)
        snap(pg, "fix_busca_inativo")
        log(f"  Buscou por qainativo_tc4")

    # Ver opcoes no kebab do usuario inativo
    rows = pg.locator("tbody tr, [class*='row']")
    if rows.count():
        log(f"  Encontrou {rows.count()} linhas")
        # Verificar se ha indicador de status na linha
        primeira_linha = rows.first
        linha_html = pg.evaluate("""(el) => el.outerHTML.slice(0, 500)""", primeira_linha.element_handle())
        log(f"  HTML linha: {linha_html}")

        # Tentar kebab
        kebab = primeira_linha.locator("button[aria-label*='more' i], button svg, button").last
        box_k = kebab.bounding_box()
        if box_k:
            pg.mouse.click(box_k['x']+box_k['width']/2, box_k['y']+box_k['height']/2)
            pg.wait_for_timeout(1000)
            snap(pg, "fix_inativo_kebab_lista")

            items = pg.evaluate("""() => {
                return [...document.querySelectorAll('[role="menuitem"]')].map(e => ({
                    text: (e.innerText||'').trim(), id: e.id
                })).filter(i => i.text);
            }""")
            log(f"  Menu items do inativo: {json.dumps(items, ensure_ascii=False)}")

            pg.keyboard.press("Escape")
    else:
        log("  ATENCAO: nao encontrou linhas na lista")

    # Ir para a pagina de edicao do inativo e ver TODOS os campos
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{INATIVO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)

    # Extrair TODOS os inputs/checkboxes/selects
    todos_campos = pg.evaluate("""() => {
        const inputs = [...document.querySelectorAll('input, select, textarea')];
        return inputs.map(i => ({
            type: i.type, id: i.id, name: i.name,
            value: i.value ? i.value.slice(0,30) : '',
            checked: i.checked,
            placeholder: (i.placeholder||'').slice(0,30),
            visible: i.getBoundingClientRect().height > 0
        })).filter(i => i.visible);
    }""")
    log(f"\n  Campos no form do inativo:\n{json.dumps(todos_campos, ensure_ascii=False, indent=2)}")
    snap(pg, "fix_inativo_form_completo")

    # Scrollar ate o fim para ver se tem algo escondido
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg.wait_for_timeout(1000)
    snap(pg, "fix_inativo_form_bottom")

    # 3. Aguardar carregamento completo da pagina de Registros
    log("\n--- 3. Testar carregamento completo da pagina Registros ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=15000)
    except: pass
    pg.wait_for_timeout(5000)  # aguardar JS renderizar

    # Verificar se o spinner sumiu
    spinner = pg.locator("[class*='spinner'], [class*='loading'], svg[class*='spin']").count()
    log(f"  Spinner apos 5s: {spinner}")

    # Extrair KPIs reais
    kpis = pg.evaluate("""() => {
        // Tentar pelos cards de stat
        const cards = [...document.querySelectorAll('.chakra-stat__number, [class*="number"], .chakra-stat dd')];
        if (cards.length) return cards.map(c => ({text: c.innerText.trim(), class: c.className.slice(0,40)}));

        // Fallback: numeros grandes
        const all = [...document.querySelectorAll('*')].filter(e =>
            e.children.length === 0 && /^\\d+$/.test((e.innerText||'').trim()) &&
            e.getBoundingClientRect().height > 0
        );
        return all.map(e => ({text: e.innerText.trim(), tag: e.tagName, class: e.className.slice(0,40)})).slice(0,10);
    }""")
    log(f"  KPIs reais: {json.dumps(kpis, ensure_ascii=False)}")
    snap(pg, "fix_registros_carregado")

    # Verificar tbody
    tbody = pg.locator("tbody tr").count()
    log(f"  Linhas na tabela: {tbody}")

    # Mostrar texto completo dos KPI cards
    kpi_cards_text = pg.evaluate("""() => {
        // Procurar os 4 cards de KPI especificos (Emitidos, Expirados, Pendentes, Recusados)
        const labels = ['Emitidos', 'Expirados', 'Pendentes', 'Recusados'];
        const result = {};
        labels.forEach(lbl => {
            const el = [...document.querySelectorAll('*')].find(e =>
                e.children.length === 0 && e.innerText.trim() === lbl
            );
            if (el) {
                const card = el.closest('.chakra-stat, [class*="stat-"], [class*="card"]') || el.parentElement;
                const num = card ? card.querySelector('[class*="number"], dd, h2, h3') : null;
                result[lbl] = num ? num.innerText.trim() : 'num_nao_encontrado';
            } else {
                result[lbl] = 'label_nao_encontrada';
            }
        });
        return result;
    }""")
    log(f"  KPI por label: {json.dumps(kpi_cards_text, ensure_ascii=False)}")

    ca.close(); ba.close()
