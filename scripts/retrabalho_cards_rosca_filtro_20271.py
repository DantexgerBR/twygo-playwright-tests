"""
Retrabalho 20271 — Cards com grafico de rosca na visao Admin reagem a filtros incorretamente.

RN 31 (principal): Os cards/donut NAO devem mudar ao aplicar o drawer de filtros da lista.
RN 30 (complementar): Cards devem responder a hover (cursor pointer + animacao) e a clique
       (estado selected/dimmed + filtra a lista abaixo).

INSTRUCOES DE EXECUCAO:
    .venv\Scripts\python.exe scripts\retrabalho_cards_rosca_filtro_20271.py

Evidencias em: evidencias/cards_rosca_filtro_20271/
"""
import os
import sys
import json
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

BASE_URL = c["base_url"]
ORG_ID = c["org_id"]
RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records"

SLUG = "cards_rosca_filtro_20271"
BASE = tw.ROOT / "evidencias" / SLUG
BASE.mkdir(parents=True, exist_ok=True)

print(f"[CONFIG] base_url={BASE_URL} | org_id={ORG_ID} | email={c['email']}")
print(f"[CONFIG] evidencias em: {BASE}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login_admin(page):
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", c["email"])
    page.fill("#user_password", c["senha"])
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded", timeout=30000,
    )
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    print(f"[LOGIN] url apos switch admin: {page.url}")


def ir_records(page):
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector("tbody tr", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)


def ler_cards(page) -> dict:
    """
    Extrai numeros dos 4 cards de rosca (Emitidos/Expirados/Pendentes/Recusados).
    Os cards tem classe css-rdwj84 (inner) dentro de css-11n7in3 (container).
    Retorna {label: valor} e raw list.
    """
    return page.evaluate(r"""
        () => {
            const cards = {};
            const raw = [];

            // Abordagem direta: cards com classe css-rdwj84
            const cardEls = Array.from(document.querySelectorAll('.css-rdwj84'));
            cardEls.forEach(el => {
                const txt = (el.innerText || '').replace(/\s+/g, ' ').trim();
                // Texto esperado: "293 Emitidos" ou "15 Expirados" etc.
                const m = txt.match(/^(\d+)\s+([A-Za-zÀ-ɏ]+)$/);
                if (m) {
                    cards[m[2]] = parseInt(m[1], 10);
                    raw.push(txt);
                }
            });

            // Fallback: numeros folha com label
            if (!Object.keys(cards).length) {
                const allLeafs = Array.from(document.querySelectorAll('*')).filter(el => {
                    if (!el.offsetParent || el.children.length > 0) return false;
                    const t = (el.innerText || '').trim();
                    return /^\d+$/.test(t);
                });
                allLeafs.forEach(el => {
                    const val = parseInt((el.innerText || '').trim(), 10);
                    if (isNaN(val) || val > 99999) return;
                    let anc = el.parentElement;
                    let label = '';
                    for (let i = 0; i < 8 && anc; i++) {
                        const t = (anc.innerText || '').replace(/\s+/g, ' ').trim();
                        const semNum = t.replace(val.toString(), '').replace(/\s+/g, ' ').trim();
                        if (semNum.length >= 3 && semNum.length <= 40 &&
                            /[A-Za-zÀ-ɏ]/.test(semNum) &&
                            !semNum.includes('chevron') && !semNum.includes('keyboard') &&
                            !semNum.includes('leaderboard') && !semNum.includes('format_') &&
                            !semNum.includes('school') && !semNum.includes('Dashboard')) {
                            label = semNum;
                            break;
                        }
                        anc = anc.parentElement;
                    }
                    if (label) {
                        cards[label] = val;
                        raw.push(`${val} ${label}`);
                    }
                });
            }

            return {structured: cards, raw: [...new Set(raw)].slice(0, 10)};
        }
    """)


