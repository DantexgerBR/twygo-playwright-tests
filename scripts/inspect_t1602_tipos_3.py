"""Abre o form de edição de cada atividade conhecida e captura:
- content_type / media_type (de inputs hidden do form)
- presença do checkbox #water-mark-video-enabled
- texto do tipo se visível
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

OUT = Path("test-results/inspect_t1602_tipos_3")
OUT.mkdir(parents=True, exist_ok=True)

# Lista de atividades pra inspecionar — varrer o 787697 inteiro + 9280032 (787696)
ATIVIDADES = [
    ("787696", "9280032", "Vídeo Interno (Novo 1) - REFERÊNCIA POSITIVA"),
    ("787697", "9187421", "Conteúdo 1 (vídeo externo - já documentado)"),
    ("787697", "9187422", "Material de apoio"),
    ("787697", "9187423", "Apresentação"),
    ("787697", "9187430", "Avaliação - Conteúdo 1"),
    ("787697", "9187425", "Conteúdo adicional"),
    ("787697", "9187426", "Apostila"),
    ("787697", "9187428", "Ebook"),
    ("787697", "9187429", "Avaliação do curso"),
    ("787720", "9273084", "Novo 1 (evento 787720)"),
]


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(2500)

        resultados = []
        for ev_id, ativ_id, descricao in ATIVIDADES:
            url = f"{BASE}e/{ev_id}/contents/{ativ_id}/edit"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
            except Exception as e:
                resultados.append({"ev": ev_id, "ativ": ativ_id, "desc": descricao, "erro_goto": str(e)})
                continue
            page.wait_for_timeout(5000)
            page.screenshot(path=str(OUT / f"edit_{ev_id}_{ativ_id}.png"), full_page=True)

            info = page.evaluate(r"""() => {
                const data = {url: window.location.href};
                // hidden inputs comuns
                const ctype = document.querySelector('input[name="content_type"], select[name="content_type"], input[name="content[content_type]"], input[name="media_type"], input[name="content[media_type]"]');
                data.content_type_el = ctype ? {name: ctype.name, value: ctype.value} : null;

                // 'media_type' Rails
                const allInputs = Array.from(document.querySelectorAll('input, select'));
                data.media_inputs = allInputs
                    .filter(i => /content_type|media_type|external_type|external/i.test(i.name||''))
                    .map(i => ({name: i.name, value: i.value, type: i.type}));

                // Texto que indica tipo na breadcrumb/cabecalho
                const heading = document.querySelector('h1, h2, .page-title, header')?.innerText?.slice(0,200) || '';
                data.heading = heading.replace(/\s+/g,' ');

                // Marca d'agua: checkbox visivel?
                const cb = document.querySelector('#water-mark-video-enabled');
                const labelText = Array.from(document.querySelectorAll('label, p, div, span'))
                    .map(el => (el.innerText||'').trim())
                    .find(t => /Habilitar marca d['']água/i.test(t || '')) || null;
                data.water_checkbox_exists = !!cb;
                data.water_label_text = labelText ? labelText.slice(0, 80) : null;

                return data;
            }""")
            info["ev"] = ev_id
            info["ativ"] = ativ_id
            info["desc"] = descricao
            resultados.append(info)
            print(f"\n--- {ev_id}/{ativ_id} ({descricao}) ---")
            print(f"  url={info.get('url')}")
            print(f"  content_type_el={info.get('content_type_el')}")
            print(f"  media_inputs={info.get('media_inputs')}")
            print(f"  heading={info.get('heading','')[:120]}")
            print(f"  water_checkbox={info.get('water_checkbox_exists')} label={info.get('water_label_text')!r}")

        with open(OUT / "results.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
