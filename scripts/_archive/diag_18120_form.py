"""diag_18120_form.py — inspeciona o form de Registro externo: inputs file,
o que habilita o botao 'Preencher com IA', e a area de upload de evidencia."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

EVID = tw.ROOT / "evidencias" / "ia_registros_18120"
CERT = EVID / "certificado_teste.png"


def main():
    c = tw.cfg("GOATWY")
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        tw.login(page, c)
        page.goto(f"{c['base_url']}/o/{c['org_id']}/records/new",
                  wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)

        # inventario dos inputs file e proximidade com labels
        info = page.evaluate(
            r"""() => {
                const inputs = Array.from(document.querySelectorAll('input[type=file]'));
                return inputs.map((i,idx)=>{
                    // sobe ate achar texto de contexto
                    let ctx='';
                    let n=i;
                    for(let k=0;k<6 && n;k++){ n=n.parentElement; if(n){const t=(n.innerText||'').replace(/\s+/g,' ').trim(); if(t.length>ctx.length) ctx=t;} }
                    return {idx, accept:i.getAttribute('accept'), name:i.getAttribute('name'),
                            id:i.id, testid:i.getAttribute('data-test-id'),
                            ctx: ctx.slice(0,160)};
                });
            }"""
        )
        print("=== INPUTS FILE ===")
        for it in info:
            print(it)

        btn = page.evaluate(
            r"""() => {
                const b=document.querySelector('[data-test-id="records-form-ai-autofill-button"]');
                if(!b) return null;
                return {disabled:b.disabled, text:(b.innerText||'').trim()};
            }"""
        )
        print("=== BOTAO IA (antes upload) ===", btn)

        # tenta upload no input com accept de docs/imagens (evidencia), nao no Website
        idx_evid = 0
        for it in info:
            acc = (it.get("accept") or "").lower()
            if any(x in acc for x in ["pdf", "png", "jpg", "csv", "doc", "image"]):
                idx_evid = it["idx"]
                break
        print(f"=== usando input file idx={idx_evid} para evidencia ===")
        page.locator("input[type=file]").nth(idx_evid).set_input_files(str(CERT))
        page.wait_for_timeout(4000)
        tw.snap(page, EVID, "diag_pos_upload", full=True)

        btn2 = page.evaluate(
            r"""() => {
                const b=document.querySelector('[data-test-id="records-form-ai-autofill-button"]');
                if(!b) return null;
                return {disabled:b.disabled, text:(b.innerText||'').trim()};
            }"""
        )
        print("=== BOTAO IA (apos upload evidencia) ===", btn2)

        # tambem testa: e se preencher Website habilita?
        # acha input de website (placeholder)
        web = page.evaluate(
            r"""() => {
                const ins=Array.from(document.querySelectorAll('input'));
                const w=ins.find(i=>{const ph=(i.placeholder||'').toLowerCase();return ph.includes('exemplo.com')||ph.includes('http');});
                return w?{placeholder:w.placeholder,id:w.id,name:w.name}:null;
            }"""
        )
        print("=== INPUT WEBSITE ===", web)

        page.wait_for_timeout(2000)
        ctx.close(); browser.close()


if __name__ == "__main__":
    main()
