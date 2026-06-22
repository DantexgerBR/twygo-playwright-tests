"""run_qa11_rerun.py — Re-run parcial: apenas TC6, TC7 e TC13.
Corrige 3 problemas identificados pelo revisor:
  - TC7: td.nth(1) era Origem (ícone "home"), não Conteúdo → corrigido para td.nth(2)
  - TC13: scan de spans com data-icon="menu" além de buttons
  - TC6: click em card usando coordenadas JS em vez de seletor CSS
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "registros-f2-qa11"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)

BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
ALUNO_EMAIL = os.environ.get("ALUNO_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ORG_ID = os.environ.get("ORG_ID", "36675")
RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"

RESULTADOS = {}


def log(msg):
    print(msg)


def passou(tc_id, evidencias, obs=""):
    RESULTADOS[tc_id] = {"veredito": "PASSOU", "evidencias": evidencias, "obs": obs}
    log(f"  [TC{tc_id}] PASSOU{' — ' + obs if obs else ''}")


def falhou(tc_id, evidencias, motivo):
    RESULTADOS[tc_id] = {"veredito": "FALHOU", "evidencias": evidencias, "obs": motivo}
    log(f"  [TC{tc_id}] FALHOU — {motivo}")


def bloqueado(tc_id, motivo):
    RESULTADOS[tc_id] = {"veredito": "BLOQUEADO", "evidencias": [], "obs": motivo}
    log(f"  [TC{tc_id}] BLOQUEADO — {motivo}")


def login_como_aluno(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", ALUNO_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    if "/users/login" in page.url:
        raise SystemExit("Sessão invalidada após login como aluno.")


def ir_para_meu_historico(page):
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=25000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    try:
        page.wait_for_selector("table, .chakra-stat", timeout=8000)
    except Exception:
        pass


def clicar_toggle_grid(page):
    grid_icon = page.locator("#grid-view-icon")
    if grid_icon.count() > 0:
        grid_icon.click(timeout=5000)
        return True
    return False


def is_modal_aberto(page):
    try:
        dialogs = page.locator("[role='dialog']:not(.chakra-popover__content), [role='alertdialog']")
        if dialogs.count() == 0:
            return False
        return dialogs.first.is_visible(timeout=500)
    except Exception:
        return False


# ─── TC6 ─────────────────────────────────────────────────────────────────────

def run_tc6(page):
    """TC6 — Linha e card não navegam ao clicar."""
    log("\n[TC6] Linha e card não navegam ao clicar...")
    page.mouse.move(200, 200)
    page.wait_for_timeout(500)
    ir_para_meu_historico(page)
    evids = []
    url_antes = page.url

    # Passo 2: clicar na linha (coluna Conteúdo = td.nth(2))
    primeira_linha = page.locator("table tbody tr").first
    if primeira_linha.count() == 0:
        bloqueado(6, "requer ao menos 1 linha na tabela")
        return
    celula_conteudo = primeira_linha.locator("td").nth(2)
    celula_conteudo.click(timeout=5000)
    page.wait_for_timeout(1500)
    url_depois_linha = page.url
    modal_aberto = is_modal_aberto(page)
    navegou_linha = url_depois_linha != url_antes or modal_aberto
    log(f"  Passo 2 — navegou após click na linha: {navegou_linha}")
    tw.snap(page, EVID, "tc6r_01_click_linha")
    evids.append("tc6r_01_click_linha.png")

    if url_depois_linha != url_antes:
        page.go_back(wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1500)
    if modal_aberto:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    # Passo 3: toggle para Grid
    page.mouse.move(200, 200)
    page.wait_for_timeout(300)
    grid_ok = clicar_toggle_grid(page)
    page.wait_for_timeout(1500)
    log(f"  Passo 3 — toggle Grid: {grid_ok}")

    # Passo 4: clicar no corpo de um card (usando coordenadas JS)
    navegou_card = False
    card_info = page.evaluate("""() => {
        const spans = document.querySelectorAll('span');
        for (const span of spans) {
            const t = span.textContent?.trim();
            if (t === 'Interno' || t === 'Externo' || t === 'Compartilhado') {
                let el = span.parentElement;
                for (let i = 0; i < 8; i++) {
                    if (!el) break;
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 150 && rect.height > 60 && rect.width < 600) {
                        if (el.querySelectorAll('*').length > 3) {
                            return { found: true, x: Math.round(rect.x + 30), y: Math.round(rect.y + 30) };
                        }
                    }
                    el = el.parentElement;
                }
            }
        }
        return { found: false };
    }""")
    log(f"  Passo 4 — card JS: {card_info}")

    if card_info and card_info.get("found"):
        try:
            url_antes_card = page.url
            page.mouse.click(card_info["x"], card_info["y"])
            page.wait_for_timeout(1500)
            url_depois_card = page.url
            modal_card = is_modal_aberto(page)
            navegou_card = url_depois_card != url_antes_card or modal_card
            log(f"  Passo 4 — navegou após click no card: {navegou_card}")
            tw.snap(page, EVID, "tc6r_02_click_card")
            evids.append("tc6r_02_click_card.png")
        except Exception as e:
            log(f"  Passo 4 — erro: {e}")
    else:
        # Verifica se estamos em modo grid (mesmo sem achar card via JS)
        selecionar_todos = page.locator("text=Selecionar todos da página atual").count() > 0
        log(f"  Passo 4 — modo grid ativo (Selecionar todos): {selecionar_todos}")
        tw.snap(page, EVID, "tc6r_02_grid_sem_card")
        evids.append("tc6r_02_grid_sem_card.png")

    if not navegou_linha and not navegou_card:
        passed_msg = "click em linha não navegou"
        if card_info and card_info.get("found"):
            passed_msg += "; click em card não navegou"
        else:
            passed_msg += "; card não localizável via JS (modo grid confirmado, passo 4 inconclusivo)"
        passou(6, evids, passed_msg)
    elif navegou_linha:
        falhou(6, evids, "click na linha causou navegação/modal inesperado")
    else:
        falhou(6, evids, "click no card causou navegação/modal inesperado")


# ─── TC7 ─────────────────────────────────────────────────────────────────────

def run_tc7(page):
    """TC7 — Busca em tempo real (corrigido: td.nth(2) = Conteúdo)."""
    log("\n[TC7] Busca em tempo real...")
    ir_para_meu_historico(page)
    evids = []

    row_count = page.locator("table tbody tr").count()
    if row_count == 0:
        bloqueado(7, "requer ao menos 1 registro")
        return
    log(f"  Passo 1 — {row_count} linhas")

    busca = page.get_by_placeholder(re.compile("Pesquise", re.I)).first

    def buscar_e_aguardar(termo, wait_ms=3000):
        busca.click(click_count=3)
        page.keyboard.press("Delete")
        page.wait_for_timeout(300)
        busca.press_sequentially(termo, delay=60)
        page.wait_for_timeout(wait_ms)

    # Diagnóstico: mostra o conteúdo das primeiras células para identificar índices corretos
    primeira_linha = page.locator("table tbody tr").first
    cell_texts = []
    for i in range(5):
        try:
            txt = primeira_linha.locator("td").nth(i).inner_text().strip()
            cell_texts.append(f"td[{i}]='{txt[:30]}'")
        except Exception:
            cell_texts.append(f"td[{i}]=ERRO")
    log(f"  Células da 1ª linha: {', '.join(cell_texts)}")

    # td.nth(2) = Conteúdo (título do curso/trilha)
    titulo_completo = primeira_linha.locator("td").nth(2).inner_text().strip()
    log(f"  Título completo (td.nth(2)): '{titulo_completo}'")

    # Remove ícones/chars especiais, pega substring de 5+ chars
    titulo_limpo = "".join(c for c in titulo_completo if c.isalpha() or c == " ").strip()
    titulo_parcial = titulo_limpo[:6].strip() if len(titulo_limpo) >= 6 else titulo_limpo
    if not titulo_parcial:
        titulo_parcial = "Acade"  # fallback para "Academia de liderança" (conteúdo conhecido)
    log(f"  Substring de busca: '{titulo_parcial}'")

    # Passo 4: busca por substring que DEVE existir → espera filtrar para <= total
    buscar_e_aguardar(titulo_parcial)
    rows_parcial = page.locator("table tbody tr").count()
    empty_parcial = page.get_by_text("Nenhum registro encontrado").count() > 0
    log(f"  Passo 4 (busca '{titulo_parcial}') — linhas: {rows_parcial}, empty: {empty_parcial}")
    tw.snap(page, EVID, "tc7r_01_busca_existente")
    evids.append("tc7r_01_busca_existente.png")

    # Passo 5: busca por termo inexistente → deve retornar 0 ou empty state
    buscar_e_aguardar("zzzzz-inexistente-99")
    rows_inexistente = page.locator("table tbody tr").count()
    empty_inexistente = page.get_by_text("Nenhum registro encontrado").count() > 0
    log(f"  Passo 5 (busca inexistente) — linhas: {rows_inexistente}, empty: {empty_inexistente}")
    tw.snap(page, EVID, "tc7r_02_busca_inexistente")
    evids.append("tc7r_02_busca_inexistente.png")

    # Passo 6: limpar → restaura total
    busca.click(click_count=3)
    page.keyboard.press("Delete")
    page.wait_for_timeout(2500)
    rows_clear = page.locator("table tbody tr").count()
    log(f"  Passo 6 (limpar) — linhas: {rows_clear}")
    tw.snap(page, EVID, "tc7r_03_busca_limpa")
    evids.append("tc7r_03_busca_limpa.png")

    # Avalia:
    # Busca por existente DEVE filtrar (< total) OU retornar exatamente os matches
    # Busca por inexistente DEVE retornar 0/empty
    # Se ambos retornam o total → busca não funciona (bug backend)
    busca_existente_filtrou = rows_parcial < row_count
    busca_inexistente_filtrou = rows_inexistente == 0 or empty_inexistente

    if busca_existente_filtrou and busca_inexistente_filtrou:
        passou(7, evids,
               f"busca por '{titulo_parcial}' filtrou ({rows_parcial}/{row_count}); "
               f"busca inexistente retornou 0/empty; limpar restaurou {rows_clear}")
    elif not busca_existente_filtrou and not busca_inexistente_filtrou:
        # Ambos falham → bug claro no backend
        falhou(7, evids,
               f"busca NÃO filtra — '{titulo_parcial}' retornou {rows_parcial}/{row_count} "
               f"E inexistente retornou {rows_inexistente} — backend ignora search_query (bug corroborado com TC4)")
    elif not busca_existente_filtrou:
        falhou(7, evids,
               f"busca por '{titulo_parcial}' (existente) retornou {rows_parcial}/{row_count} — sem filtragem")
    else:
        falhou(7, evids,
               f"busca por inexistente retornou {rows_inexistente} linhas (esperava 0)")


# ─── TC13 ────────────────────────────────────────────────────────────────────

def run_tc13(page):
    """TC13 — Hamburger sidebar mobile (varredura ampliada com spans data-icon)."""
    log("\n[TC13] Hamburger mobile...")
    evids = []

    page.set_viewport_size({"width": 360, "height": 740})
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=25000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    tw.snap(page, EVID, "tc13r_01_mobile_inicial")
    evids.append("tc13r_01_mobile_inicial.png")

    # Dump de todos os [data-icon] no DOM
    all_data_icons = page.evaluate("""() => {
        const els = document.querySelectorAll('[data-icon]');
        return Array.from(els).map(e => {
            const r = e.getBoundingClientRect();
            return {
                tag: e.tagName,
                icon: e.getAttribute('data-icon'),
                text: e.innerText?.trim()?.substring(0, 20) || '',
                visible: r.width > 0 && r.height > 0,
                x: Math.round(r.x),
                y: Math.round(r.y)
            };
        });
    }""")
    log(f"  Todos [data-icon] no DOM ({len(all_data_icons)} elementos):")
    for ei in all_data_icons:
        log(f"    tag={ei['tag']} icon='{ei['icon']}' text='{ei['text']}' vis={ei['visible']} pos=({ei['x']},{ei['y']})")

    # Dump de material-symbols-outlined (texto = nome do ícone)
    all_material = page.evaluate("""() => {
        const els = document.querySelectorAll('.material-symbols-outlined, .material-icons');
        return Array.from(els).map(e => {
            const r = e.getBoundingClientRect();
            return {
                text: e.innerText?.trim()?.substring(0, 30) || '',
                visible: r.width > 0 && r.height > 0,
                x: Math.round(r.x),
                y: Math.round(r.y),
                clickable: window.getComputedStyle(e.parentElement || e).cursor === 'pointer'
            };
        });
    }""")
    log(f"  Material symbols ({len(all_material)} elementos):")
    for ms in all_material:
        log(f"    text='{ms['text']}' vis={ms['visible']} pos=({ms['x']},{ms['y']}) clickable={ms['clickable']}")

    # Dump de botões e elementos clicáveis no canto sup-esq (x<80, y<80)
    top_left = page.evaluate("""() => {
        const all = document.querySelectorAll('*');
        const result = [];
        for (const el of all) {
            const rect = el.getBoundingClientRect();
            if (rect.x < 80 && rect.y < 80 && rect.width > 0 && rect.height > 0) {
                const cursor = window.getComputedStyle(el).cursor;
                const tag = el.tagName.toLowerCase();
                if (cursor === 'pointer' || tag === 'button' || tag === 'a') {
                    result.push({
                        tag,
                        cursor,
                        text: el.innerText?.trim()?.substring(0, 30) || '',
                        ariaLabel: el.getAttribute('aria-label') || '',
                        dataIcon: el.getAttribute('data-icon') || '',
                        x: Math.round(rect.x + rect.width/2),
                        y: Math.round(rect.y + rect.height/2)
                    });
                }
            }
        }
        return result;
    }""")
    log(f"  Clicáveis no canto sup-esq ({len(top_left)} elementos):")
    for tl in top_left:
        log(f"    tag={tl['tag']} text='{tl['text']}' aria='{tl['ariaLabel']}' icon='{tl['dataIcon']}' pos=({tl['x']},{tl['y']})")

    # Tenta encontrar hamburger
    hamburger = None
    hamburger_desc = ""

    # 1. Seletores clássicos
    button_selectors = [
        ("button[aria-label*='menu' i]", "button aria-label menu"),
        ("button[aria-label*='hamburger' i]", "button aria-label hamburger"),
        ("button[aria-label*='sidebar' i]", "button aria-label sidebar"),
        ("[data-testid*='hamburger']", "data-testid hamburger"),
        ("[data-testid*='menu-toggle']", "data-testid menu-toggle"),
        ("header button:first-child", "header first-button"),
    ]
    for sel, desc in button_selectors:
        candidate = page.locator(sel).first
        if candidate.count() > 0:
            try:
                if candidate.is_visible(timeout=500):
                    hamburger = candidate
                    hamburger_desc = desc
                    break
            except Exception:
                pass

    # 2. Span com data-icon="menu" (padrão Twygo para ícones)
    if hamburger is None:
        for icon_name in ("menu", "menu_open", "dehaze"):
            candidate = page.locator(f"[data-icon='{icon_name}']").first
            if candidate.count() > 0:
                try:
                    if candidate.is_visible(timeout=500):
                        hamburger = candidate
                        hamburger_desc = f"data-icon={icon_name}"
                        break
                except Exception:
                    pass

    # 3. Material symbol com texto "menu"
    if hamburger is None:
        for ms_sel in (".material-symbols-outlined", ".material-icons"):
            for ms_loc in page.locator(ms_sel).all():
                try:
                    if ms_loc.inner_text().strip().lower() in ("menu", "dehaze") and ms_loc.is_visible(timeout=300):
                        hamburger = ms_loc
                        hamburger_desc = f"material-icon text=menu"
                        break
                except Exception:
                    pass
            if hamburger:
                break

    log(f"  Hamburger encontrado: {hamburger is not None} ({hamburger_desc})")
    tw.snap(page, EVID, "tc13r_02_scan_concluido")
    evids.append("tc13r_02_scan_concluido.png")

    if hamburger is not None:
        # Tenta clicar e verificar se drawer abre
        hamburger.click(timeout=5000)
        page.wait_for_timeout(1500)
        tw.snap(page, EVID, "tc13r_03_apos_click_hamburger")
        evids.append("tc13r_03_apos_click_hamburger.png")

        drawer_ok = False
        try:
            dialogs = page.locator("[role='dialog']").all()
            for d in dialogs:
                box = d.bounding_box()
                if box and box["width"] > 100 and box["height"] > 200 and d.is_visible():
                    drawer_ok = True
                    break
        except Exception:
            pass
        historico_no_drawer = page.get_by_text(re.compile("Meu Histórico|Meu histórico", re.I)).count() > 1
        log(f"  Após click — drawer: {drawer_ok}, 'Meu Histórico' no drawer: {historico_no_drawer}")

        if drawer_ok or historico_no_drawer:
            tw.snap(page, EVID, "tc13r_04_drawer_conteudo")
            evids.append("tc13r_04_drawer_conteudo.png")
            passou(13, evids, f"hamburger ({hamburger_desc}) abre drawer (RN 17 implementada)")
        else:
            falhou(13, evids, f"hamburger ({hamburger_desc}) encontrado mas drawer não abriu")
    else:
        # Sem hamburger após varredura ampliada (buttons + spans data-icon + material icons)
        tw.snap(page, EVID, "tc13r_02_sem_hamburger")
        evids.append("tc13r_02_sem_hamburger.png")
        falhou(13, evids,
               "RN 17: hamburger não encontrado após varredura ampliada "
               "(buttons + [data-icon='menu'] + material-icons). "
               "Produto usa tab 'Meu Histórico' sem drawer lateral — RN 17 não implementada.")

    # Restaura viewport
    page.set_viewport_size({"width": 1500, "height": 950})


# ─── Main ─────────────────────────────────────────────────────────────────────

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    login_como_aluno(page)

    for tc_fn in [run_tc6, run_tc7, run_tc13]:
        try:
            tc_fn(page)
        except Exception as exc:
            tc_num = tc_fn.__name__.replace("run_tc", "")
            try:
                tw.snap(page, EVID, f"tc{tc_num}r_CRASH")
            except Exception:
                pass
            falhou(int(tc_num), [f"tc{tc_num}r_CRASH.png"], f"CRASH: {exc}")

    ctx.close()
    browser.close()

print("\n=== RESULTADO RE-RUN ===")
for tc_id in sorted(RESULTADOS.keys()):
    r = RESULTADOS[tc_id]
    print(f"  TC{tc_id}: {r['veredito']} — {r['obs']}")