def ler_lista(page) -> dict:
    """Conta linhas visíveis e informacoes de paginacao."""
    return page.evaluate(r"""
        () => {
            const linhas = document.querySelectorAll('tbody tr').length;
            const body = document.body.innerText || '';
            const btnNums = Array.from(document.querySelectorAll('button'))
                .filter(b => /^\d+$/.test((b.innerText || '').trim()))
                .map(b => parseInt(b.innerText.trim(), 10))
                .filter(n => n > 0 && n < 1000);
            const vazio = body.includes('dados para exibir') || body.includes('Nao ha dados');
            // Termo de pesquisa ativo
            const searchInput = document.querySelector('input[placeholder*="Pesquise" i], input[type="search"]');
            const searchVal = searchInput ? searchInput.value : '';
            return {
                linhas_dom: linhas,
                pag_btns: btnNums,
                vazio,
                search_ativo: searchVal,
            };
        }
    """)


def capturar_estilos_hover_completo(page, locator) -> dict:
    """
    Captura estilos computados completos ANTES e DEPOIS do hover.
    Inclui cursor, transform, boxShadow, border, background, outline, opacity.
    Tambem usa elementFromPoint para cursor real na posicao do card.
    """
    # Posicao do card
    box = locator.bounding_box()
    if not box:
        return {}

    cx = box['x'] + box['width'] / 2
    cy = box['y'] + box['height'] / 2

    # Estilos ANTES (sem hover)
    estilos_antes = locator.evaluate(r"""
        el => {
            const st = window.getComputedStyle(el);
            return {
                cursor: st.cursor,
                transform: st.transform,
                boxShadow: st.boxShadow,
                border: st.border,
                borderColor: st.borderColor,
                backgroundColor: st.backgroundColor,
                outline: st.outline,
                opacity: st.opacity,
            };
        }
    """)

    # Hover
    page.mouse.move(cx, cy)
    page.wait_for_timeout(800)

    # Estilos DEPOIS (com hover)
    estilos_depois = locator.evaluate(r"""
        el => {
            const st = window.getComputedStyle(el);
            return {
                cursor: st.cursor,
                transform: st.transform,
                boxShadow: st.boxShadow,
                border: st.border,
                borderColor: st.borderColor,
                backgroundColor: st.backgroundColor,
                outline: st.outline,
                opacity: st.opacity,
            };
        }
    """)

    # Cursor do elemento MAIS INTERNO na posicao do mouse (elementFromPoint)
    cursor_elemento_real = page.evaluate(r"""
        ([cx, cy]) => {
            const el = document.elementFromPoint(cx, cy);
            if (!el) return {cursor: null, tag: null, class: null};
            const st = window.getComputedStyle(el);
            return {
                cursor: st.cursor,
                tag: el.tagName,
                class: el.className.substring(0, 60),
                text: (el.innerText || '').trim().substring(0, 30),
            };
        }
    """, [cx, cy])

    # Diferencas
    diffs = {k: (estilos_antes.get(k), estilos_depois.get(k))
             for k in estilos_antes
             if estilos_antes.get(k) != estilos_depois.get(k)}

    return {
        "antes": estilos_antes,
        "depois": estilos_depois,
        "diffs": diffs,
        "cursor_elemento_real": cursor_elemento_real,
        "pos": {"cx": cx, "cy": cy},
    }


