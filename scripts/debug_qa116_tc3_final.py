# -*- coding: utf-8 -*-
"""TC3 definitivo: usar selector .clear_manager para clicar no X."""
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
log("="*60)
log("TC3 DEFINITIVO")
log("="*60)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "tc3_def_before")

    # O elemento X e um <a class="clear_manager">
    # Usar Playwright locator direto
    clear_manager = pg.locator("a.clear_manager")
    count = clear_manager.count()
    log(f"  clear_manager count: {count}")

    if count > 0:
        # Scrollar para o elemento ser visivel
        clear_manager.scroll_into_view_if_needed(timeout=5000)
        pg.wait_for_timeout(500)
        snap(pg, "tc3_def_scroll_to_x")

        # Clicar
        clear_manager.click(timeout=5000)
        pg.wait_for_timeout(1500)
        snap(pg, "tc3_def_apos_click")

        qa_presente = pg.evaluate("""() => {
            return [...document.querySelectorAll('*')].some(e => e.children.length === 0 && e.innerText && e.innerText.trim().includes('QALider'));
        }""")
        log(f"  QALider presente apos click: {qa_presente}")
        results['responsavel_removido'] = not qa_presente

        if not qa_presente:
            log("  Responsavel removido com sucesso!")
            # Salvar
            save = pg.locator("button, input[type=submit]").filter(has_text=re.compile("Salvar|Save", re.I)).first
            if save.count():
                save.click(timeout=5000)
                pg.wait_for_timeout(4000)
                snap(pg, "tc3_def_salvo")
                log(f"  Salvo! URL: {pg.url}")
                results['tc3_salvo'] = True
            else:
                # Tentar JS
                save_js = pg.evaluate("""() => {
                    const btns = [...document.querySelectorAll('button, input[type=submit]')];
                    const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
                    if (s) { s.click(); return true; }
                    return false;
                }""")
                pg.wait_for_timeout(4000)
                snap(pg, "tc3_def_salvo_js")
                results['tc3_salvo'] = save_js
        else:
            log("  X clicou mas QALider ainda presente")
            results['tc3'] = 'INCONCLUSIVO_responsavel_permaneceu'
    else:
        log("  .clear_manager nao encontrado! Tentando via ID do manager_container...")
        # Ver se o manager_container existe
        mc = pg.locator("#manager_container")
        log(f"  #manager_container: {mc.count()}")

        # Tentar alternativas
        clear_link = pg.locator("#manager_container a")
        log(f"  Links em #manager_container: {clear_link.count()}")
        if clear_link.count() > 0:
            clear_link.first.scroll_into_view_if_needed(timeout=5000)
            pg.wait_for_timeout(500)
            clear_link.first.click(timeout=5000)
            pg.wait_for_timeout(1500)
            snap(pg, "tc3_def_alt_click")
            qa_ok = pg.evaluate("""() => !([...document.querySelectorAll('*')].some(e => e.children.length === 0 && e.innerText && e.innerText.trim().includes('QALider')))""")
            log(f"  Responsavel removido: {qa_ok}")
            if qa_ok:
                # Salvar
                pg.evaluate("""() => { const s = [...document.querySelectorAll('button')].find(b => /salvar|save/i.test(b.innerText) && b.getBoundingClientRect().height > 0); if (s) s.click(); }""")
                pg.wait_for_timeout(4000)
                snap(pg, "tc3_def_alt_salvo")
                results['tc3_salvo'] = True
        else:
            results['tc3'] = 'INCONCLUSIVO_clear_manager_ausente'

    ca.close(); ba.close()


# Verificar resultado se salvou
if results.get('tc3_salvo'):
    log("\n  TC3: verificando persistencia (admin) e invisibilidade (lider)...")
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

        snap(pg_admin, "tc3_def_admin_pos")
        n_admin = contar_linhas_reais(pg_admin)
        rows_admin = pg_admin.evaluate("""() => [...document.querySelectorAll('tbody tr')].map(tr => tr.innerText && tr.innerText.replace(/\\n/g,' ').slice(0, 100))""")
        log(f"  Admin ve {n_admin} registros de liderado: {rows_admin}")
        results['tc3_n_admin'] = n_admin

        login_lider(pg_lider)
        snap(pg_lider, "tc3_def_lider_pos")
        n_lider = contar_linhas_reais(pg_lider)
        kpis = extrair_kpis(pg_lider)
        log(f"  Lider ve {n_lider} registros, KPIs: {kpis}")
        results['tc3_n_lider'] = n_lider
        results['tc3_kpis_lider_pos'] = kpis

        if n_admin > 0 and n_lider == 0:
            results['tc3'] = 'PASS'
            log("  TC3 PASS - Registro persiste no admin; lider nao ve mais")
        elif n_admin == 0:
            results['tc3'] = 'FAIL_registro_sumiu_do_admin'
            log("  TC3 FAIL - Registro sumiu do admin tambem!")
        elif n_lider > 0:
            results['tc3'] = f'FAIL_lider_ainda_ve_{n_lider}'
            log(f"  TC3 FAIL - Lider ainda ve {n_lider} registros")

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
        snap(pg, "restore_def_before")

        # Clicar no input do manager para buscar
        # O input hidden tem id="manager_name". Precisamos torná-lo visível
        # Pela estrutura HTML: #manager_search é hidden. Precisamos simular o click que mostra o input
        # Alternativa: manipular o DOM via JS para mostrar o input
        resultado_show = pg.evaluate("""() => {
            // Tentar remover a classe "hidden" do manager_search
            const ms = document.getElementById('manager_search');
            const ml = document.getElementById('manager_label');
            if (ms) ms.style.display = 'block';
            if (ml) ml.style.display = 'none';

            // Focar no input
            const inp = document.getElementById('manager_name');
            if (inp) { inp.focus(); return {found: true}; }
            return {found: false};
        }""")
        log(f"  Show manager_search: {resultado_show}")
        pg.wait_for_timeout(500)
        snap(pg, "restore_def_show_input")

        # Agora preencher o input
        manager_input = pg.locator("#manager_name")
        if manager_input.count():
            manager_input.fill("qaliderpuro")
            pg.wait_for_timeout(1500)
            snap(pg, "restore_def_busca")

            # Ver opcoes
            opcoes = pg.locator("#professiona-manager-list [class*=item], #professiona-manager-list li, #professiona-manager-list div").all()
            log(f"  Opcoes dropdown: {len(opcoes)}")

            if len(opcoes) > 0:
                opcoes[0].click(timeout=5000)
                pg.wait_for_timeout(1000)
                log("  Selecionado primeiro resultado!")
            else:
                # Ver o HTML da lista
                lista_html = pg.evaluate("() => document.getElementById('professiona-manager-list')?.innerHTML.slice(0, 300) || 'vazio'")
                log(f"  Lista: {lista_html}")
        else:
            log("  Input manager_name nao encontrado")

        # Salvar
        save = pg.evaluate("""() => {
            const btns = [...document.querySelectorAll('button, input[type=submit]')];
            const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
            if (s) { s.click(); return true; }
            return false;
        }""")
        pg.wait_for_timeout(3000)
        snap(pg, "restore_def_salvo")
        log(f"  Salvo: {save}, URL: {pg.url}")

        ca.close(); ba.close()


log("\n" + "="*60)
log("SUMARIO")
for k, v in results.items():
    log(f"  {k}: {v}")
