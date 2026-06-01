"""Retrabalho 19638 — [Recertificação] Botao 'Iniciar reinscricao' nao aparece em
todos participantes na lista de Aprendizagem.

Esperado: na lista de participantes (Aprendizagem) de um conteudo com reinscricao
habilitada, o item 'Iniciar reinscricao' deve aparecer no kebab de TODOS os
participantes — habilitado p/ quem cumpre criterio (100% progresso, aprovado ou
inscricao expirada), bloqueado (aria-disabled) + tooltip com motivo p/ quem nao cumpre.

Env: eduapi (org 36912) — credenciais no .env (perfil EDUAPI). Ver .env.example.

Uso: python scripts/retrabalho_19638_botao_reinscricao.py ["Nome do curso"]
(default: primeiro curso da lista)
"""
import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

import _twygo as tw
_c = tw.cfg("EDUAPI")
BASE_URL, ORG_ID, EMAIL, SENHA = _c["base_url"], _c["org_id"], _c["email"], _c["senha"]

NOME_CURSO = sys.argv[1] if len(sys.argv) > 1 else "Construindo times de alta performance"

PASTA = ROOT / "evidencias" / "19638_botao_reinscricao"
PASTA.mkdir(parents=True, exist_ok=True)


def snap(page, nome):
    p = PASTA / f"{nome}.png"
    page.screenshot(path=str(p), full_page=False)
    print(f"   [snap] {p.name}")
    return p


