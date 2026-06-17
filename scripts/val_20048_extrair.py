import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "competencias_20048"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/succession_people_analysis", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4500)
    tw.dispensar_nps(page)
    page.locator("#data-export-button").click(force=True)
    page.wait_for_timeout(2500)
    tw.snap(page, PASTA, "EXTRAIR-modal")
    print("URL:", page.url)
    ctx.close(); browser.close()
