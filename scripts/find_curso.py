"""Encontra o curso 'Construindo times de alta performance' e descobre IDs."""
import os, re
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ALUNO_EMAIL"]
PWD = os.environ["ALUNO_PASSWORD"]
ALVO = "Construindo times"  # substring do nome


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        # Tenta várias rotas de "Meus Cursos"
        rotas = [
            "dashboard_students/courses",
            "aprender",
            "aprender/courses",
            "meus_cursos",
            "courses",
            "dashboard_students",
        ]
        for r in rotas:
            page.goto(BASE + r, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(4000)
            html = page.content()
            if ALVO.lower() in html.lower():
                print(f"\n*** Achei '{ALVO}' em {page.url} ***")
                # Tira screenshot
                slug = r.replace("/", "_") or "root"
                png = f"/tmp/find-{slug}.png"
                page.screenshot(path=png, full_page=True)
                print(f"Screenshot: {png}")

                # Lista todos os links que tenham o texto ou estejam perto dele
                hits = page.eval_on_selector_all(
                    "a",
                    "els => els.map(e => ({href: e.getAttribute('href'), text: (e.innerText||'').trim()})).filter(x => x.href && x.text)"
                )
                relevantes = [h for h in hits if ALVO.lower() in (h["text"] or "").lower()]
                print(f"\nLinks com texto '{ALVO}' ({len(relevantes)}):")
                for h in relevantes[:10]:
                    print(f"  href={h['href']!r}")
                    print(f"  text={h['text'][:120]!r}\n")

                # Pega quaisquer IDs numéricos em hrefs próximos
                vizinhos = page.eval_on_selector_all(
                    "*",
                    """els => {
                        const out = [];
                        for (const el of els) {
                            if ((el.innerText || '').includes('Construindo times')) {
                                // sobe até achar um <a>
                                let cur = el;
                                for (let i = 0; i < 6 && cur; i++) {
                                    if (cur.tagName === 'A' && cur.href) {
                                        out.push({href: cur.getAttribute('href'), text: (el.innerText||'').slice(0,80)});
                                        break;
                                    }
                                    // ou procura <a> filho
                                    const a = cur.querySelector('a[href]');
                                    if (a) {
                                        out.push({href: a.getAttribute('href'), text: (el.innerText||'').slice(0,80)});
                                        break;
                                    }
                                    cur = cur.parentElement;
                                }
                            }
                        }
                        return out;
                    }"""
                )
                print(f"\nHrefs vizinhos ao texto ({len(vizinhos)}):")
                for v in vizinhos[:10]:
                    print(f"  href={v['href']!r}  text={v['text']!r}")
                browser.close()
                return

        print(f"Não achei '{ALVO}' em nenhuma rota tentada.")
        browser.close()


if __name__ == "__main__":
    main()
