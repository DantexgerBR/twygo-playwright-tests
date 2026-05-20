"""Confere se 9187421 (atividade 'Conteúdo 1' em 787697) é uma legada de verdade
— video sem secao de marca d'agua no form de edicao."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.login_page import LoginPage  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BASE_URL = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
SENHA = os.environ["ADMIN_PASSWORD"]
OUT = Path("test-results/inspect_9187421_legada")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        try:
            LoginPage(page).login(BASE_URL, EMAIL, SENHA)
        except Exception:
            page.wait_for_timeout(3000)

        # ediçao
        try:
            page.goto(f"{BASE_URL}e/787697/contents/9187421/edit", wait_until="networkidle", timeout=25000)
        except Exception:
            pass
        page.wait_for_timeout(8000)
        page.screenshot(path=str(OUT / "01-edit.png"), full_page=True)

        info = page.evaluate(r"""() => {
            const data = {};
            // verificar se tem ANY video element / video file uploader
            data.tem_video_tag = !!document.querySelector('video');
            data.tem_file_input = Array.from(document.querySelectorAll('input[type=file]')).map(i => ({name: i.name, accept: i.accept || ''}));
            // procurar texto 'video' / 'vídeo' / 'mp4' no form
            data.body_substring = document.body.innerText.slice(0, 1200);
            // listar labels do form
            data.labels = Array.from(document.querySelectorAll('label')).map(l => (l.innerText || '').trim().slice(0,100));
            // ha selecao de tipo de atividade?
            data.tipo_selecionado = Array.from(document.querySelectorAll('select[name*="type"], input[name*="type"]:checked, [name="kind"]'))
                .map(el => ({name: el.name, value: el.value, tag: el.tagName}));
            // ha qualquer mencao a watermark/marca d'agua?
            data.tem_marca_dagua_no_html = /marca.{0,3}d.{0,3}gua|water.?mark/i.test(document.body.innerHTML);
            // capturar todos os campos visiveis do form
            data.inputs_visiveis = [];
            document.querySelectorAll('input, select, textarea').forEach(el => {
                if (el.offsetParent === null) return;
                data.inputs_visiveis.push({
                    tag: el.tagName, type: el.type, name: el.name, id: el.id,
                    value: (el.value || '').slice(0,80), readonly: el.readOnly,
                });
            });
            return data;
        }""")

        print("=== form de edicao /e/787697/contents/9187421/edit ===")
        print("tem <video>:", info["tem_video_tag"])
        print("inputs file:", info["tem_file_input"])
        print("body (1200ch):")
        print(info["body_substring"])
        print("\nlabels:", info["labels"])
        print("\ntipo selecionado:", info["tipo_selecionado"])
        print("\ntem texto 'marca d'agua' no html:", info["tem_marca_dagua_no_html"])
        print("\ninputs visiveis no form:")
        for i in info["inputs_visiveis"][:30]: print(" ", i)

        browser.close()


if __name__ == "__main__":
    main()
