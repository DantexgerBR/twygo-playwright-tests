"""Inspecao na org destinataria (danteshare.stage.twygoead.com) — onde fica o token de ambiente externo?"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.login_page import LoginPage  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_DEST = os.environ.get("BASE_URL_DESTINATARIA", "https://danteshare.stage.twygoead.com/")
EMAIL = os.environ.get("ADMIN_DESTINATARIA_EMAIL", "dante.tavares@twygo.com")
SENHA = os.environ.get("ADMIN_DESTINATARIA_PASSWORD", "SENHA_NO_ENV")
OUT = Path("test-results/inspect_destinataria")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_DEST, EMAIL, SENHA)
        print("[1] logado na destinataria:", page.url)
        page.screenshot(path=str(OUT / "01-pos-login.png"), full_page=True)

        # 1) Compartilhamentos
        page.goto(BASE_DEST + "shared_events", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        print("[2] shared_events:", page.url, "title=", page.title())
        page.screenshot(path=str(OUT / "02-shared_events.png"), full_page=True)

        # listar links / botoes com 'token' / 'compartilh' / 'configuracoes'
        info = page.evaluate(r"""() => {
            const re = /token|compartilh|configura|ambiente externo|chave|secret/i;
            const els = Array.from(document.querySelectorAll('a, button, [role="button"]'))
                .filter(el => re.test((el.innerText || '').trim()) && el.offsetParent !== null);
            return els.slice(0,40).map(el => ({
                tag: el.tagName,
                text: (el.innerText || '').trim().slice(0,120),
                href: el.getAttribute('href'),
                id: el.id,
            }));
        }""")
        print("\nbotoes/links com texto suspeito:")
        for s in info: print(" ", s)

        # 2) Configuracoes da organizacao
        # Twygo costuma ter /o/{id}/edit ou /organization
        for path in ["organization/edit", "settings", "configuracoes"]:
            try:
                page.goto(BASE_DEST + path, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(4000)
                print(f"\n[3] tentou {path}: url={page.url} title={page.title()}")
                page.screenshot(path=str(OUT / f"03-{path.replace('/', '_')}.png"), full_page=True)
            except Exception as e:
                print(f"  ! falhou {path}: {type(e).__name__}")

        # 3) Procurar token na pagina de compartilhamentos com aba/sub-pagina
        page.goto(BASE_DEST + "shared_events", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        # ha tabs? configuracoes?
        info2 = page.evaluate(r"""() => {
            return Array.from(document.querySelectorAll('button[role="tab"], .chakra-tabs__tab'))
                .map(el => ({text: (el.innerText || '').trim(), id: el.id}));
        }""")
        print("\ntabs em shared_events:", info2)

        # 4) Pesquisar o texto 'token' / 'Token de ambiente' em toda a pagina
        text_search = page.evaluate(r"""() => {
            const body = document.body.innerText;
            const lower = body.toLowerCase();
            const tokens = [];
            ['token', 'ambiente externo', 'chave', 'compartilhar com outras', 'integracao'].forEach(needle => {
                let idx = lower.indexOf(needle);
                while (idx !== -1) {
                    tokens.push({needle, ctx: body.slice(Math.max(0, idx-40), idx+120)});
                    idx = lower.indexOf(needle, idx + 1);
                    if (tokens.length > 30) break;
                }
            });
            return tokens.slice(0, 30);
        }""")
        print("\nocorrencias de 'token'/'ambiente externo' no body:")
        for t in text_search: print(" ", t)

        # 5) Tentar /shared_events?tab=settings ou similar
        for q in ["?tab=settings", "?tab=tokens", "?tab=external", "/settings", "/external", "/tokens"]:
            try:
                url = BASE_DEST + "shared_events" + q
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(3500)
                content_has_token = page.evaluate("() => document.body.innerText.toLowerCase().includes('token')")
                print(f"\n  {q} -> token visivel? {content_has_token} url={page.url}")
                if content_has_token:
                    page.screenshot(path=str(OUT / f"05-token-{q.replace('?','').replace('=','_').replace('/','_')}.png"), full_page=True)
            except Exception as e:
                print(f"  ! falhou {q}: {type(e).__name__}")

        browser.close()


if __name__ == "__main__":
    main()
