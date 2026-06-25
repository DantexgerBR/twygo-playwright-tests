"""Descobre a URL real da tela Registros e o perfil do usuário lider@teste.com."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
from dotenv import load_dotenv

load_dotenv(tw.ROOT / ".env")
c = {
    "base_url": os.environ["REGISTROSF2_BASE_URL"].rstrip("/"),
    "org_id": os.environ["REGISTROSF2_ORG_ID"],
    "email": os.environ["REGISTROSF2_ADMIN_EMAIL"],
    "senha": os.environ["REGISTROSF2_ADMIN_PASSWORD"],
}

SLUG = "registros-f2-qa116"
BASE = tw.ROOT / "evidencias" / SLUG
BASE.mkdir(parents=True, exist_ok=True)

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    # Login admin
    tw.login(page, c, admin=True)

    # Tentar clicar na sidebar via JS scroll + force
    print("Tentando clicar em 'Registros' na sidebar via JS...")
    try:
        registros_link = page.locator("a", has_text="Registros").filter(has_not_text="Compartilhamento").first
        registros_link.scroll_into_view_if_needed(timeout=5000)
        page.wait_for_timeout(500)
        registros_link.click(force=True, timeout=5000)
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)
        print(f"URL após clicar Registros: {page.url}")
        tw.snap(page, BASE, "discover_registros_url")
    except Exception as e:
        print(f"Erro ao clicar: {e}")
        # Tentar via evaluate para pegar o href
        links = page.evaluate("""
            () => Array.from(document.querySelectorAll('a')).filter(a => /registros/i.test(a.textContent)).map(a => ({text: a.textContent.trim(), href: a.href}))
        """)
        print(f"Links com 'Registros': {links}")

    # Tentar URLs alternativas
    print("\nTestando URLs...")
    urls_tentar = [
        f"{c['base_url']}/o/{c['org_id']}/learning_records",
        f"{c['base_url']}/o/{c['org_id']}/registros",
        f"{c['base_url']}/o/{c['org_id']}/records",
        f"{c['base_url']}/o/{c['org_id']}/aprendizagem/registros",
        f"{c['base_url']}/o/{c['org_id']}/learning/records",
        f"{c['base_url']}/o/{c['org_id']}/training_records",
        f"{c['base_url']}/o/{c['org_id']}/external_records",
        f"{c['base_url']}/o/{c['org_id']}/trainings",
    ]

    for url in urls_tentar:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(1500)
            body = page.locator("body").inner_text()
            is_404 = "doesn't exist" in body or "not found" in body.lower() or "404" in page.url
            print(f"  {url.split('/')[-1]:25s} → {'404' if is_404 else 'OK: ' + page.url}")
            if not is_404:
                tw.snap(page, BASE, f"url_ok_{url.split('/')[-1]}")
                break
        except Exception as ex:
            print(f"  {url.split('/')[-1]:25s} → ERRO: {ex}")

    # Após encontrar a URL, verificar perfil do líder
    print("\nVerificando usuário lider (qalider@teste.com)...")
    page.goto(f"{c['base_url']}/o/{c['org_id']}/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Buscar o usuário líder via search
    try:
        search = page.locator("input[placeholder*='Pesquise'], input[type='search']").first
        if search.count():
            search.fill("qalider")
            page.wait_for_timeout(2000)
    except Exception:
        pass

    tw.snap(page, BASE, "discover_lider_usuario")

    lider_row = page.locator("tbody tr").filter(has_text="qalider").first
    if lider_row.count():
        info = lider_row.inner_text()
        print(f"Linha do líder: {info[:300]}")

    # Ver URL de edição do líder para identificar perfis
    try:
        lider_link = page.locator("a", has_text="lider").first
        href = lider_link.get_attribute("href")
        print(f"Link do líder: {href}")
        if href:
            page.goto(f"{c['base_url']}{href}" if href.startswith('/') else href,
                      wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)
            tw.snap(page, BASE, "discover_lider_perfil")
            print(f"URL perfil líder: {page.url}")
            # Verificar texto na página de perfil
            texto = page.locator("body").inner_text()
            if "gestor" in texto.lower() or "turma" in texto.lower() or "team" in texto.lower():
                print("  Confirmado: possui perfil Gestor de turma")
            print(f"  Preview: {texto[:500]}")
    except Exception as e:
        print(f"Erro ao verificar perfil do líder: {e}")

    ctx.close()
    browser.close()

print("\nDone.")
