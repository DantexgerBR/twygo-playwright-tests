# -*- coding: utf-8 -*-
"""
Fix senha lider + TC4 correto.
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
INATIVO_ID     = 4299629   # qainativo_tc4_28129

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log  = lambda *a: print(*a, flush=True)

def snap(pg, nome):
    pg.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True)
    log(f"  [snap] {nome}.png")

def aguardar_registros(pg):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=15000)
    except: pass
    try: pg.wait_for_selector("tbody tr, .chakra-stat", timeout=10000)
    except: pass
    pg.wait_for_timeout(4000)

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
            } else {
                result[lbl] = -1;
            }
        });
        return result;
    }""")

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=600)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # ==== PARTE 1: Resetar senha do lider via "Alterar senha" ====
    log("\n=== PARTE 1: Resetar senha do lider ===")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)

    busca = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca.count():
        busca.fill("qaliderpuro")
        pg.wait_for_timeout(2000)

    # Abrir kebab do lider via bounding box do botao de 3 pontos (last button na linha)
    botao_kebab = pg.evaluate("""() => {
        const rows = [...document.querySelectorAll('tbody tr, [class*="chakra-table"] tr')];
        for (const row of rows) {
            if (row.innerText.includes('qaliderpuro')) {
                const btns = [...row.querySelectorAll('button')].filter(b => {
                    const box = b.getBoundingClientRect();
                    return box.width > 0 && box.height > 0;
                });
                if (btns.length) {
                    const last = btns[btns.length - 1];
                    const box = last.getBoundingClientRect();
                    return {x: box.x + box.width/2, y: box.y + box.height/2};
                }
            }
        }
        return null;
    }""")
    log(f"  botao_kebab: {botao_kebab}")
    if botao_kebab:
        pg.mouse.click(botao_kebab['x'], botao_kebab['y'])
        pg.wait_for_timeout(1000)
        # Clicar em Alterar senha
        tw.click_menuitem(pg, "Alterar senha")
        pg.wait_for_timeout(2000)
        snap(pg, "fix3_alterar_senha_resultado")
        log(f"  URL apos alterar senha: {pg.url}")

        # Verificar se redirecionou para pagina de senha ou abriu modal
        if "/password" in pg.url or "/senha" in pg.url:
            log("  Redirecionou para pagina de senha")
            pwd = pg.locator("input[type='password']")
            log(f"  Campos password: {pwd.count()}")
            if pwd.count() >= 1:
                pwd.nth(0).fill("123456")
            if pwd.count() >= 2:
                pwd.nth(1).fill("123456")
            # Salvar
            save = pg.locator("button[type='submit'], input[type='submit']").first
            if save.count(): save.click(timeout=5000)
            pg.wait_for_timeout(2000)
            snap(pg, "fix3_senha_salva")
        else:
            # Verificar se ha modal aberto
            modal = pg.locator("[role='dialog'], [role='alertdialog'], .chakra-modal__content")
            if modal.count():
                log("  Modal aberto")
                snap(pg, "fix3_modal_senha")
                # Procurar inputs no modal
                inputs_modal = pg.evaluate("""() => {
                    const modal = document.querySelector('[role="dialog"], .chakra-modal__content');
                    if (!modal) return [];
                    return [...modal.querySelectorAll('input')].map(i => ({
                        type: i.type, id: i.id, placeholder: i.placeholder, value: i.value
                    }));
                }""")
                log(f"  Inputs no modal: {json.dumps(inputs_modal, ensure_ascii=False)}")
            else:
                log(f"  Sem modal e sem redirect para /password. URL: {pg.url}")
                # Ver texto da pagina atual
                texto = pg.evaluate("() => document.body.innerText.slice(0, 500)")
                log(f"  Texto da pagina: {texto[:200]}")

    # ==== PARTE 2: TC4 - Inativar e verificar registros ====
    log("\n=== PARTE 2: TC4 - Registros somem quando usuario e inativado ===")

    # KPIs ANTES de qualquer inativacao
    aguardar_registros(pg)
    pg.wait_for_timeout(6000)
    snap(pg, "tc4v3_registros_inicial")

    kpis_antes = extrair_kpis(pg)
    linhas_antes = pg.locator("tbody tr").count()
    log(f"  KPIs totais ANTES: {json.dumps(kpis_antes, ensure_ascii=False)}")
    log(f"  Linhas na tabela: {linhas_antes}")

    # Buscar registros especificos do usuario para confirmar que existem
    busca_reg = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca_reg.count():
        busca_reg.fill("QAInativo TC4-28129")
        pg.wait_for_timeout(2000)
        linhas_inativo_antes = pg.locator("tbody tr").count()
        snap(pg, "tc4v3_busca_inativo_antes")
        log(f"  Linhas registros do inativo ANTES: {linhas_inativo_antes}")

        # Ver nomes dos registros
        nomes_regs = pg.evaluate("""() => {
            return [...document.querySelectorAll('tbody tr')].map(tr => tr.innerText.slice(0,100).replace(/\\n/g,' ')).slice(0,5);
        }""")
        log(f"  Nomes registros: {nomes_regs}")
        busca_reg.fill("")
        pg.wait_for_timeout(1000)

    # Ir para lista de usuarios e inativar o usuario
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)

    busca_usr = pg.locator("input[placeholder*='Pesquise' i]").first
    if busca_usr.count():
        busca_usr.fill("qainativo_tc4_28129")
        pg.wait_for_timeout(2000)
        snap(pg, "tc4v3_lista_antes_inativar")

    # Verificar estado atual do toggle
    toggle_info = pg.evaluate("""() => {
        const switches = [...document.querySelectorAll('.chakra-switch')];
        return switches.map(sw => {
            const box = sw.getBoundingClientRect();
            return {
                checked: sw.getAttribute('data-checked') !== null,
                x: box.x + box.width/2, y: box.y + box.height/2,
                visible: box.width > 0
            };
        }).filter(s => s.visible);
    }""")
    log(f"  Toggles visiveis: {json.dumps(toggle_info, ensure_ascii=False)}")

    if toggle_info:
        sw = toggle_info[0]
        if sw['checked']:
            log("  Usuario ATIVO. Clicando toggle para INATIVAR...")
            pg.mouse.click(sw['x'], sw['y'])
            pg.wait_for_timeout(1500)
            snap(pg, "tc4v3_modal_confirmacao")

            # Clicar "Confirmar" no modal
            confirmar = pg.evaluate("""() => {
                const btns = [...document.querySelectorAll('button')];
                const c = btns.find(b => b.innerText.trim() === 'Confirmar' && b.getBoundingClientRect().height > 0);
                if (c) {
                    const box = c.getBoundingClientRect();
                    return {x: box.x + box.width/2, y: box.y + box.height/2};
                }
                return null;
            }""")
            log(f"  Botao Confirmar: {confirmar}")
            if confirmar:
                pg.mouse.click(confirmar['x'], confirmar['y'])
                pg.wait_for_timeout(3000)
                snap(pg, "tc4v3_pos_inativar_lista")
                log("  Inativado com sucesso!")

                # Verificar estado do toggle depois
                estado_final = pg.evaluate("""() => {
                    const switches = [...document.querySelectorAll('.chakra-switch')];
                    return switches.map(sw => ({
                        checked: sw.getAttribute('data-checked') !== null,
                        class: sw.className.slice(0, 60)
                    })).slice(0, 3);
                }""")
                log(f"  Estado toggles depois: {json.dumps(estado_final, ensure_ascii=False)}")
            else:
                log("  ATENCAO: botao Confirmar nao encontrado no modal")
        else:
            log("  Usuario JA INATIVO antes do TC4")
            log("  ATENCAO: usuario esta inativo - necessario reativar primeiro")
            # Reativar
            pg.mouse.click(sw['x'], sw['y'])
            pg.wait_for_timeout(1500)
            # Confirmar reativacao se necessario
            modal_chk = pg.locator("[role='dialog']").first
            if modal_chk.count():
                confirmar2 = pg.evaluate("""() => {
                    const btns = [...document.querySelectorAll('button')];
                    const c = btns.find(b => /confirmar|sim|ok/i.test(b.innerText) && b.getBoundingClientRect().height > 0);
                    if (c) { const box = c.getBoundingClientRect(); return {x: box.x+box.width/2, y: box.y+box.height/2}; }
                    return null;
                }""")
                if confirmar2:
                    pg.mouse.click(confirmar2['x'], confirmar2['y'])
                    pg.wait_for_timeout(2000)

            pg.wait_for_timeout(2000)
            snap(pg, "tc4v3_reativado")
            log("  Reativado. Inativando agora...")

            # Buscar novamente e inativar
            pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
            try: pg.wait_for_load_state("networkidle", timeout=10000)
            except: pass
            pg.wait_for_timeout(2000)
            busca_usr2 = pg.locator("input[placeholder*='Pesquise' i]").first
            if busca_usr2.count():
                busca_usr2.fill("qainativo_tc4_28129")
                pg.wait_for_timeout(2000)

            toggle_info2 = pg.evaluate("""() => {
                const switches = [...document.querySelectorAll('.chakra-switch')].filter(s => s.getBoundingClientRect().width > 0);
                return switches.map(sw => ({
                    checked: sw.getAttribute('data-checked') !== null,
                    x: sw.getBoundingClientRect().x + sw.getBoundingClientRect().width/2,
                    y: sw.getBoundingClientRect().y + sw.getBoundingClientRect().height/2
                }));
            }""")
            if toggle_info2 and toggle_info2[0]['checked']:
                sw2 = toggle_info2[0]
                pg.mouse.click(sw2['x'], sw2['y'])
                pg.wait_for_timeout(1500)
                confirmar3 = pg.evaluate("""() => {
                    const c = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Confirmar' && b.getBoundingClientRect().height > 0);
                    if (c) { const box = c.getBoundingClientRect(); return {x: box.x+box.width/2, y: box.y+box.height/2}; }
                    return null;
                }""")
                if confirmar3:
                    pg.mouse.click(confirmar3['x'], confirmar3['y'])
                    pg.wait_for_timeout(3000)
                    snap(pg, "tc4v3_inativado_segunda_vez")
                    log("  Inativado na segunda tentativa!")
    else:
        log("  ATENCAO: nenhum toggle encontrado")
        snap(pg, "tc4v3_sem_toggle")

    # PASSO 3: Verificar Registros apos inativacao
    log("\n--- Verificando Registros apos inativacao ---")
    aguardar_registros(pg)
    pg.wait_for_timeout(6000)
    snap(pg, "tc4v3_registros_pos_inativar")

    kpis_depois = extrair_kpis(pg)
    linhas_depois = pg.locator("tbody tr").count()
    log(f"  KPIs DEPOIS de inativar: {json.dumps(kpis_depois, ensure_ascii=False)}")
    log(f"  Linhas depois: {linhas_depois}")

    busca_reg2 = pg.locator("input[placeholder*='Pesquise' i]").first
    linhas_inativo_depois = -1
    if busca_reg2.count():
        busca_reg2.fill("QAInativo TC4-28129")
        pg.wait_for_timeout(2000)
        linhas_inativo_depois = pg.locator("tbody tr").count()
        snap(pg, "tc4v3_busca_inativo_depois")
        log(f"  Linhas do inativo DEPOIS: {linhas_inativo_depois}")

        msg_vazia = pg.evaluate("""() => {
            return [...document.querySelectorAll('td, p, div')].some(e =>
                e.children.length === 0 && /nenhum|no record|sem registro/i.test(e.innerText)
            );
        }""")
        log(f"  Mensagem 'Nenhum': {msg_vazia}")
        busca_reg2.fill("")
        pg.wait_for_timeout(1000)

    # Verificar toggle "mostrar inativos"
    toggle_mostrar = pg.locator("button, label, [role='checkbox']").filter(
        has_text=re.compile("Inativ|mostrar inativ|show inact", re.I)).count()
    snap(pg, "tc4v3_sem_toggle_inativos")
    log(f"  Toggle 'mostrar inativos': {toggle_mostrar}")

    # VEREDITO TC4
    linhas_inativo_antes_v = locals().get('linhas_inativo_antes', -1)
    log(f"\n  === VEREDITO TC4 ===")
    log(f"  Registros inativo ANTES: {linhas_inativo_antes_v}")
    log(f"  Registros inativo DEPOIS: {linhas_inativo_depois}")
    log(f"  KPIs antes: {kpis_antes}")
    log(f"  KPIs depois: {kpis_depois}")

    total_antes = sum(v for v in kpis_antes.values() if isinstance(v, int) and v >= 0)
    total_depois = sum(v for v in kpis_depois.values() if isinstance(v, int) and v >= 0)
    log(f"  Total KPI antes: {total_antes}, depois: {total_depois}")

    if linhas_inativo_antes_v > 0 and linhas_inativo_depois == 0 and total_depois < total_antes:
        log("  TC4: PASS - Registros SUMIRAM e KPI DECREMENTOU")
    elif linhas_inativo_depois > 0:
        log(f"  TC4: FAIL - Registros AINDA aparecem ({linhas_inativo_depois} linhas)")
    elif total_depois >= total_antes and linhas_inativo_antes_v > 0:
        log(f"  TC4: FAIL - KPI NAO decrementou ({total_antes} -> {total_depois})")
    elif linhas_inativo_antes_v <= 0:
        log(f"  TC4: INCONCLUSIVO - registros nao encontrados antes (linhas={linhas_inativo_antes_v})")
    else:
        log(f"  TC4: INCONCLUSIVO")

    ca.close(); ba.close()
