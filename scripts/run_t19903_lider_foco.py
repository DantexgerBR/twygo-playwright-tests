"""
QA 1.16 - Foco no Lider:
1. Login lider, navegar para Registros, aguardar carga
2. Ler KPIs APOS confirmar que estamos como Gestor de Turma
3. Contar linhas e paginacao
4. Clicar no campo Pessoas do form Adicionar
5. Verificar dropdown de pessoas (liderados vs todos)
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
    "email": "qalider@teste.com",
    "senha": "123456",
}

SLUG = "registros-f2-qa116"
BASE = tw.ROOT / "evidencias" / SLUG
BASE.mkdir(parents=True, exist_ok=True)
BASE_URL = c["base_url"]
ORG_ID = c["org_id"]
REGISTROS_URL = f"{BASE_URL}/o/{ORG_ID}/records"


def login_lider(page):
    """Login do lider sem admin switch."""
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
    # Aguardar campo aparecer
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", c_lider["email"])
    page.fill("#user_password", c_lider["senha"])
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    # Fechar modais de onboarding/NPS
    tw.dispensar_nps(page)
    # Fechar tour de boas-vindas se aparecer
    try:
        fechar = page.locator("button", has_text="Fechar").or_(
            page.locator("button[aria-label*='fechar']")
        ).or_(page.locator("button[aria-label*='close']")).first
        if fechar.count() and fechar.is_visible():
            fechar.click()
            page.wait_for_timeout(500)
    except Exception:
        pass
    # Pressionar Escape pra fechar qualquer modal
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)


def ir_registros_lider(page):
    """Navega para Registros como lider e aguarda carregamento."""
    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    # Aguardar linha ou empty
    try:
        page.wait_for_selector("tbody tr, [class*='empty'], [class*='Empty']",
                               timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    # ===== LIDER =====
    print("=== LOGIN COMO LIDER ===")
    login_lider(page)

    # Confirmar perfil ANTES de ir para Registros
    perfil_atual = page.evaluate("""
        () => {
            const header = document.body.innerText || '';
            const m = header.match(/Gestor de turma|Administrador|Colaborador/i);
            return {
                perfil: m ? m[0] : 'desconhecido',
                url: window.location.href,
                header_botao: (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const perfilBtn = btns.find(b =>
                        /gestor|administrador|colaborador/i.test(b.innerText || ''));
                    return perfilBtn ? perfilBtn.innerText.trim() : '';
                })()
            };
        }
    """)
    print(f"Perfil apos login: {json.dumps(perfil_atual, ensure_ascii=False)}")
    tw.snap(page, BASE, "lider_pos_login")

    # Ir para Registros
    print("\n=== REGISTROS DO LIDER ===")
    ir_registros_lider(page)

    # Confirmar perfil na tela de Registros
    perfil_registros = page.evaluate("""
        () => {
            const btns = Array.from(document.querySelectorAll('button'));
            const perfilBtn = btns.find(b => /gestor|administrador|colaborador/i.test(b.innerText || ''));
            return {
                url: window.location.href,
                perfil_botao: perfilBtn ? perfilBtn.innerText.trim() : 'nao encontrado',
                titulo: document.title
            };
        }
    """)
    print(f"Perfil na tela Registros: {json.dumps(perfil_registros, ensure_ascii=False)}")
    tw.snap(page, BASE, "lider_registros_confirmado")

    # KPIs com busca direta pelos cards
    kpis = page.evaluate("""
        () => {
            const cards = Array.from(document.querySelectorAll(
                '[class*="card"], [class*="Card"], [class*="kpi"], [class*="stat"]'
            )).filter(el => el.offsetParent !== null);

            const resultado = {};
            const labels = ['Emitidos', 'Expirados', 'Pendentes', 'Recusados'];

            for (const label of labels) {
                // Buscar o texto do label em todos os elementos
                const allEls = Array.from(document.querySelectorAll('*'));
                for (const el of allEls) {
                    if (el.children.length === 0) { // Apenas folhas do DOM
                        const txt = (el.textContent || '').trim();
                        if (txt === label) {
                            // Pegar o numero no elemento pai ou irmao
                            const parent = el.parentElement;
                            if (parent) {
                                const numEl = parent.querySelector('[class*="number"], [class*="count"], span, strong, b');
                                if (numEl) {
                                    const num = parseInt((numEl.textContent || '').trim(), 10);
                                    if (!isNaN(num)) { resultado[label.toLowerCase()] = num; break; }
                                }
                                // Tenta o texto todo do parent
                                const parentTxt = parent.textContent || '';
                                const m = parentTxt.match(/(\\d+)/);
                                if (m) { resultado[label.toLowerCase()] = parseInt(m[1], 10); break; }
                            }
                        }
                    }
                }
            }
            return resultado;
        }
    """)
    print(f"KPIs Lider (busca direta): {kpis}")

    # Contar linhas e paginas
    info_lista = page.evaluate("""
        () => {
            const linhas = document.querySelectorAll('tbody tr').length;
            const pagBtns = Array.from(document.querySelectorAll(
                '[class*="pagination"] button, [class*="Pagination"] button, nav button'
            )).map(b => (b.innerText || '').trim()).filter(t => /^\\d+$/.test(t));

            const maxPag = pagBtns.length > 0 ? Math.max(...pagBtns.map(Number)) : 1;

            // Emails na lista
            const emails = new Set();
            document.querySelectorAll('tbody tr').forEach(r => {
                const m = (r.innerText || '').match(/[\\w.+%-]+@[\\w.-]+\\.[a-z]{2,}/gi);
                if (m) m.forEach(e => emails.add(e.toLowerCase()));
            });

            return {
                linhas,
                max_pagina: maxPag,
                pagBtns,
                emails: Array.from(emails)
            };
        }
    """)
    print(f"Info lista lider: {json.dumps(info_lista, ensure_ascii=False)}")

    # Screenshot completo
    tw.snap(page, BASE, "lider_registros_lista")

    # ===== FORM ADICIONAR - CAMPO PESSOAS =====
    print("\n=== FORM ADICIONAR - CAMPO PESSOAS ===")
    try:
        btn_add = page.locator("button", has_text="Adicionar").first
        if btn_add.count():
            btn_add.click()
            # Aguardar form
            try:
                page.wait_for_selector("input[placeholder*='essoa'], input[placeholder*='Search']",
                                       timeout=8000)
            except Exception:
                page.wait_for_timeout(3000)
            tw.snap(page, BASE, "lider_form_add_inicio")

            # Tentar clicar no campo Pessoas
            campo_pessoas = page.locator("input[placeholder*='essoa']").or_(
                page.locator("[placeholder*='Adicionar pessoas']")
            ).or_(page.locator("input[id*='erson']")).first

            if campo_pessoas.count():
                campo_pessoas.click()
                page.wait_for_timeout(1000)
                # Tentar digitar para abrir dropdown
                campo_pessoas.fill("a")
                page.wait_for_timeout(1500)
                tw.snap(page, BASE, "lider_pessoas_dropdown_a")

                # Ler opcoes
                opcoes = page.evaluate("""
                    () => {
                        const opts = Array.from(document.querySelectorAll(
                            '[role="option"], [role="listbox"] li, [class*="option"], [class*="Option"]'
                        )).filter(el => el.offsetParent !== null);
                        return opts.map(o => (o.innerText || '').trim()).filter(t => t.length > 0).slice(0, 15);
                    }
                """)
                print(f"Opcoes no campo Pessoas (digitando 'a'): {opcoes}")

                # Limpar e ver todas as opcoes
                campo_pessoas.fill("")
                page.wait_for_timeout(1000)
                campo_pessoas.press("Backspace")
                page.wait_for_timeout(1000)
                tw.snap(page, BASE, "lider_pessoas_dropdown_vazio")

                opcoes_vazio = page.evaluate("""
                    () => {
                        const opts = Array.from(document.querySelectorAll(
                            '[role="option"], [role="listbox"] li, [class*="option"], [class*="Option"]'
                        )).filter(el => el.offsetParent !== null);
                        return opts.map(o => (o.innerText || '').trim()).filter(t => t.length > 0).slice(0, 15);
                    }
                """)
                print(f"Opcoes no campo Pessoas (campo vazio): {opcoes_vazio}")
            else:
                print("Campo Pessoas nao encontrado por placeholder")
                # Listar todos os inputs do form
                inputs = page.evaluate("""
                    () => Array.from(document.querySelectorAll('input, [contenteditable]'))
                        .filter(el => el.offsetParent !== null)
                        .map(el => ({tag: el.tagName, placeholder: el.placeholder || '', id: el.id || ''}))
                """)
                print(f"Inputs visiveis: {inputs}")
                tw.snap(page, BASE, "lider_form_add_inputs")

    except Exception as e:
        print(f"Erro form adicionar: {e}")

    # ===== ADMIN: KPIs corretos com wait =====
    print("\n=== ADMIN: KPIs CORRETOS ===")
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector("#user_email", timeout=10000)
    tw.login(page, c, admin=True)
    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector("tbody tr", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.snap(page, BASE, "admin_registros_final")

    kpis_admin = page.evaluate("""
        () => {
            const allEls = Array.from(document.querySelectorAll('*'));
            const resultado = {};
            const labels = ['Emitidos', 'Expirados', 'Pendentes', 'Recusados'];
            for (const label of labels) {
                for (const el of allEls) {
                    if (el.children.length === 0) {
                        const txt = (el.textContent || '').trim();
                        if (txt === label) {
                            const parent = el.parentElement;
                            if (parent) {
                                const parentTxt = parent.textContent || '';
                                const m = parentTxt.match(/(\\d+)/);
                                if (m) { resultado[label.toLowerCase()] = parseInt(m[1], 10); break; }
                            }
                        }
                    }
                }
            }
            return resultado;
        }
    """)
    info_admin = page.evaluate("""
        () => {
            const linhas = document.querySelectorAll('tbody tr').length;
            const pagBtns = Array.from(document.querySelectorAll(
                '[class*="pagination"] button, [class*="Pagination"] button, nav button'
            )).map(b => (b.innerText || '').trim()).filter(t => /^\\d+$/.test(t));
            return {
                linhas,
                max_pagina: pagBtns.length > 0 ? Math.max(...pagBtns.map(Number)) : 1,
                pagBtns
            };
        }
    """)
    print(f"KPIs Admin: {kpis_admin}")
    print(f"Info lista Admin: {info_admin}")

    ctx.close()
    browser.close()

print("\nDone. Screenshots em evidencias/registros-f2-qa116/lider_*.png")
