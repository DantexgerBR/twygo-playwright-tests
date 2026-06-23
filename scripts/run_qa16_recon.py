"""run_qa16_recon.py — Recon do form de Adicionar registro (org 37079).
Captura estrutura real dos campos (labels, placeholders, required) e URLs
para o form Admin e Aluno.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL       = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID         = os.environ.get("REGISTROSF2_ORG_ID", "37079")
ADMIN_EMAIL    = os.environ.get("REGISTROSF2_ADMIN_EMAIL", "dante.tavares@twygo.com")
ADMIN_PASSWORD = os.environ.get("REGISTROSF2_ADMIN_PASSWORD", "123456")
ALUNO_EMAIL    = os.environ.get("REGISTROSF2_TC3_EMAIL", "qa11tc342588@twygotest.com")
ALUNO_PASSWORD = os.environ.get("REGISTROSF2_TC3_PASSWORD", "twygoqa2026")
LIDER_EMAIL    = "qalider@teste.com"
LIDER_PASSWORD = "123456"

SLUG = "registros-f2-qa16"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg)


def suprimir_sophia(page):
    page.evaluate("""() => {
        ['#hubspot-messages-iframe-container','[id*="sophia"],[id*="hubspot"]']
        .forEach(s => document.querySelectorAll(s).forEach(e => e.style.display='none'));
        document.querySelectorAll('iframe').forEach(f => {
            try { if ((f.src||'').match(/chat|hubspot|widget/)) f.style.display='none'; } catch(e){}
        });
    }""")


def ir_para_registros(page):
    page.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    suprimir_sophia(page)
    if page.locator(".chakra-spinner").count() > 0:
        page.reload(wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        tw.dispensar_nps(page)
        suprimir_sophia(page)
    try:
        page.wait_for_selector(".chakra-spinner", state="hidden", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1500)


def login_como(page, email, senha, perfil_admin=False):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", email)
    page.fill("#user_password", senha)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    if perfil_admin:
        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
            wait_until="domcontentloaded", timeout=30000,
        )
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)
    log(f"  [login] {email} -> {page.url}")
    return "/login" not in page.url


def dump_form_fields(page):
    """Extrai todos os labels + placeholders + required do form via JS."""
    return page.evaluate("""() => {
        const safe = el => (el && el.innerText != null) ? el.innerText.trim().replace(/\\s+/g, ' ') : '';
        const fields = [];
        document.querySelectorAll('label').forEach(label => {
            try {
                const txt = safe(label);
                if (!txt) return;
                const req = txt.includes('*');
                const forAttr = label.getAttribute('for') || '';
                let inputEl = forAttr ? document.getElementById(forAttr) : null;
                if (!inputEl) {
                    inputEl = label.closest('[class*="chakra"]')?.querySelector('input, select, textarea, [role="combobox"]');
                }
                const placeholder = inputEl ? (inputEl.getAttribute('placeholder') || '') : '';
                const inputType = inputEl ? (inputEl.type || inputEl.tagName.toLowerCase()) : '';
                fields.push({ label: txt, required: req, placeholder, inputType });
            } catch(e) {}
        });

        const btns = [];
        document.querySelectorAll('button').forEach(btn => {
            try {
                const txt = safe(btn);
                if (txt && ['Salvar', 'Cancelar', 'Enviar', 'Aprovar', 'Excluir', 'Voltar', 'Adicionar'].some(k => txt.includes(k))) {
                    btns.push({ text: txt, disabled: btn.disabled });
                }
            } catch(e) {}
        });

        const headings = [];
        document.querySelectorAll('h1, h2, h3').forEach(h => {
            try {
                const txt = safe(h);
                if (txt) headings.push({ tag: h.tagName, text: txt });
            } catch(e) {}
        });

        const chakraTitles = [];
        document.querySelectorAll('[class*="chakra-heading"]').forEach(h => {
            try {
                const txt = safe(h);
                if (txt) chakraTitles.push(txt);
            } catch(e) {}
        });

        const crumbs = [];
        document.querySelectorAll('[aria-label="breadcrumb"] li, .chakra-breadcrumb__list li').forEach(li => {
            try { crumbs.push(safe(li)); } catch(e) {}
        });

        return { fields, buttons: btns, headings, chakraTitles, breadcrumb: crumbs };
    }""")


def main():
    log("=" * 60)
    log("RECON QA 1.6 — Form de Adicionar registro")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)

        # ── RECON ADMIN ──────────────────────────────────────────────────
        log("\n[Recon Admin] Iniciando...")
        ctx_admin = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page_admin = ctx_admin.new_page()

        ok = login_como(page_admin, ADMIN_EMAIL, ADMIN_PASSWORD, perfil_admin=True)
        log(f"  Admin login OK: {ok}")
        tw.snap(page_admin, EVID, "recon_admin_01_login")

        ir_para_registros(page_admin)
        tw.snap(page_admin, EVID, "recon_admin_02_registros")

        # Abrir form via botão Adicionar
        btn_add = page_admin.get_by_role("button", name="Adicionar").first
        if btn_add.count() == 0:
            btn_add = page_admin.locator("button:has-text('Adicionar')").first
        if btn_add.count() > 0 and btn_add.is_visible():
            btn_add.click()
            page_admin.wait_for_timeout(3000)
            suprimir_sophia(page_admin)

        url_form_admin = page_admin.url
        log(f"  URL do form Admin: {url_form_admin}")
        tw.snap(page_admin, EVID, "recon_admin_03_form_topo")

        # Scroll para ver campos abaixo
        page_admin.keyboard.press("End")
        page_admin.wait_for_timeout(1000)
        tw.snap(page_admin, EVID, "recon_admin_04_form_baixo")

        # Scroll para o meio
        page_admin.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        page_admin.wait_for_timeout(500)
        tw.snap(page_admin, EVID, "recon_admin_05_form_meio")

        # Dump dos campos
        data = dump_form_fields(page_admin)
        log("\n  === CAMPOS DO FORM ADMIN ===")
        for f in data.get("fields", []):
            log(f"    Label: '{f['label']}' | Req: {f['required']} | Placeholder: '{f['placeholder']}' | Type: {f['inputType']}")
        log("\n  === BOTÕES ADMIN ===")
        for b in data.get("buttons", []):
            log(f"    Botão: '{b['text']}' | Disabled: {b['disabled']}")
        log("\n  === HEADINGS ADMIN ===")
        for h in data.get("headings", []):
            log(f"    {h['tag']}: '{h['text']}'")
        log("\n  === BREADCRUMB ADMIN ===")
        log(f"    {data.get('breadcrumb', [])}")

        ctx_admin.close()

        # ── RECON ALUNO (qa11tc342588) ──────────────────────────────────
        log("\n[Recon Aluno] Testando qa11tc342588@twygotest.com / twygoqa2026...")
        ctx_aluno = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page_aluno = ctx_aluno.new_page()

        ok_aluno = login_como(page_aluno, ALUNO_EMAIL, ALUNO_PASSWORD, perfil_admin=False)
        log(f"  Aluno login OK: {ok_aluno}")
        tw.snap(page_aluno, EVID, "recon_aluno_01_pos_login")

        if ok_aluno:
            # URL de Meu Histórico confirmada via recon anterior: /o/37079/records?in_use_mode_layout=true
            meu_hist_url = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
            page_aluno.goto(meu_hist_url, wait_until="domcontentloaded", timeout=30000)
            page_aluno.wait_for_timeout(3000)
            tw.dispensar_nps(page_aluno)
            suprimir_sophia(page_aluno)
            if page_aluno.locator(".chakra-spinner").count() > 0:
                page_aluno.reload(wait_until="domcontentloaded", timeout=30000)
                page_aluno.wait_for_timeout(4000)
            log(f"  Meu Histórico URL real: {page_aluno.url}")

            url_meu_hist = page_aluno.url
            log(f"  URL Meu Histórico: {url_meu_hist}")
            tw.snap(page_aluno, EVID, "recon_aluno_02_meu_historico")

            # Clicar Adicionar
            btn_add_aluno = page_aluno.get_by_role("button", name="Adicionar").first
            if btn_add_aluno.count() == 0:
                btn_add_aluno = page_aluno.locator("button:has-text('Adicionar')").first
            if btn_add_aluno.count() > 0 and btn_add_aluno.is_visible():
                btn_add_aluno.click()
                page_aluno.wait_for_timeout(3000)
                suprimir_sophia(page_aluno)
                url_form_aluno = page_aluno.url
                log(f"  URL form Aluno: {url_form_aluno}")
                tw.snap(page_aluno, EVID, "recon_aluno_03_form_topo")
                page_aluno.keyboard.press("End")
                page_aluno.wait_for_timeout(500)
                tw.snap(page_aluno, EVID, "recon_aluno_04_form_baixo")

                # Dump campos aluno
                data_aluno = dump_form_fields(page_aluno)
                log("\n  === CAMPOS DO FORM ALUNO ===")
                for f in data_aluno.get("fields", []):
                    log(f"    Label: '{f['label']}' | Req: {f['required']} | Placeholder: '{f['placeholder']}'")
                log("\n  === BOTÕES ALUNO ===")
                for b in data_aluno.get("buttons", []):
                    log(f"    Botão: '{b['text']}' | Disabled: {b['disabled']}")
                log("\n  === HEADINGS ALUNO ===")
                for h in data_aluno.get("headings", []):
                    log(f"    {h['tag']}: '{h['text']}'")
            else:
                log("  Botão Adicionar não encontrado no form do Aluno")
                tw.snap(page_aluno, EVID, "recon_aluno_sem_adicionar")

        ctx_aluno.close()

        # ── RECON LIDER (url depois de logar) ──────────────────────────
        log("\n[Recon Lider] qalider@teste.com / 123456...")
        ctx_lider = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page_lider = ctx_lider.new_page()
        ok_lider = login_como(page_lider, LIDER_EMAIL, LIDER_PASSWORD, perfil_admin=False)
        log(f"  Lider login OK: {ok_lider}, URL: {page_lider.url}")
        tw.snap(page_lider, EVID, "recon_lider_01_pos_login")

        if ok_lider:
            # Ver se o lider pode acessar Registros como Gestor
            ir_para_registros(page_lider)
            tw.snap(page_lider, EVID, "recon_lider_02_registros")

            # Tentar clicar Adicionar
            btn_add_lider = page_lider.get_by_role("button", name="Adicionar").first
            if btn_add_lider.count() == 0:
                btn_add_lider = page_lider.locator("button:has-text('Adicionar')").first
            log(f"  Botão Adicionar para Lider: {btn_add_lider.count() > 0 and btn_add_lider.is_visible()}")

            if btn_add_lider.count() > 0 and btn_add_lider.is_visible():
                btn_add_lider.click()
                page_lider.wait_for_timeout(3000)
                suprimir_sophia(page_lider)
                tw.snap(page_lider, EVID, "recon_lider_03_form")

                # Clicar no campo Pessoas
                campo_pessoas = page_lider.locator("[placeholder='Adicionar pessoas'], [placeholder*='pessoa'], [placeholder*='colaborador']").first
                if campo_pessoas.count() == 0:
                    campo_pessoas = page_lider.locator("label:has-text('Pessoas')").locator("..").locator("input").first
                if campo_pessoas.count() > 0:
                    campo_pessoas.click()
                    page_lider.wait_for_timeout(1500)
                    tw.snap(page_lider, EVID, "recon_lider_04_dropdown_pessoas")

                    opcoes = page_lider.locator("[role=option]").all_text_contents()
                    log(f"  Opções dropdown Pessoas (Lider): {opcoes}")
                else:
                    log("  Campo Pessoas não encontrado no form do Lider")

        ctx_lider.close()
        browser.close()

    log("\n[Recon] Concluido.")


if __name__ == "__main__":
    main()
