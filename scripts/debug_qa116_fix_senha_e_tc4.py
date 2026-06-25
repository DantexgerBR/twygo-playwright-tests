# -*- coding: utf-8 -*-
"""
Fix da senha do lider via kebab e execucao correta do TC4.
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
LIDER_ID       = 4299626
INATIVO_ID     = 4299629   # qainativo_tc4_28129 - JA ATIVO pelo print

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log  = lambda *a: print(*a, flush=True)

def snap(pg, nome):
    pg.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True)
    log(f"  [snap] {nome}.png")

def aguardar_registros(pg):
    """Navega para /records e aguarda spinner sumir."""
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=15000)
    except: pass
    # Aguardar spinner de carregamento sumir (max 15s)
    try:
        pg.wait_for_selector("tbody tr", timeout=15000)
    except:
        pass
    pg.wait_for_timeout(2000)

def extrair_kpis_correto(pg):
    """Extrai os KPIs dos 4 cards: Emitidos, Expirados, Pendentes, Recusados."""
    return pg.evaluate("""() => {
        const labels = ['Emitidos', 'Expirados', 'Pendentes', 'Recusados'];
        const result = {};
        labels.forEach(lbl => {
            // Procurar elemento com texto exato do label
            const labelEl = [...document.querySelectorAll('p, span, div')].find(e =>
                e.children.length === 0 && e.innerText.trim() === lbl
            );
            if (labelEl) {
                // Procurar o numero no mesmo card (parent)
                let card = labelEl.parentElement;
                for (let i = 0; i < 4; i++) {
                    const num = card.querySelector('p, span, h2, h3');
                    if (num && /^\\d+$/.test(num.innerText.trim()) && num !== labelEl) {
                        result[lbl] = parseInt(num.innerText.trim());
                        break;
                    }
                    card = card.parentElement;
                }
                if (result[lbl] === undefined) result[lbl] = 'num_nao_encontrado';
            } else {
                result[lbl] = 'label_nao_encontrada';
            }
        });
        return result;
    }""")

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # PARTE 1: Alterar senha do lider via kebab na lista de usuarios
    log("\n=== PARTE 1: Alterar senha do lider ===")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)

    busca = pg.locator("input[placeholder*='Pesquise' i], input[type='search']").first
    if busca.count():
        busca.fill("qaliderpuro")
        pg.wait_for_timeout(2000)
        snap(pg, "fix2_busca_lider")

    # Encontrar linha do lider e clicar no kebab (3 pontinhos)
    rows_lider = pg.locator("tbody tr, [class*='chakra-table'] tr, table tr").filter(
        has_text=re.compile("qaliderpuro", re.I))
    if not rows_lider.count():
        # Tentar busca mais ampla
        rows_lider = pg.locator("tr").filter(has_text="qaliderpuro")

    log(f"  Linhas do lider encontradas: {rows_lider.count()}")

    if rows_lider.count():
        primeira = rows_lider.first
        # O kebab e o icone ":" (three dots)
        kebab_btn = pg.evaluate("""(row) => {
            const btns = [...row.querySelectorAll('button')];
            // Ultimo botao visivel
            const visCandidates = btns.filter(b => {
                const box = b.getBoundingClientRect();
                return box.width > 0 && box.height > 0;
            });
            if (visCandidates.length) {
                const last = visCandidates[visCandidates.length - 1];
                const box = last.getBoundingClientRect();
                return {x: box.x + box.width/2, y: box.y + box.height/2};
            }
            return null;
        }""", primeira.element_handle())

        if kebab_btn:
            pg.mouse.click(kebab_btn['x'], kebab_btn['y'])
            pg.wait_for_timeout(1000)
            snap(pg, "fix2_lider_kebab")

            items = pg.evaluate("""() => {
                return [...document.querySelectorAll('[role="menuitem"]')].map(e => ({
                    text: (e.innerText||'').trim(), id: e.id
                })).filter(i => i.text);
            }""")
            log(f"  Menu items lider: {json.dumps(items, ensure_ascii=False)}")

            # Procurar "Alterar senha" no menu
            senha_item = pg.locator("[role='menuitem']").filter(
                has_text=re.compile("Alterar senha|Senha|Password|Redefinir", re.I)).first
            if senha_item.count():
                box_s = senha_item.bounding_box()
                if box_s:
                    pg.mouse.click(box_s['x']+box_s['width']/2, box_s['y']+box_s['height']/2)
                    pg.wait_for_timeout(1500)
                    snap(pg, "fix2_modal_alterar_senha")
                    log("  Modal de alterar senha aberto")

                    # Preencher campos de senha no modal
                    pwd_fields = pg.locator("input[type='password']")
                    log(f"  Campos password no modal: {pwd_fields.count()}")
                    if pwd_fields.count() >= 1:
                        pwd_fields.nth(0).fill("123456")
                    if pwd_fields.count() >= 2:
                        pwd_fields.nth(1).fill("123456")

                    pg.wait_for_timeout(500)

                    # Confirmar
                    confirmar = pg.locator("button").filter(
                        has_text=re.compile("Confirmar|Salvar|Alterar|OK|Sim", re.I)).first
                    if confirmar.count():
                        box_c = confirmar.bounding_box()
                        if box_c:
                            pg.mouse.click(box_c['x']+box_c['width']/2, box_c['y']+box_c['height']/2)
                            pg.wait_for_timeout(2000)
                            snap(pg, "fix2_senha_alterada")
                            log("  Senha alterada!")
                    else:
                        pg.keyboard.press("Escape")
                        log("  ATENCAO: botao Confirmar nao encontrado")
            else:
                pg.keyboard.press("Escape")
                log("  ATENCAO: item Alterar senha nao encontrado")
        else:
            log("  ATENCAO: kebab do lider nao encontrado via JS")
    else:
        log("  ATENCAO: linha do lider nao encontrada")
        snap(pg, "fix2_sem_lider")

    # PARTE 2: Executar TC4 de forma correta
    log("\n=== PARTE 2: TC4 - Toggle inativar via lista de usuarios ===")

    # Primeiro verificar KPIs ANTES de inativar
    aguardar_registros(pg)
    pg.wait_for_timeout(5000)  # aguardar JS dos KPIs
    snap(pg, "tc4v2_kpis_inicial")

    kpis_antes = extrair_kpis_correto(pg)
    linhas_antes = pg.locator("tbody tr").count()
    log(f"  KPIs iniciais: {json.dumps(kpis_antes, ensure_ascii=False)}")
    log(f"  Linhas iniciais: {linhas_antes}")

    # Buscar registros do inativo para confirmar que aparecem
    busca_rec = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca_rec.count():
        busca_rec.fill("qainativo_tc4_28129")
        pg.wait_for_timeout(2000)
        linhas_inativo_antes = pg.locator("tbody tr").count()
        snap(pg, "tc4v2_busca_inativo_antes")
        log(f"  Registros do inativo ANTES de inativar: {linhas_inativo_antes}")
        busca_rec.fill("")
        pg.wait_for_timeout(1000)

    # Ir para lista de usuarios e inativar o usuario via toggle
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(3000)

    busca_usr = pg.locator("input[placeholder*='Pesquise' i], input[type='search']").first
    if busca_usr.count():
        busca_usr.fill("qainativo_tc4_28129")
        pg.wait_for_timeout(2000)
        snap(pg, "tc4v2_lista_antes_inativar")
        log("  Encontrou usuario para inativar")

    # Encontrar o toggle "Ativo" da primeira linha e clicar
    # O toggle e um chakra-switch na coluna Ativo
    toggle_ativo = pg.evaluate("""() => {
        // Procurar o switch/toggle na linha do usuario
        const switches = [...document.querySelectorAll('.chakra-switch, [role="switch"]')];
        if (switches.length) {
            const sw = switches[0];
            const box = sw.getBoundingClientRect();
            return {x: box.x + box.width/2, y: box.y + box.height/2, checked: sw.getAttribute('data-checked') !== null};
        }
        // Alternativo: input checkbox
        const chks = [...document.querySelectorAll('input[type="checkbox"]')].filter(c => {
            const box = c.getBoundingClientRect();
            return box.width > 0 && box.height > 0;
        });
        if (chks.length) {
            const chk = chks[0];
            const box = chk.getBoundingClientRect();
            return {x: box.x + box.width/2, y: box.y + box.height/2, checked: chk.checked};
        }
        return null;
    }""")
    log(f"  Toggle estado: {toggle_ativo}")

    if toggle_ativo:
        if toggle_ativo.get('checked'):
            log("  Usuario ATIVO. Clicando para INATIVAR...")
            pg.mouse.click(toggle_ativo['x'], toggle_ativo['y'])
            pg.wait_for_timeout(2000)
            snap(pg, "tc4v2_pos_inativar_toggle")

            # Verificar se apareceu modal de confirmacao
            modal = pg.locator("[role='alertdialog'], [role='dialog']").filter(
                has_text=re.compile("Inativar|Confirmar|Desativar|Are you sure", re.I)).first
            if modal.count():
                log("  Modal de confirmacao detectado")
                snap(pg, "tc4v2_modal_confirmacao")
                confirmar_btn = pg.locator("button").filter(
                    has_text=re.compile("Confirmar|Sim|Inativar|OK", re.I)).first
                if confirmar_btn.count():
                    confirmar_btn.click(timeout=5000)
                    pg.wait_for_timeout(2000)

            snap(pg, "tc4v2_lista_pos_inativar")
            log(f"  Toggle apos inativacao - URL: {pg.url}")
        else:
            log("  ATENCAO: usuario ja esta INATIVO (toggle off)")
            # Reativar primeiro
            pg.mouse.click(toggle_ativo['x'], toggle_ativo['y'])
            pg.wait_for_timeout(2000)
            modal = pg.locator("[role='alertdialog'], [role='dialog']").first
            if modal.count():
                confirmar_btn2 = pg.locator("button").filter(
                    has_text=re.compile("Confirmar|Sim|OK|Reativar", re.I)).first
                if confirmar_btn2.count():
                    confirmar_btn2.click(timeout=5000)
                    pg.wait_for_timeout(2000)
            snap(pg, "tc4v2_reativado")
            log("  Reativado. Aguardando 2s para inativar novamente...")
            pg.wait_for_timeout(2000)

            # Inativar
            pg.mouse.click(toggle_ativo['x'], toggle_ativo['y'])
            pg.wait_for_timeout(2000)
            modal2 = pg.locator("[role='alertdialog'], [role='dialog']").first
            if modal2.count():
                confirmar_btn3 = pg.locator("button").filter(
                    has_text=re.compile("Confirmar|Sim|OK|Inativar", re.I)).first
                if confirmar_btn3.count():
                    confirmar_btn3.click(timeout=5000)
                    pg.wait_for_timeout(2000)
            snap(pg, "tc4v2_inativado_segunda_vez")
    else:
        log("  ATENCAO: toggle nao encontrado")

    # Verificar via lista de usuarios se o toggle mudou para cinza
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    if busca_usr.count():
        busca_usr2 = pg.locator("input[placeholder*='Pesquise' i], input[type='search']").first
        busca_usr2.fill("qainativo_tc4_28129")
        pg.wait_for_timeout(2000)
    snap(pg, "tc4v2_lista_verificar_inativo")

    # Verificar estado do toggle apos inativacao
    estado_final = pg.evaluate("""() => {
        const switches = [...document.querySelectorAll('.chakra-switch')];
        return switches.map(sw => ({
            checked: sw.getAttribute('data-checked') !== null,
            class: sw.className.slice(0,60)
        }));
    }""")
    log(f"  Estado toggles apos inativar: {json.dumps(estado_final, ensure_ascii=False)}")

    # PARTE 3: Verificar Registros apos inativacao
    log("\n=== PARTE 3: Verificar Registros apos inativacao ===")
    aguardar_registros(pg)
    pg.wait_for_timeout(6000)  # aguardar JS renderizar completamente
    snap(pg, "tc4v2_registros_pos_inativar")

    kpis_depois = extrair_kpis_correto(pg)
    linhas_depois = pg.locator("tbody tr").count()
    log(f"  KPIs DEPOIS de inativar: {json.dumps(kpis_depois, ensure_ascii=False)}")
    log(f"  Linhas depois: {linhas_depois}")

    # Buscar pelo usuario inativado
    busca_rec2 = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca_rec2.count():
        busca_rec2.fill("qainativo_tc4_28129")
        pg.wait_for_timeout(2000)
        linhas_inativo_depois = pg.locator("tbody tr").count()
        snap(pg, "tc4v2_busca_inativo_depois")
        log(f"  Registros do inativo DEPOIS de inativar: {linhas_inativo_depois}")

        # Verificar msg vazia
        msg_vazia = pg.evaluate("""() => {
            const all = [...document.querySelectorAll('td, p, div')];
            return all.some(e => e.children.length === 0 && /nenhum|no record|sem registro/i.test(e.innerText));
        }""")
        log(f"  Mensagem 'Nenhum registro': {msg_vazia}")
    else:
        linhas_inativo_depois = -1
        msg_vazia = False
        log("  Campo busca nao encontrado")

    # Verificar toggle "mostrar inativos"
    toggle_mostr = pg.locator("button, label").filter(
        has_text=re.compile("Inativ|mostrar inativ|show inact", re.I)).count()
    log(f"  Toggle 'mostrar inativos' presente: {toggle_mostr > 0}")
    snap(pg, "tc4v2_verificar_toggle_mostrar_inativos")

    # VEREDITO TC4
    linhas_inativo_antes_v = locals().get('linhas_inativo_antes', -1)
    log(f"\n  === VEREDITO TC4 ===")
    log(f"  Linhas inativo ANTES: {linhas_inativo_antes_v}")
    log(f"  Linhas inativo DEPOIS: {linhas_inativo_depois}")
    log(f"  Msg vazia: {msg_vazia}")
    log(f"  KPIs antes: {kpis_antes}")
    log(f"  KPIs depois: {kpis_depois}")

    ca.close(); ba.close()

# Testar login do lider com senha 123456
log("\n=== PARTE 4: Testar login do lider ===")
with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    try:
        tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                       "email": LIDER_EMAIL, "senha": "123456"}, admin=True)
        log(f"  [lider] logado com 123456! URL: {pg.url}")
        pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
        try: pg.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        pg.wait_for_timeout(5000)
        snap(pg, "tc5_lider_registros_logado")
    except SystemExit as e:
        log(f"  Login com 123456 falhou: {e}")
        # Tentar senha original
        try:
            tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                           "email": LIDER_EMAIL, "senha": "twygoqa2026"}, admin=True)
            log(f"  [lider] logado com twygoqa2026! URL: {pg.url}")
        except SystemExit as e2:
            log(f"  Ambas as senhas falharam: {e2}")

    ca.close(); ba.close()
