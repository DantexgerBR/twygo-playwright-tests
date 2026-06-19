"""Diag 33085519 lider: campanha 193 ativou? situacao dos times do ciclo 178? lider do dante?"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "desempenho_seguir_33085519"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    # campanha 193 status
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/178/campaigns", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    rows = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/Campanha QA lider|Programada|andamento|Ativa/i.test(t))""")
    print("CAMPANHA 193:", rows)
    tw.snap(page, PASTA, "11-campanha193-status")

    # Situacao dos times do ciclo (admin) - ha avaliacoes geradas?
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles?profile=admin", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    try:
        page.get_by_text("Status dos times", exact=False).first.click(timeout=4000); page.wait_for_timeout(2500)
        tw.snap(page, PASTA, "12-status-dos-times", full=True)
        st = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/Dante|Adriana|lider|Inici|Conclu|andamento/i.test(t)).slice(0,15)""")
        print("STATUS TIMES:", st)
    except Exception as ex:
        print("erro status times:", str(ex)[:80])

    # lider direto do dante.tavares (Usuarios > ver detalhes)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/users?profile=admin", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    page.get_by_placeholder(re.compile("Pesquise", re.I)).first.fill("dante.tavares"); page.wait_for_timeout(2000)
    rowd = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/dante\.tavares/i.test(t))""")
    print("LINHA DANTE:", rowd)
    ctx.close(); browser.close()
print("OK")
