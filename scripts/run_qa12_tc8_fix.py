"""TC8 isolado — testar toggle grid + borda roxa na seleção de card."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID   = os.environ.get("REGISTROSF2_ORG_ID", "37079")
ADMIN_EMAIL    = os.environ.get("REGISTROSF2_ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("REGISTROSF2_ADMIN_PASSWORD", "")

RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa12"
EVID.mkdir(parents=True, exist_ok=True)

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    page.on("dialog", lambda d: (print(f"[dialog] {d.type}"), d.accept()))

    # Login + switch
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Ir para records
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    tw.snap(page, EVID, "tc8fix_01_inicial", full=True)

    # Localizar todos os botões com coordenadas
    print("\n=== Todos os botões com bbox ===")
    all_btns_info = []
    for b in page.locator("button").all():
        try:
            t = b.inner_text().strip()[:25]
            bb = b.bounding_box()
            if bb:
                all_btns_info.append({"text": t, "x": round(bb["x"]), "y": round(bb["y"]), "w": round(bb["width"]), "h": round(bb["height"])})
        except Exception:
            pass

    for info in all_btns_info:
        print(f"  x={info['x']:4d} y={info['y']:3d} w={info['w']:3d} h={info['h']:2d} | '{info['text']}'")

    # Localizar a busca e o Filtro para definir zona dos toggles
    busca_el = page.locator("input[placeholder*='Pesquise']").first
    filtro_el = page.locator("button").filter(has_text="Filtro").first
    bb_busca = busca_el.bounding_box()
    bb_filtro = filtro_el.bounding_box()
    print(f"\nbusca: x={bb_busca['x']:.0f} y={bb_busca['y']:.0f} right={bb_busca['x']+bb_busca['width']:.0f}")
    print(f"filtro: x={bb_filtro['x']:.0f} y={bb_filtro['y']:.0f}")

    # Filtrar botões na zona: x > busca_right, x < filtro_left, y similar ao filtro (+/- 30px)
    busca_right = bb_busca["x"] + bb_busca["width"]
    filtro_left = bb_filtro["x"]
    filtro_y = bb_filtro["y"]

    toggles_na_zona = []
    for info in all_btns_info:
        if (busca_right < info["x"] < filtro_left and
                abs(info["y"] - filtro_y) < 30):
            toggles_na_zona.append(info)
            print(f"  TOGGLE CANDIDATO: x={info['x']} y={info['y']} w={info['w']} h={info['h']} | '{info['text']}'")

    print(f"\nToggle candidatos na zona: {len(toggles_na_zona)}")

    if toggles_na_zona:
        # Clicar no primeiro (grid)
        toggle_target = toggles_na_zona[0]
        # Clicar por coordenadas
        page.mouse.click(toggle_target["x"] + toggle_target["w"]//2,
                         toggle_target["y"] + toggle_target["h"]//2)
        page.wait_for_timeout(2000)
        tw.snap(page, EVID, "tc8fix_02_grid_ativo", full=True)

        # Verificar se mudou para grid
        cards = page.locator("[class*='card'], [class*='Card']").count()
        rows = page.locator("table tbody tr").count()
        print(f"\nApós clique toggle: cards={cards}, rows={rows}")

        # Fechar qualquer modal com Escape
        modal = page.locator(".chakra-modal__content-container")
        if modal.count() > 0 and modal.first.is_visible():
            print("Modal aberto — Escape 2x")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
            try:
                page.wait_for_selector(".chakra-modal__content-container", state="hidden", timeout=5000)
            except Exception:
                pass
            tw.snap(page, EVID, "tc8fix_03_modal_fechado")

        # Se clicou em algo errado (abriu modal de Extrair), clicar no segundo toggle
        modal2 = page.locator(".chakra-modal__content-container")
        if len(toggles_na_zona) > 1 and (modal2.count() > 0 or cards == 0):
            toggle_target2 = toggles_na_zona[1]
            page.mouse.click(toggle_target2["x"] + toggle_target2["w"]//2,
                             toggle_target2["y"] + toggle_target2["h"]//2)
            page.wait_for_timeout(2000)
            tw.snap(page, EVID, "tc8fix_04_toggle2", full=True)
            cards = page.locator("[class*='card'], [class*='Card']").count()
            rows = page.locator("table tbody tr").count()
            print(f"Após clique toggle2: cards={cards}, rows={rows}")

        # Tentar clicar no checkbox de um card/linha
        page.wait_for_timeout(1000)
        chk = page.locator(".chakra-checkbox__control")
        if chk.count() > 1:
            chk.nth(1).click(timeout=5000)  # pular o header
            page.wait_for_timeout(500)
            tw.snap(page, EVID, "tc8fix_05_card_selecionado", full=True)

            # Verificar borda do container selecionado
            borda = page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input[type="checkbox"]:checked');
                    for (const inp of inputs) {
                        // Subir para encontrar container com border
                        let el = inp.parentElement;
                        for (let i = 0; i < 10; i++) {
                            if (!el) break;
                            const style = window.getComputedStyle(el);
                            const border = style.border || style.borderColor || style.outline || style.boxShadow;
                            if (border && (border.includes('7c3aed') || border.includes('124, 58') ||
                                          border.includes('purple') || border.includes('violet') ||
                                          (border.includes('rgb') && border.includes('(')))) {
                                return {el: el.className.substring(0,50), border: border.substring(0,100)};
                            }
                            el = el.parentElement;
                        }
                    }
                    return null;
                }
            """)
            print(f"Borda roxa detectada: {borda}")
        else:
            print("Sem checkboxes para clicar em grid")
    else:
        print("Nenhum toggle encontrado na zona da toolbar")
        tw.snap(page, EVID, "tc8fix_sem_toggle")

    ctx.close()
    browser.close()
