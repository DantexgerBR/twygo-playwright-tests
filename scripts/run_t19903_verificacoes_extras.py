"""
QA 1.16 — Verificacoes extras (v2):
1. KPIs com wait adequado (esperar nodes nao-spinner)
2. Total real da lista (paginacao)
3. Filtro por Origem=Compartilhado (nao so pagina 1)
4. Perfil exato do lider (admin tambem?)
5. Organograma URL real (sidebar)
6. Form Adicionar do lider com waits corretos
"""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
from dotenv import load_dotenv

load_dotenv(tw.ROOT / ".env")

c = {
    "base_url": os.environ["REGISTROSF2_BASE_URL"].rstrip("/"),
    "org_id": os.environ["REGISTROSF2_ORG_ID"],
    "email": os.environ["REGISTROSF2_ADMIN_EMAIL"],
    "senha": os.environ["REGISTROSF2_ADMIN_PASSWORD"],
}
c_lider = {
    "base_url": c["base_url"],
    "org_id": c["org_id"],
    "email": "qalider@teste.com",
    "senha": "123456",
}

SLUG = "registros-f2-qa116"
BASE = tw.ROOT / "evidencias" / SLUG
BASE.mkdir(parents=True, exist_ok=True)
BASE_URL = c["base_url"]
ORG_ID = c["org_id"]
REGISTROS_URL = f"{BASE_URL}/o/{ORG_ID}/records"


def login_admin(page):
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    tw.login(page, c, admin=True)


def login_lider(page):
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.fill("#user_email", c_lider["email"])
    page.fill("#user_password", c_lider["senha"])
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)


def ir_registros_e_aguardar(page):
    """Navega para Registros e aguarda a lista carregada (linha real em tbody)."""
    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    # Esperar alguma linha ou empty-state aparecer
    try:
        page.wait_for_selector("tbody tr, [class*='empty'], [class*='EmptyState']",
                               timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)


def ler_kpis_por_card(page) -> dict:
    """Le cada KPI card procurando o elemento que contem o label e seu numero."""
    return page.evaluate("""
        () => {
            const result = {};
            const bodyText = document.body.innerText || '';
            // Labels dos KPIs de Registros
            const labels = ['Emitidos', 'Expirados', 'Pendentes', 'Recusados'];
            for (const label of labels) {
                // Procurar o label no DOM
                const walker = document.createTreeWalker(
                    document.body, NodeFilter.SHOW_TEXT,
                    {acceptNode: n => new RegExp('^\\\\s*' + label + '\\\\s*$', 'i').test(n.nodeValue)
                        ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP}
                );
                const textNode = walker.nextNode();
                if (textNode) {
                    // Subir na arvore para achar o card/container pai
                    let el = textNode.parentElement;
                    for (let i = 0; i < 5; i++) {
                        const numText = el.innerText || '';
                        const m = numText.match(/^\\s*(\\d+)\\s*/);
                        if (m) { result[label.toLowerCase()] = parseInt(m[1], 10); break; }
                        if (el.parentElement) el = el.parentElement; else break;
                    }
                }
            }
            // Fallback por regex mais simples
            if (Object.keys(result).length === 0) {
                for (const label of labels) {
                    // Buscar padrao "NNN label" ou "label NNN" com NNN sendo o primeiro numero grande
                    const rx = new RegExp('(\\\\b\\\\d+\\\\b)\\\\s*' + label, 'i');
                    const m = bodyText.match(rx);
                    if (m) result[label.toLowerCase()] = parseInt(m[1], 10);
                }
            }
            return result;
        }
    """)


