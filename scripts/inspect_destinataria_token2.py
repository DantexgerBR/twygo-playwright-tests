"""Aba 'Token' em /o/37018/integrations — esperado: campo/botao para gerar token de ambiente externo."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.login_page import LoginPage  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BASE_DEST = "https://danteshare.stage.twygoead.com/"
EMAIL = "dante.tavares@twygo.com"
SENHA = "123456"
ORG_DEST = "37018"
OUT = Path("test-results/inspect_destinataria_token2")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_DEST, EMAIL, SENHA)
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/integrations", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(7000)
        page.screenshot(path=str(OUT / "01-integrations.png"), full_page=True)

        # clicar na aba Token
        clicou = page.evaluate(r"""() => {
            const t = Array.from(document.querySelectorAll('button, a, [role=tab]'))
                .find(el => (el.innerText || '').trim() === 'Token' && el.offsetParent !== null);
            if (t) { t.click(); return true; }
            return false;
        }""")
        print(f"[click Token] {clicou}")
        page.wait_for_timeout(5000)
        page.screenshot(path=str(OUT / "02-aba-token.png"), full_page=True)

        # ler conteudo da aba
        info = page.evaluate(r"""() => {
            const data = {labels: [], inputs: [], buttons: [], text_sample: ''};
            // procurar painel ativo
            const panel = document.querySelector('[role=tabpanel]:not([hidden])')
                || document.querySelector('.chakra-tabs__tab-panel')
                || document.body;
            data.text_sample = (panel.innerText || '').slice(0, 1500);
            panel.querySelectorAll('label').forEach(el => data.labels.push((el.innerText || '').trim().slice(0,100)));
            panel.querySelectorAll('input, textarea, select').forEach(el => {
                if (el.offsetParent === null) return;
                data.inputs.push({
                    tag: el.tagName, type: el.type, name: el.name, id: el.id,
                    placeholder: el.placeholder, value: el.value, readonly: el.readOnly,
                });
            });
            panel.querySelectorAll('button, a').forEach(el => {
                if (el.offsetParent === null) return;
                const t = (el.innerText || '').trim();
                if (t && t.length < 60) data.buttons.push({tag: el.tagName, text: t, id: el.id, cls: (el.className || '').toString().slice(0,150)});
            });
            return data;
        }""")
        print("\nlabels no painel Token:", info["labels"])
        print("\ninputs:", info["inputs"])
        print("\nbotoes:", info["buttons"])
        print("\ntext_sample:")
        print(info["text_sample"])

        # se houver botao 'Gerar token' ou similar, clicar
        gerou = page.evaluate(r"""() => {
            const cand = Array.from(document.querySelectorAll('button, a'))
                .find(el => /gerar|criar|nov[oa]|adicion/i.test((el.innerText || '').trim()) && el.offsetParent !== null);
            if (!cand) return null;
            cand.click();
            return (cand.innerText || '').trim();
        }""")
        if gerou:
            print(f"\nclicou em: {gerou!r}")
            page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / "03-pos-gerar.png"), full_page=True)
            # tentar capturar o token recem gerado
            apos = page.evaluate(r"""() => {
                const data = {inputs: [], texts: []};
                document.querySelectorAll('input, textarea').forEach(el => {
                    if (el.offsetParent === null) return;
                    data.inputs.push({type: el.type, name: el.name, id: el.id, value: el.value, readonly: el.readOnly});
                });
                const body = document.body.innerText;
                const matches = body.match(/[A-Za-z0-9_\-=.]{30,}/g) || [];
                data.texts = matches.slice(0, 10);
                return data;
            }""")
            print("inputs pos-gerar:", apos["inputs"])
            print("candidatos token (>=30 chars):", apos["texts"])

        browser.close()


if __name__ == "__main__":
    main()
