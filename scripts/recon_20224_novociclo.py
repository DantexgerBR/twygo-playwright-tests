"""Recon 20224 v3: marcar Avaliacao de Desempenho -> revelar modelo + quem responde; ver Etapas."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/new", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    page.get_by_placeholder("Ex.: Ciclo Anual 2026").fill("QA 20224 autoavaliacao")
    d = page.locator("input[type=date]")
    d.nth(0).fill("2026-06-19"); d.nth(1).fill("2026-12-31")

    page.get_by_role("tab", name=re.compile("Avaliações", re.I)).first.click(timeout=4000)
    page.wait_for_timeout(1500)
    # marcar "Avaliacao de Desempenho" pelo card (data-test-id)
    page.locator('[data-test-id="cycle-form-evaluation-card-performance"]').first.click(timeout=4000)
    page.wait_for_timeout(2000)
    tw.snap(page, PASTA, "05-desempenho-marcado", full=True)
    info = page.evaluate(r"""()=>{
        const vis=el=>el.offsetParent!==null;
        const sel=Array.from(document.querySelectorAll('select,[role=combobox],input,[role=radio],[role=switch]')).filter(vis).map(e=>(e.getAttribute('aria-label')||e.placeholder||e.type||e.tagName||'').trim()).filter(Boolean);
        const txt=(document.body.innerText||'').replace(/\n{2,}/g,'\n');
        const i=txt.search(/Quem responde|modelo|Modelo/);
        return {sel:[...new Set(sel)].slice(0,25), snippet:i>=0?txt.slice(Math.max(0,i-40),i+500):''};
    }""")
    print("CONTROLES apos marcar Desempenho:", info["sel"])
    print("SNIPPET:", info["snippet"])

    # aba Etapas
    page.get_by_role("tab", name=re.compile("Etapas", re.I)).first.click(timeout=4000)
    page.wait_for_timeout(2000)
    tw.snap(page, PASTA, "06-etapas", full=True)
    et = page.evaluate(r"""()=>{const t=(document.body.innerText||'').replace(/\n{2,}/g,'\n');const i=t.search(/Etapas|participante|liderado|Quem/i);return i>=0?t.slice(i,i+600):t.slice(0,400);}""")
    print("ETAPAS texto:", et)

    ctx.close(); browser.close()
print("OK")
