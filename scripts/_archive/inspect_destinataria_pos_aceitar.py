"""Apos clicar 'Aceitar' no share recebido, descobrir onde fica o curso espelhado."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.login_page import LoginPage  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BASE_DEST = os.environ["BASE_URL_DESTINATARIA"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_DESTINATARIA_EMAIL"]
SENHA = os.environ["ADMIN_DESTINATARIA_PASSWORD"]
ORG_DEST = os.environ["ORG_DESTINATARIA_ID"]
OUT = Path("test-results/inspect_pos_aceitar")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_DEST, EMAIL, SENHA)
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/events?tab=events&profile=admin",
                  wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(5000)

        # Ir para shared_events > Recebidos
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/shared_events", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(6000)
        page.evaluate("""() => {
            const t = Array.from(document.querySelectorAll('button[role="tab"], .chakra-tabs__tab'))
                .find(el => (el.innerText || '').trim() === 'Recebidos');
            if (t) t.click();
        }""")
        page.wait_for_timeout(5000)

        # Clicar no edit (pencil) do share Construindo times
        page.evaluate(r"""() => {
            const rows = Array.from(document.querySelectorAll('tr, [role=row]'))
                .filter(r => /Construindo times de alta performance/i.test(r.innerText || ''));
            if (!rows.length) return;
            const row = rows[0];
            const icon = Array.from(row.querySelectorAll('.material-symbols-outlined, span'))
                .find(el => (el.innerText || '').trim() === 'edit');
            if (!icon) return;
            let p = icon;
            for (let i = 0; i < 6 && p; i++) {
                if (p.tagName === 'BUTTON' || p.tagName === 'A' || p.onclick) break;
                p = p.parentElement;
            }
            (p || icon).click();
        }""")
        page.wait_for_timeout(7000)
        print("URL na pagina accept:", page.url)
        page.screenshot(path=str(OUT / "01-accept-form.png"), full_page=True)

        # Clicar em Aceitar via locator nativo
        btn_aceitar = page.get_by_role("button", name="Aceitar").first
        print(f"\n[btn Aceitar] count={btn_aceitar.count()} visible={btn_aceitar.is_visible() if btn_aceitar.count() else False}")
        btn_aceitar.scroll_into_view_if_needed()
        btn_aceitar.click()
        page.wait_for_timeout(5000)
        page.screenshot(path=str(OUT / "02a-imediato.png"), full_page=True)

        # ha confirmacao modal?
        modal = page.evaluate(r"""() => {
            const m = Array.from(document.querySelectorAll('[role="dialog"], .chakra-modal__content'))
                .find(d => !/Notifica/i.test(d.querySelector('header')?.innerText || ''));
            if (!m) return null;
            return {
                text: (m.innerText || '').slice(0,500),
                buttons: Array.from(m.querySelectorAll('button')).map(b => (b.innerText || '').trim()).filter(Boolean),
            };
        }""")
        print("\nmodal pos-aceitar:", modal)
        if modal and modal.get("buttons"):
            # confirmar
            page.evaluate(r"""() => {
                const m = Array.from(document.querySelectorAll('[role="dialog"], .chakra-modal__content'))
                    .find(d => !/Notifica/i.test(d.querySelector('header')?.innerText || ''));
                if (!m) return;
                const btn = Array.from(m.querySelectorAll('button'))
                    .find(b => /aceitar|confirmar|sim/i.test((b.innerText || '').trim()));
                if (btn) btn.click();
            }""")
            page.wait_for_timeout(6000)

        print("URL pos-aceitar:", page.url)
        page.screenshot(path=str(OUT / "02-pos-aceitar.png"), full_page=True)

        # 1) listar eventos da destinataria (deve aparecer Construindo times)
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/events?tab=events", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(8000)
        page.screenshot(path=str(OUT / "03-events-pos-aceite.png"), full_page=True)
        eventos = page.evaluate(r"""() => {
            const data = [];
            // procurar links/cards com href /e/{id} ou data-id
            const seen = new Set();
            document.querySelectorAll('a[href*="/e/"], [data-id]').forEach(el => {
                let id = el.getAttribute('data-id');
                if (!id) {
                    const m = (el.href || el.getAttribute('href') || '').match(/\/e\/(\d+)/);
                    id = m ? m[1] : null;
                }
                if (!id || seen.has(id)) return;
                seen.add(id);
                const text = (el.innerText || '').trim().slice(0, 200);
                data.push({id, text, href: el.getAttribute('href')});
            });
            return data;
        }""")
        print("\neventos visiveis pos-aceite:")
        for e in eventos:
            if "Construindo" in (e.get("text") or "") or e.get("text", "").strip():
                print(" ", e)

        # 2) Procurar evento "Construindo times" especificamente
        curso = page.evaluate(r"""() => {
            const re = /Construindo times de alta performance/i;
            const cands = Array.from(document.querySelectorAll('*'))
                .filter(el => re.test(el.innerText || '') && el.children.length < 20)
                .slice(0, 5);
            return cands.map(el => ({
                tag: el.tagName,
                text: (el.innerText || '').trim().slice(0,200),
                outerHTML: el.outerHTML.slice(0, 1500),
            }));
        }""")
        print("\ncandidatos visiveis com texto Construindo times:")
        for c in curso[:3]: print(" ", c["text"])

        browser.close()


if __name__ == "__main__":
    main()
