"""TC8 Final - clicar no checkbox do card e verificar borda."""
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

    # Ativar modo grid
    page.mouse.click(1295, 382)
    page.wait_for_timeout(2000)
    tw.snap(page, EVID, "tc8final_01_grid")

    # Pegar TODOS os checkboxes (input type=checkbox) e seus pais containers (card)
    cbs_data = page.evaluate("""
        () => {
            const results = [];
            const inputs = document.querySelectorAll('input[type="checkbox"]');
            for (const inp of inputs) {
                const bb = inp.getBoundingClientRect();
                if (bb.width === 0) continue;
                // Encontrar o container do card: subir até achar div com width > 200 e height > 80
                let container = inp.parentElement;
                for (let i = 0; i < 10; i++) {
                    if (!container) break;
                    const cbb = container.getBoundingClientRect();
                    // Card tem ~300px width e ~120px height
                    if (cbb.width > 200 && cbb.height > 80 && cbb.width < 600) {
                        results.push({
                            cb_x: Math.round(bb.x),
                            cb_y: Math.round(bb.y),
                            card_x: Math.round(cbb.x),
                            card_y: Math.round(cbb.y),
                            card_w: Math.round(cbb.width),
                            card_h: Math.round(cbb.height),
                            card_class: container.className.substring(0, 80)
                        });
                        break;
                    }
                    container = container.parentElement;
                }
            }
            return results;
        }
    """)
    print(f"Checkboxes com containers: {len(cbs_data)}")
    for d in cbs_data[:4]:
        print(f"  cb=({d['cb_x']},{d['cb_y']}) card=({d['card_x']},{d['card_y']}) {d['card_w']}x{d['card_h']} class='{d['card_class'][:40]}'")

    if cbs_data:
        # Clicar no checkbox do primeiro card
        first_cb = cbs_data[0]
        page.mouse.click(first_cb["cb_x"] + 8, first_cb["cb_y"] + 8)
        page.wait_for_timeout(800)
        tw.snap(page, EVID, "tc8final_02_card_marcado")

        # Verificar borda do card container
        card_x = first_cb["card_x"] + first_cb["card_w"] // 2
        card_y = first_cb["card_y"] + first_cb["card_h"] // 2
        borda = page.evaluate(f"""
            () => {{
                const el = document.elementFromPoint({card_x}, {card_y});
                if (!el) return 'null';
                let container = el;
                for (let i = 0; i < 10; i++) {{
                    if (!container) break;
                    const rect = container.getBoundingClientRect();
                    if (rect.width > 200 && rect.width < 600 && rect.height > 80) {{
                        const style = window.getComputedStyle(container);
                        return {{
                            class: container.className.substring(0,80),
                            border: style.border.substring(0,80),
                            borderColor: style.borderColor,
                            boxShadow: style.boxShadow.substring(0,100),
                            outline: style.outline
                        }};
                    }}
                    container = container.parentElement;
                }}
                return 'container_nao_encontrado';
            }}
        """)
        print(f"Borda card: {borda}")

        # Verificar cor da borda — roxo Twygo é #7c3aed = rgb(124, 58, 237)
        if isinstance(borda, dict):
            border_str = str(borda.get("border", "")) + str(borda.get("borderColor", "")) + str(borda.get("boxShadow", ""))
            print(f"String total de borda: {border_str}")
            has_purple = any(x in border_str.lower() for x in ["7c3aed", "124, 58, 237", "purple", "violet", "58, 237"])
            print(f"Borda roxa detectada: {has_purple}")
        else:
            print(f"Borda não detectada corretamente: {borda}")

        # Desmarcar
        page.mouse.click(first_cb["cb_x"] + 8, first_cb["cb_y"] + 8)
        page.wait_for_timeout(500)
        tw.snap(page, EVID, "tc8final_03_card_desmarcado")
    else:
        print("Nenhum checkbox com container encontrado")
        tw.snap(page, EVID, "tc8final_sem_cb")

    ctx.close()
    browser.close()
