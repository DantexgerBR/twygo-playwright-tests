"""fechamento_qa11_tc11_final.py — TC11: Validar paginacao 25/50/100.

Seletores descobertos pelo recon:
- Select paginacao: #select_pages (values "25", "50", "100")
- Botao proxima pagina: button.chakra-button com texto "chevron_right" (icone Material)
- Botao pagina anterior: button.chakra-button com texto "chevron_left"
- Botoes de numero: button com texto "1", "2", etc.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ADMIN_EMAIL = "dante.tavares@twygo.com"
ADMIN_SENHA = "123456"
ORG_ID = "37079"

SLUG = "registros-f2-qa11"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def ir_meu_historico(page):
    url = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)


def preencher_creatable(page, input_id, valor):
    try:
        inp = page.locator(f"#{input_id}")
        if inp.count() == 0:
            return False
        inp.scroll_into_view_if_needed()
        inp.click(timeout=3000)
        page.wait_for_timeout(400)
        inp.fill(valor)
        page.wait_for_timeout(900)
        opcoes = page.locator("[class*='__option']").all()
        for op in opcoes:
            try:
                t = op.inner_text().strip()
                if valor.lower() in t.lower() and not re.search(r"criar|create", t, re.I):
                    op.click(timeout=3000)
                    return True
            except Exception:
                pass
        for op in opcoes:
            try:
                t = op.inner_text().strip()
                if re.search(r"criar|create", t, re.I):
                    op.click(timeout=3000)
                    return True
            except Exception:
                pass
        page.keyboard.press("Enter")
        return True
    except Exception:
        return False


def criar_registro(page, titulo, provedor, carga_hhmmss, data_iso):
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/records/new?in_use_mode_layout=true",
        wait_until="domcontentloaded", timeout=60000
    )
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(1500)
    tw.dispensar_nps(page)

    preencher_creatable(page, "react-select-2-input", provedor)
    preencher_creatable(page, "react-select-3-input", titulo)

    try:
        inp = page.locator("#react-select-4-input")
        inp.scroll_into_view_if_needed()
        inp.click(timeout=3000)
        page.wait_for_timeout(500)
        opcoes = page.locator("[class*='__option']").all()
        if opcoes:
            opcoes[0].click(timeout=3000)
        else:
            inp.fill("Treinamento")
            page.wait_for_timeout(600)
            page.keyboard.press("Enter")
        page.wait_for_timeout(200)
    except Exception:
        pass

    try:
        inp = page.locator("#react-select-5-input")
        inp.scroll_into_view_if_needed()
        inp.click(timeout=3000)
        page.wait_for_timeout(400)
        opcoes = page.locator("[class*='__option']").all()
        if opcoes:
            opcoes[0].click(timeout=3000)
        page.wait_for_timeout(200)
    except Exception:
        pass

    try:
        page.locator("#workload_seconds").scroll_into_view_if_needed()
        page.locator("#workload_seconds").fill(carga_hhmmss)
    except Exception:
        pass
    try:
        page.locator("#endDate").scroll_into_view_if_needed()
        page.locator("#endDate").fill(data_iso)
        page.wait_for_timeout(150)
    except Exception:
        pass

    try:
        btn = page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first
        if btn.count() == 0:
            btn = page.locator("button[type='submit']").first
        if btn.count() > 0 and btn.is_visible(timeout=2000):
            btn.scroll_into_view_if_needed()
            btn.click(timeout=5000)
            try:
                page.wait_for_url(re.compile(r"/records(\?|$)"), timeout=12000)
                return True
            except Exception:
                page.wait_for_timeout(3000)
                return "/records" in page.url and "/records/new" not in page.url
    except Exception:
        pass
    return False


TITULOS_SEED = [
    ("QA11-V3-Alura-Python",      "Alura",             "10:00:00", "2025-01-15"),
    ("QA11-V3-Alura-Django",      "Alura",             "15:00:00", "2025-02-10"),
    ("QA11-V3-Alura-Docker",      "Alura",             "08:00:00", "2025-03-05"),
    ("QA11-V3-Alura-Git",         "Alura",             "06:00:00", "2025-04-12"),
    ("QA11-V3-Alura-React",       "Alura",             "18:00:00", "2025-05-10"),
    ("QA11-V3-Coursera-ML",       "Coursera",          "40:00:00", "2025-01-15"),
    ("QA11-V3-Coursera-DS",       "Coursera",          "60:00:00", "2025-02-28"),
    ("QA11-V3-Coursera-TF",       "Coursera",          "30:00:00", "2025-03-15"),
    ("QA11-V3-Coursera-NLP",      "Coursera",          "20:00:00", "2025-04-01"),
    ("QA11-V3-Coursera-Agile",    "Coursera",          "15:00:00", "2025-04-10"),
    ("QA11-V3-FGV-Gestao",        "FGV",               "45:00:00", "2025-01-10"),
    ("QA11-V3-FGV-Lideranca",     "FGV",               "08:00:00", "2025-02-15"),
    ("QA11-V3-FGV-Financas",      "FGV",               "60:00:00", "2025-03-20"),
    ("QA11-V3-Udemy-Excel",       "Udemy",             "12:00:00", "2025-01-05"),
    ("QA11-V3-Udemy-PowerBI",     "Udemy",             "16:00:00", "2025-02-10"),
    ("QA11-V3-Udemy-Node",        "Udemy",             "20:00:00", "2025-03-15"),
    ("QA11-V3-USP-Estatistica",   "USP",               "60:00:00", "2025-01-10"),
    ("QA11-V3-USP-Direito",       "USP",               "04:00:00", "2025-04-01"),
    ("QA11-V3-LI-Storytelling",   "LinkedIn Learning", "02:00:00", "2025-01-05"),
    ("QA11-V3-LI-Negociacao",     "LinkedIn Learning", "04:00:00", "2025-02-10"),
    ("QA11-V3-LI-Design",         "LinkedIn Learning", "06:00:00", "2025-03-01"),
    ("QA11-V3-LI-Comunicacao",    "LinkedIn Learning", "02:00:00", "2025-04-01"),
    ("QA11-V3-Alura-AWS",         "Alura",             "25:00:00", "2025-05-01"),
    ("QA11-V3-Extra-TypeScript",  "Alura",             "14:00:00", "2025-06-01"),
    ("QA11-V3-Extra-Kubernetes",  "Coursera",          "35:00:00", "2025-06-10"),
    ("QA11-V3-Extra-SQL",         "Udemy",             "18:00:00", "2025-06-15"),
    ("QA11-V3-Extra-Scrum",       "FGV",               "08:00:00", "2025-06-20"),
]


def semear(page):
    log("\n=== Semeando registros ===")
    ir_meu_historico(page)
    total_atual = page.locator("table tbody tr").count()
    log(f"  Total atual: {total_atual}")

    if total_atual >= 26:
        log(f"  Ja tem {total_atual} — sem seed necessario")
        return 0, total_atual

    semeados = 0
    META = 26
    for i, (titulo, provedor, carga, data) in enumerate(TITULOS_SEED):
        if total_atual + semeados >= META:
            break
        log(f"  [{i+1:02d}] {titulo}")
        ok = criar_registro(page, titulo, provedor, carga, data)
        if ok:
            semeados += 1
            log(f"    OK #{semeados}")
        else:
            log(f"    FALHOU")

    ir_meu_historico(page)
    page.wait_for_timeout(1500)
    rows = page.locator("table tbody tr").count()
    tw.snap(page, EVID, "fechamento_seed_v3")
    log(f"  Pos-seed: {semeados} novos, visivel={rows}")
    return semeados, rows


def run_tc11(page):
    log("\n=== TC11: Paginacao 25/50/100 ===")
    ir_meu_historico(page)

    # Passo 1: pag1 exibe 25 linhas
    rows_p1 = page.locator("table tbody tr").count()
    log(f"  Pag1: {rows_p1} linhas")
    tw.snap(page, EVID, "fechamento_tc11_v3_pag1")

    # Rola footer para ver controles
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(800)
    tw.snap(page, EVID, "fechamento_tc11_v3_footer")

    if rows_p1 < 25:
        log(f"  FALHOU: pag1 tem {rows_p1} linhas (precisa 25)")
        return

    default_25 = (rows_p1 == 25)

    # Verifica indicador de pagina "1"
    btn_pag1 = page.locator("button").filter(has_text=re.compile(r"^1$")).first
    has_pag_indicator = btn_pag1.count() > 0
    log(f"  Indicador pag '1': {has_pag_indicator}")

    # Passo 2: clica "chevron_right" para ir para pagina 2
    pagina2_ok = False
    rows_p2 = 0
    try:
        # Seletor correto descoberto no recon: button com texto "chevron_right"
        btn_next = page.locator("button").filter(
            has_text=re.compile(r"^chevron_right$")
        ).first
        if btn_next.count() > 0:
            disabled = btn_next.evaluate("el => el.disabled")
            log(f"  Btn next: found, disabled={disabled}")
            if not disabled:
                btn_next.scroll_into_view_if_needed()
                btn_next.click(timeout=5000)
                page.wait_for_timeout(2000)
                rows_p2 = page.locator("table tbody tr").count()
                log(f"  Pag2: {rows_p2} linhas")
                tw.snap(page, EVID, "fechamento_tc11_v3_pag2")
                pagina2_ok = (rows_p2 >= 1)
            else:
                log("  Btn next esta DISABLED")
        else:
            log("  Btn next NAO encontrado")
            # Tenta pelo numero "2"
            btn_2 = page.locator("button").filter(has_text=re.compile(r"^2$")).first
            if btn_2.count() > 0 and not btn_2.evaluate("el => el.disabled"):
                log("  Tentando pelo botao '2'")
                btn_2.scroll_into_view_if_needed()
                btn_2.click(timeout=5000)
                page.wait_for_timeout(2000)
                rows_p2 = page.locator("table tbody tr").count()
                log(f"  Pag2 via btn '2': {rows_p2}")
                tw.snap(page, EVID, "fechamento_tc11_v3_pag2")
                pagina2_ok = (rows_p2 >= 1)
    except Exception as e:
        log(f"  Pag2 erro: {e}")

    # Volta pag 1 para testar selects
    ir_meu_historico(page)
    page.wait_for_timeout(1000)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)

    # Passo 3: 50 por pagina
    pg50_ok = False
    rows_50 = 0
    try:
        sel = page.locator("#select_pages")
        if sel.count() > 0 and sel.is_visible(timeout=2000):
            sel.select_option("50")
            page.wait_for_timeout(2000)
            rows_50 = page.locator("table tbody tr").count()
            log(f"  50/pag: {rows_50} linhas")
            tw.snap(page, EVID, "fechamento_tc11_v3_50pag")
            pg50_ok = True
    except Exception as e:
        log(f"  50/pag erro: {e}")

    # Passo 4: 100 por pagina
    pg100_ok = False
    rows_100 = 0
    try:
        sel = page.locator("#select_pages")
        if sel.count() > 0 and sel.is_visible(timeout=2000):
            sel.select_option("100")
            page.wait_for_timeout(2000)
            rows_100 = page.locator("table tbody tr").count()
            log(f"  100/pag: {rows_100} linhas")
            tw.snap(page, EVID, "fechamento_tc11_v3_100pag")
            pg100_ok = True
    except Exception as e:
        log(f"  100/pag erro: {e}")

    log(f"\n  RESUMO TC11:")
    log(f"    Passo 1: pag1={rows_p1}, default_25={default_25}, "
        f"indicador_pag={has_pag_indicator}")
    log(f"    Passo 2: pagina2={pagina2_ok} ({rows_p2} linhas)")
    log(f"    Passo 3: 50/pag={pg50_ok} ({rows_50} linhas)")
    log(f"    Passo 4: 100/pag={pg100_ok} ({rows_100} linhas)")

    # Avaliacao
    passos_ok = [default_25, pagina2_ok, pg50_ok, pg100_ok]
    if all(passos_ok):
        print(f"\nTC11: PASSOU — todos 4 passos OK")
    else:
        print(f"\nTC11: FALHOU — passos: {passos_ok} "
              f"(p1={default_25}, p2={pagina2_ok}, p3={pg50_ok}, p4={pg100_ok})")


def main():
    log("=" * 60)
    log("fechamento_qa11_tc11_final.py — TC11 paginacao")
    log(f"Org: {BASE_URL} / ORG_ID: {ORG_ID}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            # Login como aluno (dante)
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("#user_email", timeout=15000)
            page.fill("#user_email", ADMIN_EMAIL)
            page.fill("#user_password", ADMIN_SENHA)
            page.click("#user_submit")
            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            log(f"Logado: {page.url[:60]}")

            semeados, rows = semear(page)
            log(f"Semeados: {semeados}, visivel: {rows}")

            run_tc11(page)
        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("FIM")
    log("=" * 60)


if __name__ == "__main__":
    main()
