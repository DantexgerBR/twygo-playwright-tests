"""TC8 - clicar checkbox do card por coordenada e verificar borda."""
import os, sys
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
    page.on("dialog", lambda d: d.accept())

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
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    # Ativar modo grid clicando no ícone (primeira coordenada: grid icon)
    page.mouse.click(1295, 382)
    page.wait_for_timeout(2000)

    # Verificar qual elemento está em modo "ativo" (grid selecionado)
    toggle_state = page.evaluate("""
        () => {
            // Procurar o ícone ativo (primeiro dos dois toggle buttons)
            const allElements = document.querySelectorAll('[class*="active"], [aria-pressed="true"], [data-active]');
            return Array.from(allElements).map(e => ({tag: e.tagName, class: e.className.substring(0,60), text: e.textContent.trim().substring(0,20)}));
        }
    """)
    print(f"Elementos ativos: {toggle_state[:5]}")

    # Verificar o DOM dos cards para encontrar o seletor correto
    card_structure = page.evaluate("""
        () => {
            // Encontrar o container dos cards (grid)
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            const result = [];
            let count = 0;
            for (const cb of checkboxes) {
                if (count >= 3) break;
                // Subir para o container do card
                let el = cb.parentElement;
                for (let i = 0; i < 8; i++) {
                    if (!el) break;
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 200 && rect.height > 80) {
                        result.push({
                            level: i,
                            class: el.className.substring(0,60),
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            w: Math.round(rect.width),
                            h: Math.round(rect.height)
                        });
                        break;
                    }
                    el = el.parentElement;
                }
                count++;
            }
            return result;
        }
    """)
    print(f"Estrutura dos cards: {card_structure[:3]}")

    # Localizar checkboxes por ALL inputs (não só em [class*=card])
    all_inputs = page.locator("input[type='checkbox']")
    print(f"Total checkboxes: {all_inputs.count()}")

    # Pegar bbox do primeiro checkbox que não seja header
    # Header checkbox tem y baixo (perto da toolbar)
    cbs_info = []
    for i in range(min(all_inputs.count(), 5)):
        cb = all_inputs.nth(i)
        bb = cb.bounding_box()
        if bb:
            cbs_info.append({"i": i, "x": round(bb["x"]), "y": round(bb["y"])})
    print(f"Checkboxes bboxes: {cbs_info}")

    tw.snap(page, EVID, "tc8coord_01_grid")

    # Clicar no segundo checkbox (primeiro da lista de cards, pular o "Selecionar todos")
    # Com base no card_structure: primeiro card em y~440, x~259
    if card_structure and len(card_structure) > 0:
        card1 = card_structure[0]
        # Checkbox fica no canto superior direito do card: x = card.right - 15, y = card.y + 15
        cb_x = card1["x"] + card1["w"] - 15
        cb_y = card1["y"] + 15
        print(f"Clicando checkbox no card1 em ({cb_x}, {cb_y})")
        page.mouse.click(cb_x, cb_y)
        page.wait_for_timeout(800)
        tw.snap(page, EVID, "tc8coord_02_card_selecionado")

        # Verificar borda do card
        borda = page.evaluate(f"""
            () => {{
                // Pegar card container por coordenada aproximada
                const el = document.elementFromPoint({card1['x'] + card1['w']//2}, {card1['y'] + card1['h']//2});
                if (!el) return 'null';
                let container = el;
                for (let i = 0; i < 8; i++) {{
                    if (!container) break;
                    const style = window.getComputedStyle(container);
                    const rect = container.getBoundingClientRect();
                    if (rect.width > 200 && rect.height > 80) {{
                        return {{
                            class: container.className.substring(0,80),
                            border: style.border.substring(0,80),
                            borderColor: style.borderColor.substring(0,60),
                            boxShadow: style.boxShadow.substring(0,80)
                        }};
                    }}
                    container = container.parentElement;
                }}
                return 'container_nao_encontrado';
            }}
        """)
        print(f"Borda do card: {borda}")

    ctx.close()
    browser.close()