def dispensar_nps(page):
    for sel in ["button:has-text('Pergunte depois')", "[aria-label='Close']", ".chakra-modal__close-btn"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible():
                b.click(timeout=2000)
                page.wait_for_timeout(700)
        except Exception:
            pass


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=350)
    context = browser.new_context(viewport={"width": 1500, "height": 950}, locale="pt-BR")
    page = context.new_page()

    # --- Login + admin ---
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", EMAIL)
    page.fill("#user_password", SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    dispensar_nps(page)
    print(f"[admin] {page.url}")

    # --- Clicar no nome do curso p/ abrir edit e pegar o id da URL ---
    print(f"[curso] alvo = {NOME_CURSO!r}")
    import re as _re
    cid = ""
    try:
        page.get_by_text(NOME_CURSO, exact=False).first.click(timeout=8000)
        page.wait_for_timeout(4000)
        dispensar_nps(page)
        m = _re.search(r"/(?:contents|e)/(\d+)", page.url)
        if m:
            cid = m.group(1)
    except Exception as e:
        print(f"   click nome falhou: {repr(e)[:120]}")
    print(f"   url={page.url}  content id = {cid!r}")
    if not cid:
        print("FALHA: nao consegui o id do curso")
        snap(page, "00-sem-id")
        sys.exit(1)

    # --- Conferir switch 'Habilitar reinscricao' na aba Acesso ---
    page.goto(f"{BASE_URL}/o/{ORG_ID}/contents/{cid}/edit?tab=access",
              wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=12000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    dispensar_nps(page)
    switch = page.evaluate(
        """() => {
            const inp = document.querySelector('#has_recertification, input[name="has_recertification"]');
            if (!inp) return {existe:false};
            return {existe:true, checked: inp.checked,
                    ariaChecked: inp.getAttribute('aria-checked')};
        }""")
    print(f"[switch reinscricao] {switch}")
    snap(page, "01-acesso-switch-reinscricao")

    if not switch.get("existe"):
        print("!!! Switch 'Habilitar reinscricao' NAO existe neste conteudo/org.")
        print("    Flag recertification pode nao estar actored na 36912.")

    # --- Ir pra Aprendizagem (learning) ---
    page.goto(f"{BASE_URL}/e/{cid}/learning", wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(4000)
    dispensar_nps(page)
    print(f"[learning] {page.url}")
    snap(page, "02-lista-aprendizagem")

    # --- Extrair participantes em ordem do DOM (nome, email, progresso, aprovacao, situacao) ---
    participantes = page.evaluate(
        r"""() => {
            const out = [];
            const rows = Array.from(document.querySelectorAll('tr'));
            rows.forEach(r => {
                const txt = (r.innerText||'');
                if (!/@/.test(txt)) return;  // so linhas de participante
                const email = (txt.match(/[\w.\-]+@[\w.\-]+/)||[''])[0];
                const prog = (txt.match(/(\d+)%/)||['',''])[1];
                // aprovacao: input switch/checkbox no row
                const apInp = r.querySelector('input[type=checkbox], .chakra-switch input');
                const aprovado = apInp ? apInp.checked : null;
                out.push({email, prog, aprovado, resumo: txt.replace(/\n+/g,' | ').slice(0,160)});
            });
            return out;
        }""")
    print(f"[participantes] {len(participantes)}:")
    for i, pa in enumerate(participantes):
        print(f"   [{i}] {pa['email']} prog={pa['prog']}% aprovado={pa['aprovado']}")
    (PASTA / "_participantes.txt").write_text(
        "\n".join(f"[{i}] {pa['resumo']}" for i, pa in enumerate(participantes)), encoding="utf-8")

    # --- Iterar kebab de cada participante ---
    kebabs = page.locator("table button:has-text('more_vert'), tbody button:has-text('more_vert')")
    n = kebabs.count()
    print(f"[kebabs] {n} botoes more_vert na tabela")

    resultados = []
    for i in range(n):
        info = {"idx": i, "participante": participantes[i] if i < len(participantes) else None}
        email_i = (participantes[i]["email"] if i < len(participantes) else f"p{i}").split("@")[0]
        try:
            kb = kebabs.nth(i)
            kb.scroll_into_view_if_needed(timeout=4000)
            kb.click(timeout=5000, force=True)
            page.wait_for_timeout(1500)
            # rolar o menuitem de reinscricao (icone replay) pra dentro da view
            rein_item = page.locator("[role=menu] [role=menuitem]").filter(
                has=page.locator("[data-icon='replay']")).last
            if rein_item.count():
                rein_item.scroll_into_view_if_needed(timeout=4000)
                page.wait_for_timeout(800)
        except Exception as e:
            info["erro"] = f"kebab click: {repr(e)[:100]}"
            resultados.append(info)
            continue

        # ler itens do menu aberto (texto + aria-label + outerHTML do item de reinscricao)
        menu = page.evaluate(
            r"""() => {
                const lists = Array.from(document.querySelectorAll('[role=menu]'))
                    .filter(m => m.offsetParent !== null);
                const m = lists[lists.length-1];
                if (!m) return {itens:[], reinscricao:null};
                const els = Array.from(m.querySelectorAll('[role=menuitem]'));
                const itens = els.map(it => ({
                    txt: (it.innerText||it.textContent||'').replace(/\s+/g,' ').trim(),
                    aria: it.getAttribute('aria-label') || '',
                    ariaDisabled: it.getAttribute('aria-disabled'),
                    disabledProp: it.disabled === true,
                    dataIcon: (it.querySelector('[data-icon]')||{}).getAttribute ? it.querySelector('[data-icon]').getAttribute('data-icon') : '',
                }));
                // item de reinscricao = o que tem icone 'replay' ou texto reinscri
                const rein = itens.find(x => /reinscri/i.test(x.txt) || /reinscri/i.test(x.aria) || x.dataIcon === 'replay');
                let reinHTML = '';
                if (rein) {
                    const el = els.find(it => {
                        const di = it.querySelector('[data-icon]');
                        return /reinscri/i.test(it.innerText||'') || (di && di.getAttribute('data-icon')==='replay');
                    });
                    if (el) reinHTML = el.outerHTML.slice(0,300);
                }
                return {itens, reinscricao: rein||null, reinHTML};
            }""")
        info["itens_menu"] = [x["txt"] or x["dataIcon"] for x in menu["itens"]]
        info["reinscricao"] = menu["reinscricao"]
        info["reinHTML"] = menu.get("reinHTML", "")
        print(f"   [{i}] {info['participante']['email'] if info['participante'] else '?'} -> "
              f"reinscricao={menu['reinscricao']}")

        # screenshot do menu aberto de TODOS
        snap(page, f"03-kebab-{i}-{email_i}")

        # se achou item de reinscricao, hover p/ capturar tooltip (esp. se bloqueado)
        rein = menu["reinscricao"]
        if rein:
            try:
                # localizar o menuitem com icone replay
                item = page.locator("[role=menu] [role=menuitem]").filter(
                    has=page.locator("[data-icon='replay']")).first
                if item.count() == 0:
                    item = page.locator("[role=menu] [role=menuitem]", has_text="reinscri").first
                item.hover(timeout=3000, force=True)
                page.wait_for_timeout(1500)
                tip = page.evaluate(
                    """() => Array.from(document.querySelectorAll('[role=tooltip], .chakra-tooltip'))
                        .filter(e => e.offsetParent !== null)
                        .map(e => (e.innerText||'').trim()).filter(Boolean)""")
                info["tooltip"] = tip
                if tip:
                    snap(page, f"03-kebab-{i}-{email_i}-tooltip")
                print(f"        bloqueado={rein.get('ariaDisabled')} tooltip={tip}")
            except Exception as e:
                info["tooltip_erro"] = repr(e)[:100]

        resultados.append(info)
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)

    # --- Salvar relatorio ---
    (PASTA / "_relatorio_kebabs.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Resumo ---
    print("\n===== RESUMO =====")
    print(f"Switch reinscricao no conteudo {cid}: {switch}")
    com = [r for r in resultados if r.get("reinscricao")]
    sem = [r for r in resultados if not r.get("reinscricao") and "erro" not in r]
    hab = [r for r in com if not (r["reinscricao"].get("ariaDisabled") == "true" or r["reinscricao"].get("disabledProp"))]
    blo = [r for r in com if (r["reinscricao"].get("ariaDisabled") == "true" or r["reinscricao"].get("disabledProp"))]
    print(f"Participantes com item 'reinscricao' no kebab: {len(com)}/{len(resultados)}")
    print(f"  habilitados: {len(hab)} | bloqueados(c/ aria-disabled): {len(blo)}")
    print(f"  SEM o item no kebab: {len(sem)} -> {[r['participante']['email'] if r['participante'] else '?' for r in sem]}")

    page.wait_for_timeout(1500)
    print("\n[FIM] veja evidencias/19638_botao_reinscricao/")
    context.close()
    browser.close()