# ---------------------------------------------------------------------------
# EXECUCAO PRINCIPAL
# ---------------------------------------------------------------------------
with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=False, slow_mo=500)

    # -----------------------------------------------------------------------
    # FASE 0: Login + visao admin
    # -----------------------------------------------------------------------
    print("\n" + "="*60)
    print("FASE 0: Login e confirmacao de perfil admin")
    print("="*60)
    login_admin(page)
    ir_records(page)

    perfil_info = page.evaluate(r"""
        () => {
            const btns = Array.from(document.querySelectorAll('button'));
            const bPerfil = btns.find(b => /gestor|administrador|colaborador|l[ií]der/i.test(b.innerText || ''));
            return {
                url: window.location.href,
                perfil_btn: bPerfil ? bPerfil.innerText.trim() : null,
            };
        }
    """)
    print(f"[PERFIL] {json.dumps(perfil_info, ensure_ascii=False)}")
    perfil_detectado = perfil_info.get("perfil_btn") or "?"

    # Confirmar os 4 cards presentes
    cards_mapa = page.evaluate(r"""
        () => {
            return Array.from(document.querySelectorAll('.css-rdwj84')).map(el => ({
                text: (el.innerText || '').replace(/\s+/g, ' ').trim(),
                cursor: window.getComputedStyle(el).cursor,
                rect: `${Math.round(el.getBoundingClientRect().width)}x${Math.round(el.getBoundingClientRect().height)}`,
            }));
        }
    """)
    print(f"[CARDS] Cards encontrados: {json.dumps(cards_mapa, ensure_ascii=False)}")

    # -----------------------------------------------------------------------
    # FASE 2: RN 31 — BASELINE
    # -----------------------------------------------------------------------
    print("\n" + "="*60)
    print("FASE 2: RN31 — Captura BASELINE (sem filtro)")
    print("="*60)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)

    cards_antes = ler_cards(page)
    lista_antes = ler_lista(page)

    print(f"[RN31-ANTES] Numeros cards: {json.dumps(cards_antes['structured'], ensure_ascii=False)}")
    print(f"[RN31-ANTES] Lista: linhas={lista_antes['linhas_dom']} | pag_btns={lista_antes['pag_btns']}")

    tw.snap(page, BASE, "01-cards-sem-filtro")
    page.screenshot(path=str(BASE / "01-cards-sem-filtro-full.png"), full_page=True)
    print("[snap] 01-cards-sem-filtro.png")

    # -----------------------------------------------------------------------
    # FASE 3: Aplicar filtro que REDUZA a lista (mas nao zere)
    # Estrategia: ler o nome/email da primeira linha da tabela e usar como termo
    # -----------------------------------------------------------------------
    print("\n" + "="*60)
    print("FASE 3: Aplicar filtro no campo de pesquisa")
    print("="*60)

    # Descobrir termos reais na tabela para pesquisa valida
    nomes_tabela = page.evaluate(r"""
        () => {
            const rows = Array.from(document.querySelectorAll('tbody tr')).slice(0, 5);
            return rows.map(r => {
                const cells = Array.from(r.querySelectorAll('td'));
                // Primeira celula tende a ser o nome/conteudo
                return cells.slice(0, 3).map(c => (c.innerText || '').trim().substring(0, 40));
            });
        }
    """)
    print(f"[FILTRO] Primeiras 5 linhas da tabela: {json.dumps(nomes_tabela, ensure_ascii=False)}")

    # Usar o nome da 1a linha (1a celula) como termo de pesquisa
    termo_pesquisa = ""
    if nomes_tabela and nomes_tabela[0]:
        # Pegar 1a celula da 1a linha — deve ser um nome/titulo especifico
        termo_pesquisa = nomes_tabela[0][0] if nomes_tabela[0][0] else ""
        # Se muito curto ou vazio, tentar 2a celula
        if len(termo_pesquisa) < 3 and len(nomes_tabela[0]) > 1:
            termo_pesquisa = nomes_tabela[0][1]

    if not termo_pesquisa:
        # Fallback: usar "Richard" (nome comum em dados de teste)
        termo_pesquisa = "Richard"

    print(f"[FILTRO] Termo escolhido para pesquisa: '{termo_pesquisa}'")

    search_input = page.locator('input[placeholder*="Pesquise" i], input[type="search"]').first
    if search_input.count() and search_input.is_visible():
        search_input.clear()
        search_input.fill(termo_pesquisa)
        page.wait_for_timeout(2500)
        filtro_desc = f"pesquisa='{termo_pesquisa}'"
        print(f"[FILTRO] Campo de pesquisa preenchido com '{termo_pesquisa}'")
    else:
        filtro_desc = "sem_filtro"
        print("[FILTRO] AVISO: campo de pesquisa nao encontrado")

    # -----------------------------------------------------------------------
    # FASE 4: RN 31 — Captura DEPOIS do filtro
    # -----------------------------------------------------------------------
    print("\n" + "="*60)
    print("FASE 4: RN31 — Captura DEPOIS do filtro")
    print("="*60)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)

    cards_depois = ler_cards(page)
    lista_depois = ler_lista(page)

    print(f"[RN31-DEPOIS] Numeros cards: {json.dumps(cards_depois['structured'], ensure_ascii=False)}")
    print(f"[RN31-DEPOIS] Lista: linhas={lista_depois['linhas_dom']} | vazio={lista_depois['vazio']} | search='{lista_depois['search_ativo']}'")

    tw.snap(page, BASE, "02-cards-com-filtro")
    page.screenshot(path=str(BASE / "02-cards-com-filtro-full.png"), full_page=True)
    print("[snap] 02-cards-com-filtro.png")

    lista_encolheu = lista_depois["linhas_dom"] < lista_antes["linhas_dom"] or lista_depois["vazio"]
    cards_struct_mudaram = cards_antes["structured"] != cards_depois["structured"]

    print(f"\n[RN31-ANALISE]")
    print(f"  Filtro: {filtro_desc}")
    print(f"  Lista: {lista_antes['linhas_dom']} -> {lista_depois['linhas_dom']} linhas DOM")
    print(f"  Lista encolheu: {lista_encolheu}")
    print(f"  Numeros ANTES : {cards_antes['structured']}")
    print(f"  Numeros DEPOIS: {cards_depois['structured']}")
    print(f"  Cards mudaram: {cards_struct_mudaram}")
    if not lista_encolheu:
        print("  AVISO: lista nao encolheu — filtro possivelmente no-op!")

    # -----------------------------------------------------------------------
    # FASE 5: RN 30 — Hover e Click (reload limpo)
    # -----------------------------------------------------------------------
    print("\n" + "="*60)
    print("FASE 5: RN30 — Hover e Click nos cards (estado limpo)")
    print("="*60)

    ir_records(page)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)

    # Usar o card "Expirados" (15 — segundo menor, indice 1)
    # Corresponde a .css-rdwj84:nth-of-type(2) ou o segundo elemento .css-rdwj84
    card_loc = page.locator(".css-rdwj84").nth(1)  # Expirados
    card_texto = (card_loc.inner_text() or "").replace("\n", " ").strip()
    print(f"[RN30] Card selecionado: '{card_texto}'")

    # Container pai do card (o que tem classe css-11n7in3)
    card_container = page.locator(".css-11n7in3").nth(1)

    rn30 = {
        "card_testado": card_texto,
        "hover_estilos": {},
        "cursor_elemento_real": {},
        "lista_antes_click": None,
        "lista_depois_click": None,
        "click_mudou_lista": None,
        "card_classes_apos_click": None,
        "todos_cards_apos_click": [],
    }

    try:
        # ---- HOVER: capturar estilos completos (antes e depois) ----
        print("[RN30] Capturando estilos de hover (antes e depois)...")
        hover_data = capturar_estilos_hover_completo(page, card_loc)
        rn30["hover_estilos"] = hover_data

        print(f"[RN30] Estilos ANTES do hover: {json.dumps(hover_data.get('antes', {}), ensure_ascii=False)}")
        print(f"[RN30] Estilos DEPOIS do hover: {json.dumps(hover_data.get('depois', {}), ensure_ascii=False)}")
        print(f"[RN30] DIFERENCAS no hover: {json.dumps(hover_data.get('diffs', {}), ensure_ascii=False)}")
        print(f"[RN30] Cursor do elemento real (elementFromPoint): {json.dumps(hover_data.get('cursor_elemento_real', {}), ensure_ascii=False)}")

        tw.snap(page, BASE, "03-hover")

        # ---- CLICK ----
        lista_antes_click = ler_lista(page)
        rn30["lista_antes_click"] = lista_antes_click

        card_loc.click()
        page.wait_for_timeout(2500)

        # Classes do card clicado
        classes_card = card_loc.evaluate("el => el.className")
        rn30["card_classes_apos_click"] = classes_card

        # Estado de todos os cards apos click
        todos_cards = page.evaluate(r"""
            () => {
                return Array.from(document.querySelectorAll('.css-rdwj84, .css-11n7in3')).map(e => ({
                    text: (e.innerText || '').replace(/\s+/g, ' ').trim().substring(0, 40),
                    class: e.className.substring(0, 80),
                    opacity: window.getComputedStyle(e).opacity,
                    cursor: window.getComputedStyle(e).cursor,
                    backgroundColor: window.getComputedStyle(e).backgroundColor,
                    borderColor: window.getComputedStyle(e).borderColor,
                }));
            }
        """)
        rn30["todos_cards_apos_click"] = todos_cards
        print(f"[RN30] Classes card '{card_texto}' apos click: {classes_card[:80]}")
        print(f"[RN30] Todos os cards apos click:")
        for c_item in todos_cards:
            print(f"  '{c_item['text'][:30]}' opacity={c_item['opacity']} cursor={c_item['cursor']} bg={c_item['backgroundColor']}")

        lista_depois_click = ler_lista(page)
        rn30["lista_depois_click"] = lista_depois_click
        rn30["click_mudou_lista"] = lista_antes_click["linhas_dom"] != lista_depois_click["linhas_dom"]

        print(f"[RN30] Lista antes click: {lista_antes_click['linhas_dom']} linhas")
        print(f"[RN30] Lista depois click: {lista_depois_click['linhas_dom']} linhas")
        print(f"[RN30] Click mudou a lista: {rn30['click_mudou_lista']}")

        tw.snap(page, BASE, "04-click")

    except Exception as e:
        print(f"[RN30] Erro: {e}")
        tw.snap(page, BASE, "03-hover")
        tw.snap(page, BASE, "04-click")

    ctx.close()
    browser.close()

