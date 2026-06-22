"""Retrabalho 19851 — Líder de equipe não consegue adicionar ações.

Bug: líder abre 'Ações de resposta' na análise individual de um liderado, clica
'Adicionar' e o drawer abre mas 'Função vinculada' e 'Iniciativa' vêm vazios.

Esperado: drawer lista opções em 'Função vinculada' e 'Iniciativa'.

Env: testedemigracao / org 19653 (perfil MIGR no .env).
Login: qalider19851@teste.com / 123456 (líder de equipe).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "lider_acoes_19851"

c = tw.cfg("MIGR")
c["email"] = "qalider19851@teste.com"
c["senha"] = "123456"


def dump_nav(page, titulo):
    print(f"\n===== {titulo} =====")
    print("URL:", page.url)
    links = page.evaluate(
        "()=>Array.from(document.querySelectorAll('a,button,[role=menuitem],[role=tab]'))"
        ".map(e=>(e.innerText||e.getAttribute('aria-label')||'').replace(/\\s+/g,' ').trim())"
        ".filter(t=>t.length>0&&t.length<60)"
    )
    seen = []
    for t in links:
        if t not in seen:
            seen.append(t)
    for t in seen[:120]:
        print("  •", t)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    # login SEM switch admin — líder é perfil de usuário
    page.goto(f"{c['base_url']}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", c["email"])
    page.fill("#user_password", c["senha"])
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    print("Pós-login URL:", page.url)
    tw.snap(page, PASTA, "01-pos-login")
    dump_nav(page, "LANDING")

    # --- mapear hrefs do menu ---
    hrefs = page.evaluate(
        "()=>Array.from(document.querySelectorAll('a[href]'))"
        ".map(a=>({t:(a.innerText||'').replace(/\\s+/g,' ').trim(),h:a.getAttribute('href')}))"
        ".filter(x=>x.t.length>0&&x.t.length<40)"
    )
    print("\n--- HREFS ---")
    vistos = set()
    for x in hrefs:
        key = x["t"] + x["h"]
        if key not in vistos:
            vistos.add(key)
            print(f"  {x['t']!r} -> {x['h']}")

    # --- Equipe (análise dos liderados) ---
    eq = page.evaluate(
        "()=>{const a=Array.from(document.querySelectorAll('a[href]'))"
        ".find(a=>/Equipe/i.test(a.innerText||''));return a?a.getAttribute('href'):'';}"
    )
    print("\nEquipe href:", eq)
    if eq:
        page.goto(c["base_url"] + eq if eq.startswith("/") else eq, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    print("\nEquipe URL:", page.url)
    tw.snap(page, PASTA, "02-equipe", full=True)

    # HTML da última célula da linha (onde estão os ícones de ação)
    row_html = page.evaluate(
        "()=>{const tr=document.querySelector('tbody tr');if(!tr)return 'sem tr';"
        "const tds=tr.querySelectorAll('td');const last=tds[tds.length-1];"
        "return last?last.innerHTML:'sem td';}"
    )
    print("\n--- HTML ULTIMA CELULA ---\n", row_html[:2000])

    # clicar no ícone "monitoring" (análise individual)
    page.locator('[data-icon="monitoring"]').first.click(force=True)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    print("\nAnálise individual URL:", page.url)
    tw.snap(page, PASTA, "03-analise-individual", full=True)

    # data-icons de ações em cada linha
    icons = page.evaluate(
        "()=>Array.from(document.querySelectorAll('tbody tr [data-icon]'))"
        ".map(e=>({ic:e.getAttribute('data-icon'),id:e.closest('[id]')?e.closest('[id]').id:''}))"
    )
    print("\n--- DATA-ICONS NAS LINHAS ---")
    for x in icons:
        print(f"  {x['ic']}  (id={x['id']})")

    # procurar QUALQUER coisa com 'ação'/'resposta'/'iniciativa' no DOM inteiro
    achados = page.evaluate(
        "()=>Array.from(document.querySelectorAll('*'))"
        ".filter(e=>e.children.length===0&&/a(ç|c)(ã|a)o|resposta|iniciativa|fun(ç|c)(ã|a)o vinculada/i.test(e.innerText||''))"
        ".map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).slice(0,30)"
    )
    print("\n--- TEXTOS c/ ação/resposta/iniciativa ---")
    for t in achados:
        print("  •", t)

    ctx.close()
    browser.close()
