"""Logar na destinataria, trocar para perfil Admin, achar o token de ambiente externo."""
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
SENHA = "SENHA_NO_ENV"
ORG_DEST = "37018"
OUT = Path("test-results/inspect_destinataria_admin2")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_DEST, EMAIL, SENHA)

        # Switch profile -> Admin
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/events?tab=events&profile=admin",
                  wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(7000)
        print("admin events:", page.url)
        page.screenshot(path=str(OUT / "01-admin-events.png"), full_page=True)

        # 1) /o/37018/shared_events
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/shared_events", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(6000)
        print("\nshared_events:", page.url)
        page.screenshot(path=str(OUT / "02-shared_events.png"), full_page=True)

        # mapear botoes/textos em shared_events
        info = page.evaluate(r"""() => {
            const data = {tabs: [], buttons: [], text_token: []};
            document.querySelectorAll('button[role="tab"], .chakra-tabs__tab').forEach(el => {
                data.tabs.push((el.innerText || '').trim());
            });
            document.querySelectorAll('button, a').forEach(el => {
                if (el.offsetParent === null) return;
                const t = (el.innerText || '').trim();
                if (t && t.length < 50) data.buttons.push({tag: el.tagName, text: t, id: el.id, href: el.getAttribute('href')});
            });
            const body = document.body.innerText;
            const lower = body.toLowerCase();
            ['token', 'ambiente externo', 'gerar token', 'copiar', 'configura'].forEach(n => {
                let idx = lower.indexOf(n);
                while (idx !== -1) {
                    data.text_token.push({n, ctx: body.slice(Math.max(0, idx-60), idx+160)});
                    idx = lower.indexOf(n, idx + 1);
                    if (data.text_token.length > 30) break;
                }
            });
            return data;
        }""")
        print("tabs:", info["tabs"])
        print("\nocorrencias de token/ambiente externo:")
        for s in info["text_token"]: print(" ", s)
        print("\nbotoes/links (top 50):")
        for s in info["buttons"][:50]: print(" ", s)

        # 2) Procurar Configuracoes da org no menu lateral
        # 3) Tentar 'Configuracoes -> Compartilhamento' / 'Sharing Settings'
        for u in [
            f"o/{ORG_DEST}/shared_events/settings",
            f"o/{ORG_DEST}/sharing_settings",
            f"o/{ORG_DEST}/shareable_token",
            f"o/{ORG_DEST}/edit",
            f"o/{ORG_DEST}/integrations",
            "configurations/edit",
        ]:
            try:
                page.goto(BASE_DEST + u, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(4500)
                txt_has = page.evaluate("() => document.body.innerText.toLowerCase().includes('token')")
                print(f"\n[{u}] url={page.url}  token visivel? {txt_has}")
                if txt_has:
                    page.screenshot(path=str(OUT / f"04-{u.replace('/', '_')}.png"), full_page=True)
                    # extrair o token
                    info2 = page.evaluate(r"""() => {
                        const body = document.body.innerText;
                        const tok = [];
                        document.querySelectorAll('input').forEach(el => {
                            if (el.offsetParent === null) return;
                            tok.push({type: el.type, name: el.name, id: el.id, value: el.value, ph: el.placeholder});
                        });
                        // procurar long alphanumeric strings (>=20 chars)
                        const matches = body.match(/[A-Za-z0-9_\-=]{20,}/g) || [];
                        return {inputs: tok, candidatos_token: matches.slice(0, 15)};
                    }""")
                    print("  inputs visiveis:", info2["inputs"])
                    print("  candidatos a token:", info2["candidatos_token"])
            except Exception as e:
                print(f"  ! falhou {u}: {type(e).__name__}")

        # 4) Olhar a barra lateral em busca de uma sub-menu Compartilhamento -> Configuracoes
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/shared_events", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(5000)
        # hover/click no menu "Compartilhamentos" no sidebar para ver submenu
        page.evaluate("""() => {
            const m = document.querySelector('#shared_events, a[href*="shared_events"]');
            if (m) m.click();
        }""")
        page.wait_for_timeout(3000)
        sub = page.evaluate(r"""() => {
            return Array.from(document.querySelectorAll('a, button'))
                .filter(el => el.offsetParent !== null)
                .map(el => ({text: (el.innerText || '').trim().slice(0,80), href: el.getAttribute('href'), id: el.id}))
                .filter(x => x.text && x.href && /shared|compartil|token/i.test(x.text + x.href));
        }""")
        print("\nlinks suspeitos no menu compartilhamentos:")
        for s in sub: print(" ", s)

        browser.close()


if __name__ == "__main__":
    main()
