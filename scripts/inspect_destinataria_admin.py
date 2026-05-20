"""Procurar toggle 'Administrador' na destinataria e mapear menu admin."""
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
OUT = Path("test-results/inspect_destinataria_admin")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_DEST, EMAIL, SENHA)
        page.wait_for_timeout(4000)
        page.screenshot(path=str(OUT / "01-pos-login.png"), full_page=True)

        # listar TODOS botoes/links visiveis para encontrar toggle de perfil
        info = page.evaluate(r"""() => {
            const data = {profile: [], admin_links: [], all_buttons: []};
            // procurar texto 'Aluno' / 'Administrador' / 'perfil'
            document.querySelectorAll('button, a, [role="button"], [role="menu"], select').forEach(el => {
                const t = (el.innerText || '').trim();
                const aria = el.getAttribute('aria-label') || '';
                if (/aluno|administrador|perfil|profile|switch/i.test(t + aria)) {
                    data.profile.push({tag: el.tagName, text: t.slice(0,80), aria, id: el.id, cls: (el.className||'').toString().slice(0,150)});
                }
                if (/admin|configura|organiza/i.test(t + aria) && el.offsetParent !== null) {
                    data.admin_links.push({tag: el.tagName, text: t.slice(0,80), aria, id: el.id, href: el.getAttribute('href')});
                }
                if (el.offsetParent !== null && t && t.length < 60) {
                    data.all_buttons.push({tag: el.tagName, text: t, id: el.id});
                }
            });
            return data;
        }""")
        print("toggle de perfil candidatos:")
        for s in info["profile"]: print(" ", s)
        print("\nlinks admin candidatos:")
        for s in info["admin_links"]: print(" ", s)
        print("\nTODOS botoes/links visiveis (limit 40):")
        for s in info["all_buttons"][:40]: print(" ", s)

        # clicar no profile (canto superior direito — 'Aluno ▼')
        try:
            btn = page.locator("#btn-profile, button:has-text('Aluno'), [aria-label*='perfil']").first
            print(f"\n[click] tentando clicar em btn-profile... count={btn.count()}")
            if btn.count() > 0:
                btn.click()
                page.wait_for_timeout(3000)
                page.screenshot(path=str(OUT / "02-profile-aberto.png"), full_page=True)
                opts = page.evaluate(r"""() => {
                    return Array.from(document.querySelectorAll('a, button, [role="menuitem"]'))
                        .filter(el => el.offsetParent !== null && /admin|aluno|gestor|professor/i.test((el.innerText || '').trim()))
                        .map(el => ({text: (el.innerText || '').trim().slice(0,80), href: el.getAttribute('href'), id: el.id}));
                }""")
                print("\nopcoes do menu de perfil:")
                for o in opts: print(" ", o)
        except Exception as e:
            print(f"falha clicar profile: {e}")

        # tentar acessar /events (lista admin)
        for u in ["events", "o/1/edit", "organization"]:
            try:
                page.goto(BASE_DEST + u, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(4000)
                print(f"\n[{u}] url={page.url}")
                page.screenshot(path=str(OUT / f"03-{u.replace('/', '_')}.png"), full_page=True)
            except Exception as e:
                print(f"  ! falhou {u}: {type(e).__name__}")

        browser.close()


if __name__ == "__main__":
    main()
