"""Script de debug para explorar o form de criacao de registro e usuario."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ADMIN_EMAIL = "dante.tavares@twygo.com"
ADMIN_SENHA = "123456"
ORG_ID = "37079"

SLUG = "registros-f2-qa11"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg)


def main():
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            # Login como aluno para explorar o form de registros
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("#user_email", timeout=10000)
            page.fill("#user_email", ADMIN_EMAIL)
            page.fill("#user_password", ADMIN_SENHA)
            page.click("#user_submit")
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            log(f"Logado: {page.url[:60]}")

            # Abre form de criacao de registro
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/records/new?in_use_mode_layout=true",
                wait_until="domcontentloaded", timeout=25000
            )
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            tw.snap(page, EVID, "debug_form_inicial")
            log(f"Form URL: {page.url[:60]}")

            # Lista todos os inputs do form
            all_inputs = page.evaluate("""() => {
                const inputs = document.querySelectorAll('input, select, textarea');
                return Array.from(inputs).map(el => ({
                    tag: el.tagName,
                    id: el.id || '',
                    name: el.name || '',
                    type: el.type || '',
                    placeholder: el.placeholder || '',
                    value: el.value || '',
                    visible: el.offsetParent !== null,
                }));
            }""")
            log(f"\nInputs no form ({len(all_inputs)}):")
            for inp in all_inputs:
                if inp.get('visible'):
                    log(f"  [{inp['tag']}] id={inp['id']!r} name={inp['name']!r} "
                        f"type={inp['type']!r} placeholder={inp['placeholder'][:40]!r}")

            # Lista todos os react-select inputs
            rs_inputs = page.evaluate("""() => {
                const els = document.querySelectorAll('[id*="react-select"]');
                return Array.from(els).map(el => ({
                    id: el.id,
                    tag: el.tagName,
                    visible: el.offsetParent !== null,
                    placeholder: el.getAttribute('placeholder') || '',
                }));
            }""")
            log(f"\nReact-select inputs ({len(rs_inputs)}):")
            for rs in rs_inputs:
                log(f"  id={rs['id']!r} tag={rs['tag']} visible={rs['visible']}")

            # Tenta preencher provedor
            log("\n=== Tentando preencher Provedor (react-select-2-input) ===")
            inp = page.locator("#react-select-2-input")
            log(f"  count: {inp.count()}")
            if inp.count() > 0:
                inp.click(timeout=3000)
                page.wait_for_timeout(500)
                inp.fill("Alura")
                page.wait_for_timeout(1000)
                tw.snap(page, EVID, "debug_form_provedor_digitado")

                opcoes = page.locator("[class*='__option']").all()
                log(f"  Opcoes apos digitar 'Alura': {len(opcoes)}")
                for op in opcoes[:5]:
                    try:
                        log(f"    - {op.inner_text()[:40]!r}")
                    except Exception:
                        pass

            # Screenshot pos preenchimento do provedor
            tw.snap(page, EVID, "debug_form_apos_provedor")

            # Tenta conteudo
            log("\n=== Tentando preencher Conteudo (react-select-3-input) ===")
            inp3 = page.locator("#react-select-3-input")
            log(f"  count: {inp3.count()}")
            if inp3.count() > 0:
                inp3.click(timeout=3000)
                page.wait_for_timeout(300)
                inp3.fill("QA11-Teste")
                page.wait_for_timeout(800)
                opcoes3 = page.locator("[class*='__option']").all()
                log(f"  Opcoes apos digitar 'QA11-Teste': {len(opcoes3)}")
                for op in opcoes3[:3]:
                    try:
                        log(f"    - {op.inner_text()[:40]!r}")
                    except Exception:
                        pass

            # Tipo experiencia
            log("\n=== Tentando preencher Tipo Experiencia (react-select-4-input) ===")
            inp4 = page.locator("#react-select-4-input")
            log(f"  count: {inp4.count()}")
            if inp4.count() > 0:
                inp4.click(timeout=3000)
                page.wait_for_timeout(300)
                inp4.fill("Curs")
                page.wait_for_timeout(800)
                opcoes4 = page.locator("[class*='__option']").all()
                log(f"  Opcoes apos digitar 'Curs': {len(opcoes4)}")
                for op in opcoes4[:5]:
                    try:
                        log(f"    - {op.inner_text()[:40]!r}")
                    except Exception:
                        pass

            # Categorias
            log("\n=== Tentando preencher Categorias (react-select-5-input) ===")
            inp5 = page.locator("#react-select-5-input")
            log(f"  count: {inp5.count()}")
            if inp5.count() > 0:
                inp5.click(timeout=3000)
                page.wait_for_timeout(500)
                opcoes5 = page.locator("[class*='__option']").all()
                log(f"  Opcoes: {len(opcoes5)}")
                for op in opcoes5[:5]:
                    try:
                        log(f"    - {op.inner_text()[:40]!r}")
                    except Exception:
                        pass
            else:
                log("  Campo #react-select-5-input nao encontrado!")
                # Lista os selects disponiveis
                selects_avail = page.evaluate("""() => {
                    const inputs = document.querySelectorAll('[id*="react-select"]');
                    return Array.from(inputs).map(el => el.id).filter(id => id.includes('input'));
                }""")
                log(f"  React-select inputs disponiveis: {selects_avail}")

            tw.snap(page, EVID, "debug_form_campos_preenchidos")

            # Verifica se ha campo de categorias em outra posicao
            log("\n=== Verificando labels do form ===")
            labels = page.evaluate("""() => {
                const labels = document.querySelectorAll('label, [class*="label"]');
                return Array.from(labels).map(el => el.innerText?.trim()).filter(t => t && t.length < 60);
            }""")
            log(f"  Labels: {labels}")

        finally:
            ctx.close()
            browser.close()


if __name__ == "__main__":
    main()
