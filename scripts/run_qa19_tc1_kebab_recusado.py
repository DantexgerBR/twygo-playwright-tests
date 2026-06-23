"""
Encontrar o registro QAKPIRT-TC3 (Recusado na col11) e abrir seu kebab.
Esse e o id=44279851 com sit=pending na API.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
import _twygo as tw

BASE_URL   = "https://registrosf2.stage.twygoead.com"
ORG_ID     = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
LIDER_EMAIL    = "qalider@teste.com"
LIDER_PASSWORD = "123456"

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa19"
PASTA.mkdir(parents=True, exist_ok=True)

resultados = {}


def snap(page, nome, full=False):
    fp = PASTA / f"{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")


def tc_resultado(tc, veredito, resumo):
    resultados[tc] = {"veredito": veredito, "resumo": resumo}
    i = "✓" if veredito == "PASSOU" else ("✗" if veredito == "FALHOU" else "?")
    print(f"\n   [{i}] {tc}: {veredito} — {resumo}\n")


def ir_registros(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)
    tw.dispensar_nps(page)
    try:
        page.wait_for_selector("tbody tr", timeout=20000)
        page.wait_for_timeout(800)
    except Exception as e:
        print(f"   Wait failed: {e}")
    return page.locator("tbody tr").count()


def main():
    print("=== TC1/TC8 — Via linha 'Recusado' (provavelmente sit=pending) ===\n")

    c_admin = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}
    c_lider = {"base_url": BASE_URL, "org_id": None, "email": LIDER_EMAIL, "senha": LIDER_PASSWORD}

    with tw.sync_playwright() as p:
        ba, ca, page_admin = tw.nova_pagina(p)
        tw.login(page_admin, c_admin, admin=True)

        bb, cb, page_lider = tw.nova_pagina(p)
        tw.login(page_lider, c_lider, admin=False)

        # === ADMIN: encontrar linha QAKPIRT-TC3 (col11=Recusado) ===
        count = ir_registros(page_admin, f"{BASE_URL}/o/{ORG_ID}/records")
        print(f"Admin: {count} linhas")

        # Verificar todos os registros da pagina 1
        rows = page_admin.locator("tbody tr")
        print("\n--- Inspecionar todas as linhas para achar 'Recusado' na col11 ---")
        row_recusado = None
        row_externo_emitido = None
        for i in range(min(count, 30)):
            row = rows.nth(i)
            tds = row.locator("td")
            col10 = tds.nth(10).inner_text().strip() if tds.count() > 10 else "?"
            col11 = tds.nth(11).inner_text().strip() if tds.count() > 11 else "?"
            col3  = tds.nth(3).inner_text().strip()  if tds.count() > 3  else "?"
            col2  = tds.nth(2).inner_text().strip()  if tds.count() > 2  else "?"
            print(f"  L{i}: col3(origem)='{col3}' col10(sit)='{col10}' col11(sit_cert)='{col11}' conteudo='{col2}'")

            if "Recusado" in col11 and not row_recusado:
                row_recusado = row
                print(f"  >>> Linha {i} tem Recusado no col11 — CANDIDATA sit=pending")

            if "Externo" in col3 and "Emitido" in col11 and not row_externo_emitido:
                row_externo_emitido = row
                print(f"  >>> Linha {i} e Externo+Emitido")

        snap(page_admin, "tc1kb_00_lista_admin", full=True)

        # --- Abrir kebab da linha "Recusado" ---
        if row_recusado:
            btn = row_recusado.locator("button[aria-haspopup='menu']")
            if btn.count() == 0:
                btn = row_recusado.locator("button").last
            if btn.count() > 0:
                btn.first.click(force=True)
                page_admin.wait_for_timeout(1500)
                itens_recusado = tw.menu_visivel(page_admin)
                snap(page_admin, "tc1kb_01_menu_recusado")
                print(f"\n--- Menu linha Recusado (sit=pending?) ---")
                print(f"   {itens_recusado}")

                # Verificar se "Avaliar" esta presente
                tem_avaliar_r = any("Avaliar" in i for i in itens_recusado)
                tem_editar_r  = any("Editar"  in i for i in itens_recusado)
                print(f"   tem_Avaliar={tem_avaliar_r} tem_Editar={tem_editar_r}")

                # Se tem Editar, checar destino
                editar_aval = False
                if tem_editar_r:
                    tw.click_menuitem(page_admin, "Editar")
                    page_admin.wait_for_timeout(3000)
                    url_e = page_admin.url
                    botoes = [b.strip() for b in page_admin.locator("button").all_text_contents() if b.strip()]
                    snap(page_admin, "tc1kb_02_editar_destino")
                    editar_aval = any("Aprovar" in b for b in botoes) and any("Recusar" in b for b in botoes)
                    print(f"   Editar→URL={url_e}")
                    print(f"   Botoes: {botoes[:10]}")
                    print(f"   Editar leva a form Aprovar/Recusar: {editar_aval}")
                    page_admin.go_back()
                    ir_registros(page_admin, f"{BASE_URL}/o/{ORG_ID}/records")
                else:
                    page_admin.keyboard.press("Escape")
                    page_admin.wait_for_timeout(400)

                tc_resultado("TC1",
                    "PASSOU" if (tem_avaliar_r or editar_aval) and not (tem_avaliar_r and tem_editar_r) else
                    "FALHOU" if itens_recusado else "NAO_VERIFICADO",
                    f"Menu linha sit_cert=Recusado(sit_api=pending): {itens_recusado}. "
                    f"Avaliar={tem_avaliar_r} Editar→form={editar_aval}"
                )
            else:
                tc_resultado("TC1", "NAO_VERIFICADO", "Linha recusado sem botao kebab")
        else:
            tc_resultado("TC1", "NAO_VERIFICADO",
                        "Nao encontrou linha com col11=Recusado (sit=pending) na pagina 1. "
                        "O registro 44279851 pode nao estar na pagina 1 da lista.")

        # --- Verificar Emitido ---
        if row_externo_emitido:
            btn = row_externo_emitido.locator("button[aria-haspopup='menu']")
            if btn.count() == 0:
                btn = row_externo_emitido.locator("button").last
            if btn.count() > 0:
                btn.first.click(force=True)
                page_admin.wait_for_timeout(1500)
                itens_emit = tw.menu_visivel(page_admin)
                snap(page_admin, "tc1kb_03_menu_emitido")
                print(f"\n--- Menu Externo+Emitido ---")
                print(f"   {itens_emit}")
                page_admin.keyboard.press("Escape")
                page_admin.wait_for_timeout(400)

        # === LIDER ===
        count_l = ir_registros(page_lider, f"{BASE_URL}/o/{ORG_ID}/records")
        print(f"\nLider: {count_l} linhas")
        snap(page_lider, "tc8kb_01_lista_lider", full=True)

        rows_l = page_lider.locator("tbody tr")
        row_pend_l = None
        for i in range(min(count_l, 30)):
            row = rows_l.nth(i)
            tds = row.locator("td")
            col11 = tds.nth(11).inner_text().strip() if tds.count() > 11 else "?"
            col3  = tds.nth(3).inner_text().strip()  if tds.count() > 3  else "?"
            print(f"  L{i}: col3='{col3}' col11='{col11}'")
            if "Recusado" in col11 and not row_pend_l:
                row_pend_l = row
                print(f"  >>> Linha {i} Lider: Recusado/pendente")

        if row_pend_l:
            btn = row_pend_l.locator("button[aria-haspopup='menu']")
            if btn.count() == 0:
                btn = row_pend_l.locator("button").last
            if btn.count() > 0:
                btn.first.click(force=True)
                page_lider.wait_for_timeout(1500)
                itens_l = tw.menu_visivel(page_lider)
                snap(page_lider, "tc8kb_02_menu_lider_pendente")
                print(f"\nLider menu pendente: {itens_l}")
                tem_aval_l = any("Avaliar" in i for i in itens_l)
                tem_edit_l = any("Editar"  in i for i in itens_l)

                editar_aval_l = False
                if tem_edit_l and not tem_aval_l:
                    tw.click_menuitem(page_lider, "Editar")
                    page_lider.wait_for_timeout(3000)
                    botoes_l = [b.strip() for b in page_lider.locator("button").all_text_contents() if b.strip()]
                    snap(page_lider, "tc8kb_03_lider_editar")
                    editar_aval_l = any("Aprovar" in b for b in botoes_l)
                    print(f"   Lider Editar→Aprovar={editar_aval_l}")
                    page_lider.go_back()
                    page_lider.wait_for_timeout(2000)
                else:
                    page_lider.keyboard.press("Escape")
                    page_lider.wait_for_timeout(400)

                tc_resultado("TC8",
                    "PASSOU" if (tem_aval_l or editar_aval_l) else "FALHOU",
                    f"Lider menu pendente: {itens_l}. Avaliar={tem_aval_l} Editar→form={editar_aval_l}"
                )
        else:
            tc_resultado("TC8", "NAO_VERIFICADO",
                        f"Lider ({count_l} linhas) sem linha com sit_cert=Recusado/pendente")

        ca.close(); ba.close()
        cb.close(); bb.close()

    print("\n=== SUMARIO FINAL ===")
    for tc, r in resultados.items():
        v = r["veredito"]
        i = "✓" if v == "PASSOU" else ("✗" if v == "FALHOU" else "?")
        print(f"  {i} {tc}: {v} — {r['resumo']}")


if __name__ == "__main__":
    main()
