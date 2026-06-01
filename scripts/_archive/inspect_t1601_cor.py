"""Inspeciona como o form de edição da atividade de vídeo expõe a 'cor da fonte'
e a 'transparência' (alpha) da marca d'água. Sem isso não dá pra reproduzir T-1601.

Salva screenshot full-page + dump JSON dos elementos relevantes (color inputs,
sliders, inputs numéricos próximos a labels 'Cor'/'Transparência'/'Opacidade').
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
ATIV = os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"]

OUT = Path("test-results/inspect_t1601_cor")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(8000)

        # Habilita marca d'água se estiver desmarcada — assim os campos da seção ficam visíveis
        try:
            cb = page.get_by_label("Habilitar marca d'água no vídeo")
            cb.scroll_into_view_if_needed()
            if not cb.is_checked():
                try:
                    cb.check(timeout=3000)
                except Exception:
                    page.locator("text=Habilitar marca d'água no vídeo").first.click()
                page.wait_for_timeout(1500)
        except Exception as e:
            print(f"[warn] não habilitou marca: {e}")

        page.screenshot(path=str(OUT / "01-form-aberto.png"), full_page=True)

        info = page.evaluate(r"""() => {
            // 1) Color inputs no documento todo
            const colors = Array.from(document.querySelectorAll('input[type="color"]')).map(el => ({
                id: el.id, name: el.name, value: el.value,
                label: (el.id && document.querySelector(`label[for='${el.id}']`)?.innerText) || null,
                parentText: el.parentElement?.innerText?.slice(0, 120) || null,
            }));

            // 2) Buscar labels com 'Cor', 'Transparência', 'Opacidade', 'Alpha' e listar inputs próximos
            const wantedTexts = ['cor da fonte', 'transparência', 'transparencia', 'opacidade', 'alpha'];
            const all = Array.from(document.querySelectorAll('label, span, div, h3, h4, p'));
            const matches = [];
            for (const el of all) {
                const t = (el.innerText || '').trim().toLowerCase();
                if (!t || t.length > 80) continue;
                for (const w of wantedTexts) {
                    if (t.includes(w)) {
                        const container = el.closest('div, section, fieldset') || el.parentElement;
                        const inputs = container ? Array.from(container.querySelectorAll('input, select')).map(i => ({
                            tag: i.tagName, type: i.type, id: i.id, name: i.name, value: i.value,
                            placeholder: i.placeholder, role: i.getAttribute('role'),
                            'aria-label': i.getAttribute('aria-label'),
                        })) : [];
                        matches.push({label: t, tag: el.tagName, id: el.id, inputs: inputs.slice(0, 8)});
                        break;
                    }
                }
            }

            // 3) Procurar slider (input range) na seção de marca d'água
            const ranges = Array.from(document.querySelectorAll('input[type="range"]')).map(el => ({
                id: el.id, name: el.name, value: el.value, min: el.min, max: el.max, step: el.step,
                'aria-label': el.getAttribute('aria-label'),
                ancestorText: (el.closest('div, section')?.innerText || '').slice(0, 200),
            }));

            // 4) Procurar Chakra sliders (role=slider)
            const chakraSliders = Array.from(document.querySelectorAll('[role="slider"]')).map(el => ({
                'aria-valuenow': el.getAttribute('aria-valuenow'),
                'aria-valuemin': el.getAttribute('aria-valuemin'),
                'aria-valuemax': el.getAttribute('aria-valuemax'),
                'aria-label': el.getAttribute('aria-label'),
                'aria-valuetext': el.getAttribute('aria-valuetext'),
                ancestorText: (el.closest('div, section')?.innerText || '').slice(0, 200),
            }));

            // 5) #water-mark-video-font-color contexto (já sabemos que existe)
            const fc = document.querySelector('#water-mark-video-font-color');
            const fcInfo = fc ? {
                tag: fc.tagName, type: fc.type, value: fc.value,
                outer: fc.outerHTML.slice(0, 300),
                parentOuter: fc.parentElement?.outerHTML?.slice(0, 600),
                grandparentOuter: fc.parentElement?.parentElement?.outerHTML?.slice(0, 1200),
            } : null;

            return {color_inputs: colors, label_matches: matches, ranges, chakraSliders, fontColorEl: fcInfo};
        }""")

        with open(OUT / "info.json", "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

        print("== color inputs ==")
        print(json.dumps(info["color_inputs"], indent=2, ensure_ascii=False))
        print("\n== label matches (Cor/Transparência/Opacidade/Alpha) ==")
        print(json.dumps(info["label_matches"], indent=2, ensure_ascii=False)[:4000])
        print("\n== range/slider inputs ==")
        print(json.dumps(info["ranges"], indent=2, ensure_ascii=False))
        print("\n== chakra role=slider ==")
        print(json.dumps(info["chakraSliders"], indent=2, ensure_ascii=False))
        print("\n== #water-mark-video-font-color ==")
        print(json.dumps(info["fontColorEl"], indent=2, ensure_ascii=False)[:2000])

        # Tenta clicar no controle de cor pra ver se abre um picker com alpha
        try:
            fc = page.locator("#water-mark-video-font-color")
            fc.scroll_into_view_if_needed()
            page.screenshot(path=str(OUT / "02-cor-antes-clique.png"), full_page=True)
            # Clica no parent visível ao invés do <input type=color> direto
            fc.evaluate("e => e.click()")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "03-cor-apos-clique.png"), full_page=True)
        except Exception as e:
            print(f"[warn] click no fontColor falhou: {e}")

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
