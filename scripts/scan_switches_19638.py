"""Scan: estado do switch 'Habilitar reinscrição' (aba Acesso) de cada conteúdo da
org EDUAPI. Acha o(s) conteúdo(s) com reinscrição ON pra validar o card 19638.
Usa os helpers de scripts/_twygo.py.
"""
import json

import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "19638_botao_reinscricao"


def main():
    c = tw.cfg("EDUAPI")
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, slow_mo=120)
        tw.login(page, c)  # loga + troca pra admin (events?profile=admin)
        page.wait_for_timeout(1000)

        itens = page.evaluate(
            "()=>Array.from(document.querySelectorAll('tr[data-item-id]')).map(r=>({"
            "id:r.getAttribute('data-item-id'),nome:r.getAttribute('data-item-name'),"
            "tipo:(r.querySelector('td p.chakra-text')||{}).innerText||''}))"
        )
        print(f"[itens] {len(itens)} conteúdos")

        resultados = []
        for it in itens:
            cid = it["id"]
            try:
                page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=access",
                          wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(1800)
                sw = page.evaluate(
                    "()=>{const i=document.querySelector('#has_recertification,input[name=\"has_recertification\"]');"
                    "return i?{existe:true,checked:i.checked}:{existe:false};}")
            except Exception as e:
                sw = {"erro": repr(e)[:80]}
            on = sw.get("existe") and sw.get("checked")
            print(f"   {cid}  reinscricao={sw}  {it['nome'][:40]}{'  <<< ON' if on else ''}")
            resultados.append({**it, "switch": sw, "on": bool(on)})

        PASTA.mkdir(parents=True, exist_ok=True)
        (PASTA / "_scan_switches.json").write_text(
            json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
        ons = [r for r in resultados if r["on"]]
        print(f"\n===== {len(ons)} conteúdo(s) com reinscrição ON =====")
        for r in ons:
            print(f"   {r['id']}  {r['nome']}")

        ctx.close(); browser.close()


if __name__ == "__main__":
    main()