def total_real_lista(page) -> dict:
    """Extrai o total real de registros via texto de paginacao ou filtro."""
    return page.evaluate("""
        () => {
            const body = document.body.innerText || '';

            // Tentar "X-Y de Z registros" ou "Total: Z"
            let mTotal = body.match(/(\\d+)\\s*-\\s*(\\d+)\\s*de\\s*(\\d+)/);
            if (mTotal) return {tipo: 'faixa', de: mTotal[1], ate: mTotal[2], total: parseInt(mTotal[3], 10)};

            // Tentar botoes de pagina numerados (max pagina visivel)
            const btns = Array.from(document.querySelectorAll('button, a'))
                .map(b => parseInt((b.innerText || '').trim(), 10))
                .filter(n => !isNaN(n) && n > 0 && n < 1000);
            const maxPagina = btns.length > 0 ? Math.max(...btns) : 0;

            // Linhas por pagina via select
            const porPagina = parseInt(
                (document.querySelector('select') || {}).value || '25', 10
            );

            // Contar linhas visíveis
            const linhas = document.querySelectorAll('tbody tr').length;

            return {
                tipo: 'estimado',
                max_pagina: maxPagina,
                linhas_por_pagina: porPagina,
                linhas_pagina_atual: linhas,
                estimado_total: maxPagina * porPagina
            };
        }
    """)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    # ============================================================
    # 1. Admin: KPIs precisos e total real
    # ============================================================
    print("=== 1. Admin: KPIs e total real ===")
    login_admin(page)
    ir_registros_e_aguardar(page)
    tw.snap(page, BASE, "v2_admin_registros")

    kpis_admin = ler_kpis_por_card(page)
    total_admin = total_real_lista(page)
    print(f"KPIs Admin: {kpis_admin}")
    print(f"Total real: {total_admin}")

    # ============================================================
    # 2. Filtro por Compartilhado (todas as paginas)
    # ============================================================
    print("\n=== 2. Filtro Compartilhado ===")
    # Tentar abrir filtro e filtrar por Origem=Compartilhado
    try:
        filtro_btn = page.locator("button", has_text="Filtro").last
        if filtro_btn.count():
            filtro_btn.click()
            page.wait_for_timeout(2000)
            tw.snap(page, BASE, "v2_filtro_drawer")

            # Procurar opcao de Origem/Compartilhado no drawer
            filtro_texto = page.evaluate("""
                () => {
                    // Verificar se drawer abriu
                    const drawers = Array.from(document.querySelectorAll(
                        '[class*="drawer"], [class*="Drawer"], [role="dialog"]'
                    ));
                    if (drawers.length === 0) return {abriu: false};
                    const d = drawers[0];
                    return {
                        abriu: true,
                        texto: (d.innerText || '').replace(/\\s+/g, ' ').trim().substring(0, 500)
                    };
                }
            """)
            print(f"Filtro drawer: {filtro_texto}")

            # Procurar botao/checkbox de Origem ou Compartilhado
            opcoes_filtro = page.evaluate("""
                () => {
                    const items = Array.from(document.querySelectorAll(
                        '[role="checkbox"], [role="option"], [class*="filter-item"], button'
                    )).filter(el => el.offsetParent !== null);
                    return items.map(el => (el.innerText || '').trim())
                        .filter(t => t.length > 0 && t.length < 50)
                        .slice(0, 20);
                }
            """)
            print(f"Opcoes de filtro: {opcoes_filtro}")

            # Tentar clicar em Origem ou Compartilhado
            compartilhado_btn = page.locator("button, [role='checkbox'], label").filter(
                has_text="Compartilhado"
            ).first
            if compartilhado_btn.count():
                compartilhado_btn.click()
                page.wait_for_timeout(1000)
                # Aplicar filtro
                aplicar_btn = page.locator("button", has_text="Aplicar").first
                if aplicar_btn.count():
                    aplicar_btn.click()
                    page.wait_for_timeout(2000)
                tw.snap(page, BASE, "v2_filtro_compartilhado_aplicado")
                linhas_comp = page.evaluate("""
                    () => document.querySelectorAll('tbody tr').length
                """)
                print(f"Linhas com filtro Compartilhado: {linhas_comp}")
            else:
                print("  Opcao 'Compartilhado' nao encontrada no filtro")
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
    except Exception as e:
        print(f"Erro ao usar filtro: {e}")

    # Verificar se ha chips "Compartilhado" na lista sem filtro (scan de mais paginas)
    # Ir para ultima pagina e verificar
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    ir_registros_e_aguardar(page)

    # Verificar coluna Origem na tabela
    colunas = page.evaluate("""
        () => Array.from(document.querySelectorAll('thead th, thead td'))
            .map(th => (th.innerText || '').replace(/\\s+/g, ' ').trim())
            .filter(t => t)
    """)
    print(f"\nColunas da tabela: {colunas}")

    # Verificar valores da coluna Origem na pagina 1
    origem_valores = page.evaluate("""
        () => {
            const headers = Array.from(document.querySelectorAll('thead th, thead td'))
                .map(th => (th.innerText || '').replace(/\\s+/g, ' ').trim());
            const origemIdx = headers.findIndex(h => /origem/i.test(h));
            if (origemIdx < 0) return {origemIdx: -1, headers};
            const rows = Array.from(document.querySelectorAll('tbody tr'));
            const valores = rows.map(r => {
                const tds = r.querySelectorAll('td');
                return origemIdx < tds.length ? (tds[origemIdx].innerText || '').trim() : '';
            });
            return {
                origemIdx,
                valores: [...new Set(valores)],
                total_compartilhado: valores.filter(v => /compartilhado/i.test(v)).length,
                total_externo: valores.filter(v => /externo/i.test(v)).length
            };
        }
    """)
    print(f"Valores da coluna Origem: {origem_valores}")
    tw.snap(page, BASE, "v2_coluna_origem")

    # ============================================================
    # 3. Perfil exato do lider
    # ============================================================
    print("\n=== 3. Perfil do lider ===")
    login_lider(page)
    page.wait_for_timeout(1000)
    tw.snap(page, BASE, "v2_lider_header")

    # Verificar o header/nav: quais perfis o lider tem disponivel
    perfil_info = page.evaluate("""
        () => {
            const body = document.body.innerText || '';
            // Verificar se ha opcao de "Administrador" no dropdown de perfil
            const header = document.querySelector('header, nav, [class*="header"], [class*="Header"]');
            return {
                url: window.location.href,
                titulo_pagina: document.title,
                header_texto: header ? (header.innerText || '').replace(/\\s+/g, ' ').trim().substring(0, 300) : '',
                tem_admin_opcao: /administrador/i.test(body),
                tem_gestor_opcao: /gestor.*turma/i.test(body),
                perfil_atual: (body.match(/Gestor de turma|Administrador|Colaborador/i) || [''])[0]
            };
        }
    """)
    print(f"Perfil info: {json.dumps(perfil_info, ensure_ascii=False)}")

    # Clicar no dropdown de perfil para ver opcoes
    try:
        perfil_btn = page.locator(
            "button[class*='profile'], [class*='ProfileButton'], button"
        ).filter(has_text="Gestor de turma").first
        if perfil_btn.count():
            perfil_btn.click()
            page.wait_for_timeout(1000)
            tw.snap(page, BASE, "v2_lider_dropdown_perfil")
            opcoes_perfil = page.evaluate("""
                () => {
                    const items = Array.from(document.querySelectorAll('[role="menuitem"], [role="option"], li'));
                    return items.filter(el => el.offsetParent !== null)
                        .map(el => (el.innerText || '').trim())
                        .filter(t => t.length > 0 && t.length < 100);
                }
            """)
            print(f"Opcoes do dropdown de perfil: {opcoes_perfil}")
            page.keyboard.press("Escape")
    except Exception as e:
        print(f"Erro ao verificar dropdown de perfil: {e}")

    # ============================================================
    # 4. Lider nos Registros: lista e KPIs
    # ============================================================
    print("\n=== 4. Lider: Registros (com waits) ===")
    ir_registros_e_aguardar(page)
    tw.snap(page, BASE, "v2_lider_registros")

    kpis_lider = ler_kpis_por_card(page)
    total_lider = total_real_lista(page)
    print(f"KPIs Lider: {kpis_lider}")
    print(f"Total lider: {total_lider}")

    # Verificar emails na lista do lider (pagina 1)
    emails_lider = page.evaluate("""
        () => {
            const rows = Array.from(document.querySelectorAll('tbody tr'));
            const emails = new Set();
            rows.forEach(r => {
                const txt = r.innerText || '';
                const m = txt.match(/[\\w.+%-]+@[\\w.-]+\\.[a-z]{2,}/gi);
                if (m) m.forEach(e => emails.add(e.toLowerCase()));
            });
            return Array.from(emails).slice(0, 20);
        }
    """)
    print(f"Emails na lista do lider: {emails_lider}")

    # ============================================================
    # 5. Form Adicionar do lider (com waits)
    # ============================================================
    print("\n=== 5. Lider: Form Adicionar ===")
    try:
        btn_add = page.locator("button", has_text="Adicionar").first
        if btn_add.count():
            btn_add.click()
            # Esperar formulario carregar
            try:
                page.wait_for_selector("form, [class*='Form'], input[placeholder]",
                                       timeout=8000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            tw.snap(page, BASE, "v2_lider_form_adicionar")

            # Verificar campos do form
            campos = page.evaluate("""
                () => {
                    const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
                    return inputs.map(i => ({
                        tag: i.tagName,
                        id: i.id,
                        name: i.name,
                        placeholder: i.placeholder,
                        type: i.type
                    })).filter(i => i.placeholder || i.name || i.id);
                }
            """)
            print(f"Campos do form: {json.dumps(campos, ensure_ascii=False)[:400]}")

            # Tentar abrir dropdown de pessoa
            # Clicar no primeiro campo que pareca ser Pessoa
            pessoa_tentativas = [
                "input[placeholder*='essoa']",
                "input[placeholder*='Pesquise']",
                "input[placeholder*='search']",
                "[class*='select'] input",
                "input[id*='erson']",
            ]
            for sel in pessoa_tentativas:
                try:
                    el = page.locator(sel).first
                    if el.count():
                        el.click()
                        page.wait_for_timeout(500)
                        el.fill("")
                        page.wait_for_timeout(500)
                        el.press("Backspace")
                        page.wait_for_timeout(1000)
                        # Ver opcoes
                        opts = page.evaluate("""
                            () => {
                                const dropdowns = Array.from(document.querySelectorAll(
                                    '[role="listbox"], [role="menu"], [class*="options"], [class*="dropdown"]'
                                )).filter(el => el.offsetParent !== null);
                                if (dropdowns.length > 0) {
                                    const items = Array.from(dropdowns[0].querySelectorAll(
                                        '[role="option"], li, [class*="option"]'
                                    ));
                                    return items.map(i => (i.innerText || '').trim())
                                        .filter(t => t.length > 0).slice(0, 10);
                                }
                                return [];
                            }
                        """)
                        if opts:
                            print(f"Opcoes Pessoa ({sel}): {opts}")
                            tw.snap(page, BASE, "v2_lider_dropdown_pessoa")
                            break
                        else:
                            print(f"  {sel}: campo achado mas sem opcoes")
                except Exception as ex:
                    pass

        page.keyboard.press("Escape")
    except Exception as e:
        print(f"Erro form adicionar: {e}")

    # ============================================================
    # 6. URL real do Organograma
    # ============================================================
    print("\n=== 6. URL Organograma via sidebar ===")
    login_admin(page)
    tw.snap(page, BASE, "v2_admin_sidebar")
    org_link = page.evaluate("""
        () => {
            const links = Array.from(document.querySelectorAll('a'));
            const org = links.find(a => /organograma/i.test(a.innerText || '') ||
                                       /organization/i.test(a.href || ''));
            return org ? {href: org.href, texto: org.innerText.trim()} : null;
        }
    """)
    print(f"Link do Organograma: {org_link}")

    if org_link and org_link.get('href'):
        page.goto(org_link['href'], wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)
        tw.snap(page, BASE, "v2_organograma_real")
        org_texto = page.evaluate("() => document.body.innerText.substring(0, 500)")
        print(f"Organograma texto: {org_texto}")

    ctx.close()
    browser.close()

print("\nDone. Screenshots em evidencias/registros-f2-qa116/v2_*.png")
