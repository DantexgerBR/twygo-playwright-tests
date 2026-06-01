"""Mapa completo do admin Twygo (stage).

Loga, navega pra perfil admin, coleta TODOS os links visíveis da sidebar e
visita cada um, capturando: texto, URL, título da página e screenshot.

Saída:
    docs/mapa-admin-twygo.md       — markdown human-readable
    docs/mapa-admin-twygo.json     — dump bruto
    docs/mapa-admin-twygo/*.png    — screenshot de cada menu visitado

AVISO: A Twygo invalida sessões concorrentes. NÃO logue no Twygo manualmente
enquanto este script roda.

Como rodar:
    .\\.venv\\Scripts\\python.exe scripts/mapa_admin_twygo.py
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BASE_URL = (os.environ.get("BASE_URL", "") or "").rstrip("/")
ORG_ID = os.environ.get("ORG_ID", "")
EMAIL = os.environ.get("ADMIN_EMAIL", "")
PWD = os.environ.get("ADMIN_PASSWORD", "")

OUT_DIR = ROOT / "docs"
SHOT_DIR = OUT_DIR / "mapa-admin-twygo"
OUT_DIR.mkdir(exist_ok=True)
SHOT_DIR.mkdir(exist_ok=True)

SLUG = re.compile(r"[^a-z0-9]+")


def slugify(s: str) -> str:
    return SLUG.sub("-", s.lower()).strip("-")[:60] or "item"


def coletar_sidebar(page):
    """Coleta links visíveis da sidebar (ou doc inteiro como fallback)."""
    return page.evaluate(
        """() => {
            const candidatos = [
                'aside', 'nav.sidebar', '.sidebar', '#sidebar',
                '.menu-lateral', '[class*="sidebar"]', '[class*="Sidebar"]'
            ];
            let scope = null;
            for (const c of candidatos) {
                const el = document.querySelector(c);
                if (el && el.offsetParent) { scope = el; break; }
            }
            scope = scope || document;
            const seen = new Set();
            const out = [];
            scope.querySelectorAll('a').forEach(a => {
                const text = (a.innerText || '').trim();
                const href = a.href || '';
                const key = text + '|' + href;
                if (!text || !href || href.endsWith('#')) return;
                if (a.offsetParent === null) return;
                if (seen.has(key)) return;
                seen.add(key);
                out.push({ text, href });
            });
            return out;
        }"""
    )


def expandir_menus(page):
    """Abre submenus colapsados (best-effort)."""
    try:
        page.evaluate(
            """() => {
                document.querySelectorAll('[aria-expanded="false"]').forEach(el => {
                    try { el.click(); } catch(e) {}
                });
            }"""
        )
        page.wait_for_timeout(800)
    except Exception:
        pass


def main() -> None:
    if not (BASE_URL and ORG_ID and EMAIL and PWD):
        raise SystemExit("Faltam vars no .env: BASE_URL, ORG_ID, ADMIN_EMAIL, ADMIN_PASSWORD")

    print(f"BASE_URL={BASE_URL}")
    print(f"ORG_ID={ORG_ID}")
    print(f"Saidas em: {OUT_DIR}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        ctx = browser.new_context(
            viewport={"width": 1366, "height": 900},
            locale="pt-BR",
        )
        page = ctx.new_page()

        print("[1] Login...")
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
        page.fill("#user_email", EMAIL)
        page.fill("#user_password", PWD)
        page.click("#user_submit")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        print(f"   pos-login: {page.url}")

        print("[2] Mudando para admin...")
        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        print(f"   url admin: {page.url}")
        if "/users/login" in page.url:
            print("FAIL sessao invalidada (login concorrente). Saindo.")
            ctx.close()
            browser.close()
            return

        print("[3] Expandindo submenus colapsados...")
        expandir_menus(page)
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT_DIR / "mapa-admin-sidebar-completa.png"), full_page=True)

        print("[4] Coletando links da sidebar...")
        itens = coletar_sidebar(page)
        print(f"   {len(itens)} itens encontrados")

        resultados = []
        for i, it in enumerate(itens, start=1):
            slug = slugify(it["text"])
            print(f"   [{i:02d}/{len(itens)}] {it['text'][:42]:<42} -> {it['href']}")
            entry = {
                "ordem": i,
                "texto": it["text"],
                "href": it["href"],
                "path": it["href"].replace(BASE_URL, ""),
            }
            try:
                page.goto(it["href"], wait_until="domcontentloaded", timeout=15000)
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass
                page.wait_for_timeout(600)
                if "/users/login" in page.url:
                    entry["erro"] = "sessao invalidada (parada de coleta)"
                    resultados.append(entry)
                    print("       sessao invalidada, parando")
                    break
                entry["titulo"] = page.title()
                entry["url_final"] = page.url
                shot_rel = f"mapa-admin-twygo/{i:02d}-{slug}.png"
                page.screenshot(path=str(OUT_DIR / shot_rel), full_page=False)
                entry["screenshot"] = shot_rel
            except Exception as e:
                entry["erro"] = f"{type(e).__name__}: {str(e)[:120]}"
            resultados.append(entry)

        (OUT_DIR / "mapa-admin-twygo.json").write_text(
            json.dumps(resultados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        md = [
            "# Mapa do admin Twygo (stage)",
            "",
            f"- **BASE_URL**: `{BASE_URL}`",
            f"- **ORG_ID**: `{ORG_ID}`",
            f"- **Itens coletados**: {len(resultados)}",
            "",
            "## Sidebar — perfil admin",
            "",
        ]
        for r in resultados:
            md.append(f"### {r['ordem']:02d}. {r['texto']}")
            md.append("")
            md.append(f"- **Path**: `{r['path']}`")
            if "erro" in r:
                md.append(f"- **Erro ao visitar**: {r['erro']}")
            else:
                md.append(f"- **Título**: {r.get('titulo','')}")
                md.append(f"- **URL final**: `{r.get('url_final','').replace(BASE_URL,'')}`")
                md.append(f"- **Screenshot**: `{r.get('screenshot','')}`")
            md.append("")
        (OUT_DIR / "mapa-admin-twygo.md").write_text("\n".join(md), encoding="utf-8")

        print()
        print("[FIM] Saidas:")
        print(f"  {OUT_DIR/'mapa-admin-twygo.md'}")
        print(f"  {OUT_DIR/'mapa-admin-twygo.json'}")
        print(f"  {SHOT_DIR}/")

        page.wait_for_timeout(1500)
        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
