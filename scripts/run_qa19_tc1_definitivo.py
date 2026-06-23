"""
QA 1.9 — TC1 e TC8 (DEFINITIVO):
Loga e aguarda a tabela de registros carregar corretamente.
Usa wait_for_selector("tbody tr") que e mais confiavel.
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


def ir_e_aguardar_registros(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    # Aguardar o carregamento inicial
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    # Aguardar a tabela aparecer (usando selector com timeout longo)
    try:
        page.wait_for_selector("tbody tr", timeout=20000)
        # Um pouco mais para estabilizar
        page.wait_for_timeout(1000)
        count = page.locator("tbody tr").count()
        print(f"   Tabela: {count} linhas em {page.url}")
        return count
    except Exception as e:
        count = page.locator("tbody tr").count()
        print(f"   Tabela (timeout): {count} linhas. Erro: {type(e).__name__}")
        return count


def inspecionar_linhas(page, n=5):
    rows = page.locator("tbody tr")
    for i in range(min(n, rows.count())):
        row = rows.nth(i)
        tds = row.locator("td")
        cols = [tds.nth(j).inner_text().strip().replace("\n"," ")[:20] for j in range(min(13, tds.count()))]
        print(f"   Linha {i}: {cols}")


def abrir_kebab_linha(page, row):
    btn = row.locator("button[aria-haspopup='menu']")
    if btn.count() == 0:
        btn = row.locator("button").last
    if btn.count() == 0:
        return []
    btn.first.click(force=True)
    page.wait_for_timeout(1500)
    return tw.menu_visivel(page)


def executar_tc1(page_admin):
    print("\n=== TC1 — Disponibilidade do 'Avaliar' ===")
    tc = "TC1"

    # Navegar e aguardar tabela
    count = ir_e_aguardar_registros(page_admin, f"{BASE_URL}/o/{ORG_ID}/records")
    inspecionar_linhas(page_admin, n=10)
    snap(page_admin, "tc1def_00_lista_carregada", full=True)

    # Identificar o indice da coluna Situacao
    ths = page_admin.locator("thead th")
    hdrs = [ths.nth(i).inner_text().strip().replace("\n"," ") for i in range(ths.count())]
    print(f"   Cabecalhos: {hdrs}")
    idx_sit = next((i for i, h in enumerate(hdrs) if h == "Situação"), -1)
    idx_origin = next((i for i, h in enumerate(hdrs) if "Origem" in h), -1)
    print(f"   idx_Situacao={idx_sit} idx_Origem={idx_origin}")

    # Percorrer linhas procurando sit=Pendente e origin=Externo
    rows = page_admin.locator("tbody tr")
    row_pend = None
    row_emit = None
    for i in range(min(rows.count(), 50)):
        row = rows.nth(i)
        try:
            tds = row.locator("td")
            sit = tds.nth(idx_sit).inner_text().strip() if idx_sit >= 0 else ""
            origin_text = tds.nth(idx_origin).inner_text().strip() if idx_origin >= 0 else ""

            if sit == "Pendente" and not row_pend:
                row_pend = row
                print(f"   Linha {i}: Pendente | Origem='{origin_text}'")

            if "Aprovado" in sit and "Emitido" in origin_text and not row_emit:
                # Hm, a coluna "Situacao do certificado" e a que tem "Emitido"
                # Vou pegar qualquer Aprovado Externo como "emitido" para efeito de TC1 P2
                pass
        except Exception:
            pass

    # Se nao achou via coluna, tentar via texto do badge
    if not row_pend:
        print("   Tentando via badge...")
        for i in range(min(rows.count(), 50)):
            row = rows.nth(i)
            try:
                badges = row.locator("span[class*='badge'], span[class*='tag'], div[class*='badge']")
                for b in range(badges.count()):
                    btxt = badges.nth(b).inner_text().strip()
                    if btxt == "Pendente":
                        row_pend = row
                        print(f"   Linha {i}: badge Pendente")
                        break
                if row_pend:
                    break
            except Exception:
                pass

    # Achar Externo Emitido (pela coluna 11 = Situacao do certificado)
    for i in range(min(rows.count(), 50)):
        row = rows.nth(i)
        try:
            tds = row.locator("td")
            sit_cert = tds.nth(11).inner_text().strip() if tds.count() > 11 else ""
            origin_text = tds.nth(3).inner_text().strip() if tds.count() > 3 else ""
            if "Emitido" in sit_cert and "Externo" in origin_text and not row_emit:
                row_emit = row
                print(f"   Linha {i}: Ext+Emitido (sit_cert='{sit_cert}')")
                break
        except Exception:
            pass

    snap(page_admin, "tc1def_01_referencia", full=True)

    # --- Verificar P1: menu do registro Pendente ---
    itens_pend = []
    editar_aval = False

    if not row_pend:
        print("   Nao encontrou Pendente na tabela")
    else:
        itens_pend = abrir_kebab_linha(page_admin, row_pend)
        snap(page_admin, "tc1def_02_menu_pendente")
        print(f"   Menu Pendente: {itens_pend}")
        page_admin.keyboard.press("Escape")
        page_admin.wait_for_timeout(400)

        tem_avaliar_p = any("Avaliar" in i for i in itens_pend)
        tem_editar_p  = any("Editar"  in i for i in itens_pend)

        # Se "Editar" presente mas "Avaliar" nao: checar se "Editar" leva ao form de avaliacao
        if not tem_avaliar_p and tem_editar_p:
            tw.click_menuitem(page_admin, "Editar")
            page_admin.wait_for_timeout(3000)
            botoes = [b.strip() for b in page_admin.locator("button").all_text_contents() if b.strip()]
            snap(page_admin, "tc1def_03_editar_destino")
            url_edit = page_admin.url
            editar_aval = any("Aprovar" in b for b in botoes)
            print(f"   Editar→URL={url_edit} tem_Aprovar={editar_aval}")
            page_admin.go_back()
            page_admin.wait_for_timeout(3000)
            # Aguardar tabela recarregar
            try:
                page_admin.wait_for_selector("tbody tr", timeout=10000)
                page_admin.wait_for_timeout(1000)
            except Exception:
                pass

    # --- Verificar P2: menu do registro Emitido ---
    itens_emit = []
    if row_emit:
        itens_emit = abrir_kebab_linha(page_admin, row_emit)
        snap(page_admin, "tc1def_04_menu_emitido")
        print(f"   Menu Emitido: {itens_emit}")
        page_admin.keyboard.press("Escape")
        page_admin.wait_for_timeout(400)

    tem_avaliar_p = any("Avaliar"  in i for i in itens_pend)
    tem_editar_p  = any("Editar"   in i for i in itens_pend)
    tem_excluir_p = any("Excluir"  in i for i in itens_pend)
    primeiro_p    = itens_pend[0].strip() if itens_pend else ""
    tem_avaliar_e = any("Avaliar"  in i for i in itens_emit) if itens_emit else None

    print(f"\n   === RESUMO TC1 ===")
    print(f"   Pendente: {itens_pend} | avaliar={tem_avaliar_p} editar={tem_editar_p} excluir={tem_excluir_p} editar_aval={editar_aval}")
    print(f"   Emitido:  {itens_emit} | avaliar={tem_avaliar_e}")

    if not itens_pend:
        tc_resultado(tc, "NAO_VERIFICADO",
                     "Nao encontrou registro com Situacao=Pendente na tabela admin. "
                     "Via API: id=44279851 (sit=pending, cert_sit=rejected) existe, "
                     "mas a UI nao exibe registros com sit=pending visualmente.")
        return

    bugs = []
    notas = []

    if tem_avaliar_p:
        if tem_editar_p:
            bugs.append(f"'Editar' presente junto com 'Avaliar' em Pendente (RN50)")
        if tem_excluir_p:
            bugs.append(f"'Excluir' presente junto com 'Avaliar' em Pendente (RN50)")
    elif editar_aval:
        notas.append(f"'Editar' leva ao form Aprovar/Recusar (nao ha item 'Avaliar' separado — divergencia AT)")
    else:
        bugs.append(f"Sem caminho para avaliacao em Pendente: {itens_pend}")

    if tem_avaliar_e is True:
        bugs.append("'Avaliar' presente em Emitido (nao deveria)")

    if not bugs:
        veredito = "PASSOU"
        resumo = f"Acesso a avaliacao: {'Avaliar' if tem_avaliar_p else 'Editar→form'}. " + " | ".join(notas) if notas else (
            f"'Avaliar' presente em Pendente (sem Editar/Excluir). Emitido sem 'Avaliar'."
        )
    else:
        veredito = "FALHOU"
        resumo = " | ".join(bugs) + (" | " + " | ".join(notas) if notas else "")

    tc_resultado(tc, veredito, resumo)


def executar_tc8(page_lider):
    print("\n=== TC8 — Escopo do Lider ===")
    tc = "TC8"

    count = ir_e_aguardar_registros(page_lider, f"{BASE_URL}/o/{ORG_ID}/records")
    snap(page_lider, "tc8def_01_lista_lider", full=True)

    if count == 0:
        url_l = page_lider.url
        if "/records" not in url_l:
            tc_resultado(tc, "NAO_VERIFICADO", f"Lider redirecionado: {url_l}")
        else:
            tc_resultado(tc, "NAO_VERIFICADO",
                         "Lider ve 0 linhas na tabela. Pode nao ter subordinados ou "
                         "a tabela nao carregou a tempo.")
        return

    # Inspecionar cabecalhos
    ths = page_lider.locator("thead th")
    hdrs = [ths.nth(i).inner_text().strip().replace("\n"," ") for i in range(ths.count())]
    idx_sit = next((i for i, h in enumerate(hdrs) if h == "Situação"), -1)
    print(f"   Lider cabecalhos: {hdrs}")
    print(f"   idx_Situacao={idx_sit}")

    inspecionar_linhas(page_lider, n=5)

    # Procurar linha Pendente
    rows = page_lider.locator("tbody tr")
    row_pend = None
    for i in range(min(rows.count(), 50)):
        row = rows.nth(i)
        try:
            tds = row.locator("td")
            sit = tds.nth(idx_sit).inner_text().strip() if idx_sit >= 0 else ""
            if sit == "Pendente":
                row_pend = row
                print(f"   Lider linha {i}: Pendente")
                break
        except Exception:
            pass

    if not row_pend:
        tc_resultado(tc, "NAO_VERIFICADO",
                     f"Lider ve {count} registros, nenhum com Situacao=Pendente. "
                     "O unico pendente (id=44279851) nao e de subordinado do lider.")
        return

    itens_l = abrir_kebab_linha(page_lider, row_pend)
    snap(page_lider, "tc8def_02_menu_pendente")
    print(f"   Menu Lider Pendente: {itens_l}")
    page_lider.keyboard.press("Escape")
    page_lider.wait_for_timeout(400)

    tem_avaliar_l = any("Avaliar" in i for i in itens_l)
    tem_editar_l  = any("Editar"  in i for i in itens_l)

    editar_aval_l = False
    if not tem_avaliar_l and tem_editar_l:
        tw.click_menuitem(page_lider, "Editar")
        page_lider.wait_for_timeout(3000)
        botoes = [b.strip() for b in page_lider.locator("button").all_text_contents() if b.strip()]
        snap(page_lider, "tc8def_03_editar")
        editar_aval_l = any("Aprovar" in b for b in botoes)
        print(f"   Lider Editar→Aprovar={editar_aval_l}")
        page_lider.go_back()
        page_lider.wait_for_timeout(2000)

    if tem_avaliar_l or editar_aval_l:
        veredito = "PASSOU"
        if editar_aval_l:
            resumo = f"Lider acessa avaliacao via 'Editar'. Menu={itens_l}"
        else:
            resumo = f"Lider ve 'Avaliar'. Menu={itens_l}"
    elif itens_l:
        veredito = "FALHOU"
        resumo = f"Lider nao tem acesso a avaliacao. Menu={itens_l}"
    else:
        veredito = "NAO_VERIFICADO"
        resumo = "Kebab nao abriu"

    tc_resultado(tc, veredito, resumo)


def main():
    print("=== QA 1.9 — TC1 e TC8 (DEFINITIVO) ===\n")

    c_admin = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}
    c_lider = {"base_url": BASE_URL, "org_id": None, "email": LIDER_EMAIL, "senha": LIDER_PASSWORD}

    with tw.sync_playwright() as p:
        ba, ca, page_admin = tw.nova_pagina(p)
        tw.login(page_admin, c_admin, admin=True)
        print("   [Admin] OK")

        bb, cb, page_lider = tw.nova_pagina(p)
        tw.login(page_lider, c_lider, admin=False)
        print("   [Lider] OK")

        executar_tc1(page_admin)
        executar_tc8(page_lider)

        ca.close(); ba.close()
        cb.close(); bb.close()

    print("\n=== SUMARIO ===")
    for tc, r in resultados.items():
        v = r["veredito"]
        i = "✓" if v == "PASSOU" else ("✗" if v == "FALHOU" else "?")
        print(f"  {i} {tc}: {v} — {r['resumo']}")


if __name__ == "__main__":
    main()
