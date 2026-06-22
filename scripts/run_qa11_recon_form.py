"""run_qa11_recon_form.py — Reconhece o form de registro do Aluno em detalhe."""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "registros-f2-qa11"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)

BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
ALUNO_EMAIL = os.environ.get("ALUNO_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ORG_ID = os.environ.get("ORG_ID", "36675")
RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"


def log(msg):
    print(msg)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    # Login como Aluno
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", ALUNO_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    log(f"Logado: {page.url[:60]}")

    # Navega para Meu histórico
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=25000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    tw.snap(page, EVID, "recon_01_meu_historico")

    # Clica em Adicionar
    btn = page.get_by_role("button", name=re.compile("Adicionar", re.I)).first
    if btn.count() == 0:
        btn = page.locator("button, a").filter(has_text="Adicionar").first

    log(f"Botão Adicionar encontrado: {btn.count() > 0}")
    if btn.count() > 0:
        btn.click(timeout=5000)
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)
        tw.snap(page, EVID, "recon_02_form_aberto")

        # Dump completo do form
        dump = page.evaluate("""() => {
            const result = {};

            // URL atual
            result.url = window.location.href;

            // Todos os inputs com label associado
            result.campos = [];
            const inputs = document.querySelectorAll('input, textarea, select');
            for (const inp of inputs) {
                const rect = inp.getBoundingClientRect();
                if (rect.width < 1) continue;

                let labelText = '';
                if (inp.id) {
                    const lbl = document.querySelector(`label[for="${inp.id}"]`);
                    if (lbl) labelText = lbl.innerText?.trim();
                }
                if (!labelText) {
                    let parent = inp.parentElement;
                    for (let i = 0; i < 5; i++) {
                        if (!parent) break;
                        const prevLbl = parent.querySelector('label');
                        if (prevLbl) { labelText = prevLbl.innerText?.trim(); break; }
                        parent = parent.parentElement;
                    }
                }

                result.campos.push({
                    tag: inp.tagName,
                    type: inp.type || '',
                    name: inp.name || '',
                    id: inp.id?.substring(0, 50) || '',
                    placeholder: inp.placeholder?.substring(0, 60) || '',
                    label: labelText?.substring(0, 60) || '',
                    value: inp.value?.substring(0, 30) || '',
                    x: Math.round(rect.x),
                    y: Math.round(rect.y)
                });
            }

            // Botões
            result.botoes = Array.from(document.querySelectorAll('button')).filter(b => {
                const r = b.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }).map(b => ({
                text: b.innerText?.trim()?.substring(0, 50) || '',
                type: b.type || '',
                disabled: b.disabled,
                x: Math.round(b.getBoundingClientRect().x),
                y: Math.round(b.getBoundingClientRect().y)
            }));

            // React-select inputs (Chakra UI selects)
            result.react_selects = Array.from(document.querySelectorAll('[class*="react-select"]')).filter(el => {
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }).slice(0, 20).map(el => ({
                class: el.className?.substring(0, 80) || '',
                text: el.innerText?.trim()?.substring(0, 60) || '',
                x: Math.round(el.getBoundingClientRect().x),
                y: Math.round(el.getBoundingClientRect().y)
            }));

            return result;
        }""")

        log(f"\nURL após abrir form: {dump.get('url', 'N/A')}")
        log(f"\n=== CAMPOS ({len(dump.get('campos', []))}) ===")
        for c in dump.get('campos', []):
            log(f"  [{c['y']:4d}] {c['tag']:<8} type={c['type']:<8} id={c['id']:<30} label='{c['label'][:40]}' ph='{c['placeholder'][:40]}'")

        log(f"\n=== BOTÕES ({len(dump.get('botoes', []))}) ===")
        for b in dump.get('botoes', []):
            log(f"  [{b['y']:4d},{b['x']:4d}] '{b['text']}' type={b['type']} disabled={b['disabled']}")

        log(f"\n=== REACT SELECTS ({len(dump.get('react_selects', []))}) ===")
        for rs in dump.get('react_selects', [])[:15]:
            log(f"  [{rs['y']:4d}] class='{rs['class'][:60]}' text='{rs['text'][:40]}'")

        # Scroll do form para ver se tem mais campos embaixo
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        tw.snap(page, EVID, "recon_03_form_scrolled")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        # Tenta preencher o campo Conteúdo (título)
        log("\n=== TENTANDO PREENCHER CAMPOS ===")

        # Provedor — react-select com ID react-select-2-input
        try:
            prov_input = page.locator("#react-select-2-input, #react-select-3-input").first
            log(f"Provedor input: {prov_input.count()}")
            if prov_input.count() > 0:
                prov_input.click()
                page.wait_for_timeout(500)
                prov_input.fill("Alura")
                page.wait_for_timeout(800)
                opcoes = page.locator("[class*='react-select__option'], [id*='react-select']").all()
                log(f"Opções após 'Alura': {[o.inner_text()[:40] for o in opcoes[:8]]}")
                if opcoes:
                    opcoes[0].click()
                    page.wait_for_timeout(300)
                else:
                    page.keyboard.press("Escape")
        except Exception as e:
            log(f"Provedor erro: {e}")

        # Conteúdo — qual input tem label "Conteúdo"?
        try:
            conteudo_input = page.get_by_label(re.compile("Conteúdo", re.I)).first
            log(f"Conteúdo label: {conteudo_input.count()}")
            if conteudo_input.count() > 0 and conteudo_input.is_visible(timeout=1000):
                log(f"  Tag: {conteudo_input.evaluate('el => el.tagName')}")
                log(f"  Role: {conteudo_input.evaluate('el => el.getAttribute(\"role\")')}")
                conteudo_input.fill("QA11-Teste-Recon")
                page.wait_for_timeout(800)
                opcoes_cont = page.locator("[class*='react-select__option']").all()
                log(f"  Opções conteúdo: {[o.inner_text()[:40] for o in opcoes_cont[:5]]}")
        except Exception as e:
            log(f"Conteúdo erro: {e}")

        # Carga horária — campo workload_seconds (HH:MM:SS)
        try:
            carga_input = page.locator("input[name='workload_seconds']").first
            log(f"Carga (workload_seconds): {carga_input.count()}")
            if carga_input.count() > 0:
                log(f"  Placeholder: {carga_input.get_attribute('placeholder')}")
                log(f"  Type: {carga_input.get_attribute('type')}")
        except Exception as e:
            log(f"Carga erro: {e}")

        # Data de término e validade
        try:
            date_inputs = page.locator("input[type='date']").all()
            log(f"\nDate inputs: {len(date_inputs)}")
            for di in date_inputs:
                log(f"  id={di.get_attribute('id')} name={di.get_attribute('name')}")
        except Exception as e:
            log(f"Date inputs erro: {e}")

        tw.snap(page, EVID, "recon_04_campos_preenchidos")

    ctx.close()
    browser.close()

log("\nRecon concluído. Veja screenshots em evidencias/registros-f2-qa11/recon_*.png")
