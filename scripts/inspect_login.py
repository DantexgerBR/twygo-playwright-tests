"""Discovery aprofundado: rota e estrutura do login Twygo."""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE_URL = os.environ["BASE_URL"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(BASE_URL + "login", wait_until="networkidle", timeout=30000)
        print("URL final:", page.url)
        print("title:", page.title())

        # Salva screenshot e HTML pra inspeção
        page.screenshot(path="/tmp/twygo-login.png", full_page=True)
        html = page.content()
        with open("/tmp/twygo-login.html", "w") as f:
            f.write(html)
        print("Screenshot: /tmp/twygo-login.png")
        print("HTML:       /tmp/twygo-login.html")

        # Lista iframes
        frames = page.frames
        print(f"\nFrames: {len(frames)}")
        for fr in frames:
            print(f"  - name={fr.name!r} url={fr.url!r}")

        # Lista todos os inputs com type=email/password
        for selector in ['input[type="email"]', 'input[type="password"]', 'input[name*="login"]', 'input[name*="email"]']:
            elems = page.locator(selector).all()
            print(f"\n{selector} → {len(elems)} elementos")
            for el in elems[:5]:
                print(f"  id={el.get_attribute('id')!r} name={el.get_attribute('name')!r} placeholder={el.get_attribute('placeholder')!r}")

        # Lista links com texto sugestivo de login
        for needle in ["Entrar", "Login", "Acessar", "Acesso"]:
            links = page.get_by_role("link", name=needle).all()
            print(f"\nlinks '{needle}' → {len(links)}")
            for lk in links[:5]:
                href = lk.get_attribute("href")
                print(f"  href={href!r}")

        browser.close()


if __name__ == "__main__":
    main()
