import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
import _twygo as tw

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True, slow_mo=100)
    c = tw.cfg("")
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/787696/edit?tab=identification",
              wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    achado = page.evaluate(
        """() => {
            const hits = [...document.querySelectorAll('label, p, span, h2, h3, div')]
              .filter(el => el.getBoundingClientRect().width > 0 && el.children.length < 3)
              .map(el => (el.textContent || '').trim())
              .filter(t => /idioma|language/i.test(t));
            const sections = [...document.querySelectorAll('h2,h3')]
              .filter(el => el.getBoundingClientRect().width > 0)
              .map(el => (el.textContent || '').trim()).filter(Boolean);
            return { hits: [...new Set(hits)].slice(0, 5), sections };
        }"""
    )
    print("36675 edit Identificacao — mencoes a Idioma:", achado["hits"])
    print("36675 sections:", achado["sections"])
    tw.snap(page, tw.ROOT / "evidencias" / "novo_estudio_baseline_trilha_pacote", "12-identificacao-36675")
    ctx.close(); browser.close()
