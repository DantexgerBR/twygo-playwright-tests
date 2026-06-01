"""Explora a área /admin pra achar a rota correta da atividade 2868819."""
import os
import re
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"]
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
ATIV_ID = os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Login
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("networkidle", timeout=20000)

        page.goto(BASE + "admin", wait_until="networkidle", timeout=30000)
        print("URL:", page.url, "| title:", page.title())
        page.screenshot(path="/tmp/twygo-admin.png", full_page=True)

        # Lista links com texto sobre cursos, atividades, conteudos
        for needle in ["Cursos", "Atividade", "Conteúdo", "Vídeo", "Trilhas"]:
            links = page.get_by_role("link", name=re.compile(needle, re.I)).all()
            print(f"\nlinks com '{needle}': {len(links)}")
            for lk in links[:6]:
                try:
                    txt = lk.inner_text()
                    href = lk.get_attribute("href")
                    print(f"  txt={txt[:50]!r} href={href!r}")
                except:
                    pass

        # Procura por todos os links que contenham um ID numérico grande (provável curso/atividade)
        all_hrefs = page.eval_on_selector_all(
            "a", "els => els.map(e => e.getAttribute('href')).filter(Boolean)"
        )
        ids = set()
        for h in all_hrefs:
            for m in re.findall(r"/(\d{6,8})", h):
                ids.add(m)
        print(f"\nIDs numéricos vistos em links: {sorted(ids)[:30]}")

        # Procura "cursos" no menu
        for href in all_hrefs:
            if "curso" in href.lower() or "content" in href.lower() or "activit" in href.lower():
                print(f"  → {href}")

        browser.close()


if __name__ == "__main__":
    main()