# ---------------------------------------------------------------------------
# RESUMO FINAL
# ---------------------------------------------------------------------------
print("\n" + "="*60)
print("RESUMO FINAL — Fatos observados (veredito a ser determinado pelo QA Lead)")
print("="*60)

print("\n=== VISAO ===")
print(f"  Perfil detectado: {perfil_detectado}")
print(f"  Email logado: {c['email']}")
print(f"  URL Records: {RECORDS_URL}")
print(f"  Cards identificados: {json.dumps(cards_mapa, ensure_ascii=False)}")

print("\n=== RN 31 (cards reagem a filtros?) ===")
print(f"  Filtro aplicado: {filtro_desc}")
print(f"  Lista antes filtro: {lista_antes['linhas_dom']} linhas DOM | pag_btns={lista_antes['pag_btns']}")
print(f"  Lista depois filtro: {lista_depois['linhas_dom']} linhas DOM | search='{lista_depois['search_ativo']}'")
print(f"  Lista encolheu: {lista_encolheu}")
print(f"  NUMEROS ANTES : {json.dumps(cards_antes['structured'], ensure_ascii=False)}")
print(f"  NUMEROS DEPOIS: {json.dumps(cards_depois['structured'], ensure_ascii=False)}")
print(f"  Cards mudaram: {cards_struct_mudaram}")

print("\n=== RN 30 (hover e click nos cards?) ===")
print(f"  Card testado: '{rn30['card_testado']}'")
hover = rn30.get("hover_estilos", {})
print(f"  cursor antes hover: {hover.get('antes', {}).get('cursor')}")
print(f"  cursor depois hover: {hover.get('depois', {}).get('cursor')}")
print(f"  cursor elemento real (elementFromPoint): {json.dumps(hover.get('cursor_elemento_real', {}), ensure_ascii=False)}")
print(f"  Diferencas de estilo no hover: {json.dumps(hover.get('diffs', {}), ensure_ascii=False)}")
print(f"  Classes card apos click: {(rn30.get('card_classes_apos_click') or '')[:80]}")
print(f"  Lista antes click: {rn30.get('lista_antes_click', {}).get('linhas_dom')} linhas")
print(f"  Lista depois click: {rn30.get('lista_depois_click', {}).get('linhas_dom')} linhas")
print(f"  Click mudou a lista: {rn30.get('click_mudou_lista')}")

print("\n=== EVIDENCIAS GERADAS ===")
for f in sorted(BASE.glob("*.png")):
    print(f"  {f}")
print()
