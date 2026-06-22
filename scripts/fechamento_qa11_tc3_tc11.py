"""fechamento_qa11_tc3_tc11.py — TC3 + Seed + TC11 (script final consolidado).

TC3: Admin cria usuario novo. Form de usuario:
  - Campo Email: placeholder "Ex: joao@email.com"
  - Campo Nome: placeholder "Ex: Leandro"
  - Campo Sobrenome: tem asterisco obrigatorio

Preenchimento PRECISO pelo placeholder.
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

RESULTADOS = {}


def log(msg):
    print(msg, flush=True)


def passou(tc_id, evidencias, obs=""):
    RESULTADOS[tc_id] = {"veredito": "PASSOU", "evidencias": evidencias, "obs": obs}
    log(f"  [TC{tc_id}] PASSOU{' — ' + obs if obs else ''}")


def falhou(tc_id, evidencias, motivo):
    RESULTADOS[tc_id] = {"veredito": "FALHOU", "evidencias": evidencias, "obs": motivo}
    log(f"  [TC{tc_id}] FALHOU — {motivo}")


def ir_meu_historico(page):
    url = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)


# ─── TC3: Admin cria usuario novo, aluno valida empty state ────────────────────

def run_tc3(p):
    log("\n=== TC3: Empty state ===")
    evids = []
    import os
    novo_email = f"qa11empty{os.getpid()}@mailtest.example"
    novo_senha = "TwygoQA123!"
    log(f"  Novo usuario: {novo_email}")

    # Browser Admin
    browser_adm, ctx_adm, page_adm = tw.nova_pagina(p)
    criado = False
    try:
        # Login admin
        page_adm.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
        page_adm.wait_for_selector("#user_email", timeout=15000)
        page_adm.fill("#user_email", ADMIN_EMAIL)
        page_adm.fill("#user_password", ADMIN_SENHA)
        page_adm.click("#user_submit")
        try:
            page_adm.wait_for_load_state("networkidle", timeout=25000)
        except Exception:
            pass
        page_adm.wait_for_timeout(2000)
        tw.dispensar_nps(page_adm)
        # Switch admin
        page_adm.goto(
            f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
            wait_until="domcontentloaded", timeout=60000
        )
        try:
            page_adm.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page_adm.wait_for_timeout(2000)
        tw.dispensar_nps(page_adm)
        log(f"  Admin: {page_adm.url[:50]}")

        # Navega Usuarios
        page_adm.goto(
            f"{BASE_URL}/o/{ORG_ID}/users/new",
            wait_until="domcontentloaded", timeout=60000
        )
        try:
            page_adm.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        page_adm.wait_for_timeout(2000)
        tw.dispensar_nps(page_adm)
        log(f"  Form: {page_adm.url[:50]}")
        tw.snap(page_adm, EVID, "fechamento_tc3_form_aberto")

        # Preenche E-mail pelo placeholder EXATO: "Ex: joao@email.com"
        email_filled = False
        try:
            campo = page_adm.locator("input[placeholder='Ex: joao@email.com']").first
            if campo.count() > 0:
                campo.scroll_into_view_if_needed()
                campo.click(timeout=3000)
                campo.fill(novo_email)
                page_adm.wait_for_timeout(200)
                email_filled = campo.input_value() == novo_email
                log(f"  Email preenchido: {campo.input_value()!r}")
        except Exception as e:
            log(f"  Email erro: {e}")

        if not email_filled:
            # Fallback pelo label "E-mail"
            try:
                label_email = page_adm.get_by_label("E-mail").first
                if label_email.count() > 0 and label_email.is_visible(timeout=1000):
                    label_email.click(timeout=2000)
                    label_email.fill(novo_email)
                    page_adm.wait_for_timeout(200)
                    email_filled = True
                    log(f"  Email por label: {label_email.input_value()!r}")
            except Exception as e:
                log(f"  Email label erro: {e}")

        # Nome — placeholder "Ex: Leandro"
        try:
            nome_inp = page_adm.locator("input[placeholder='Ex: Leandro']").first
            if nome_inp.count() > 0:
                nome_inp.scroll_into_view_if_needed()
                nome_inp.fill("QA11")
        except Exception:
            pass

        # Sobrenome — placeholder "Ex: Silva"
        try:
            sob_inp = page_adm.locator("input[placeholder='Ex: Silva']").first
            if sob_inp.count() == 0:
                sob_inp = page_adm.locator("input").filter(
                    has_text=re.compile(r"sobrenome", re.I)
                ).first
            if sob_inp.count() > 0 and sob_inp.is_visible(timeout=1000):
                sob_inp.fill("EmptyUser")
        except Exception:
            pass

        tw.snap(page_adm, EVID, "fechamento_tc3_form_preenchido")
        log(f"  Email preenchido: {email_filled}")

        # Salva
        try:
            btn = page_adm.get_by_role("button", name=re.compile(
                r"Salvar|Criar|Convidar|Enviar", re.I)).first
            if btn.count() == 0:
                btn = page_adm.locator("button[type='submit']").first
            if btn.count() > 0 and btn.is_visible(timeout=2000):
                btn.scroll_into_view_if_needed()
                btn.click(timeout=5000)
                # Aguarda redirect
                try:
                    page_adm.wait_for_url(
                        re.compile(r"/users(?!/new|\d)"),
                        timeout=10000
                    )
                    criado = True
                except Exception:
                    page_adm.wait_for_timeout(3000)
                    criado = ("/users/new" not in page_adm.url and
                              "/users" in page_adm.url)
                log(f"  Criado: {criado}, URL: {page_adm.url[:60]}")
                tw.snap(page_adm, EVID, "fechamento_tc3_apos_criar")
                evids.append("fechamento_tc3_apos_criar.png")
        except Exception as e:
            log(f"  Salvar erro: {e}")
    finally:
        ctx_adm.close()
        browser_adm.close()

    if not criado or not email_filled:
        falhou(3, evids,
               f"nao foi possivel criar usuario (email_filled={email_filled}, "
               f"criado={criado}) — validar TC3 requer usuario com ZERO registros")
        return

    # Browser do novo usuario
    browser_novo, ctx_novo, page_novo = tw.nova_pagina(p)
    try:
        page_novo.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
        page_novo.wait_for_selector("#user_email", timeout=15000)
        page_novo.fill("#user_email", novo_email)
        page_novo.fill("#user_password", novo_senha)
        page_novo.click("#user_submit")
        try:
            page_novo.wait_for_load_state("networkidle", timeout=25000)
        except Exception:
            pass
        page_novo.wait_for_timeout(3000)
        tw.dispensar_nps(page_novo)

        login_ok = "/users/login" not in page_novo.url and "/login" not in page_novo.url
        log(f"  Login novo usuario: ok={login_ok}, URL={page_novo.url[:50]}")
        tw.snap(page_novo, EVID, "fechamento_tc3_login_novo")
        evids.append("fechamento_tc3_login_novo.png")

        if not login_ok:
            # Tenta senha padrao
            page_novo.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
            page_novo.wait_for_selector("#user_email", timeout=10000)
            page_novo.fill("#user_email", novo_email)
            page_novo.fill("#user_password", "123456")
            page_novo.click("#user_submit")
            try:
                page_novo.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            page_novo.wait_for_timeout(3000)
            tw.dispensar_nps(page_novo)
            login_ok = "/users/login" not in page_novo.url and "/login" not in page_novo.url
            log(f"  Login com 123456: ok={login_ok}")

        if not login_ok:
            falhou(3, evids,
                   f"usuario criado mas login falhou (email={novo_email}) — "
                   "provavelmente precisa de convite por email")
            return

        # Navega para Meu historico
        ir_meu_historico(page_novo)
        tw.snap(page_novo, EVID, "fechamento_tc3_empty")
        evids.append("fechamento_tc3_empty.png")

        rows = page_novo.locator("table tbody tr").count()
        msg_exata = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
        has_empty = page_novo.get_by_text(msg_exata).count() > 0
        log(f"  Empty msg: {has_empty}, rows: {rows}")

        kpi_labels = ["Emitidos", "Expirados", "Pendentes", "Recusados"]
        kpi_found = {}
        kpi_values = {}
        for label in kpi_labels:
            try:
                card = page_novo.locator(
                    "[class*='stat'], [class*='kpi'], [class*='card'], [class*='Stat']"
                ).filter(has_text=label).first
                if card.count() > 0:
                    kpi_found[label] = True
                    nums = re.findall(r'\b(\d+)\b', card.inner_text())
                    kpi_values[label] = int(nums[0]) if nums else None
                else:
                    kpi_found[label] = False
                    kpi_values[label] = None
            except Exception:
                kpi_found[label] = False
                kpi_values[label] = None

        tw.snap(page_novo, EVID, "fechamento_tc3_kpis")
        evids.append("fechamento_tc3_kpis.png")
        log(f"  KPIs: {kpi_found} / valores: {kpi_values}")

        all_4 = all(kpi_found.get(l, False) for l in kpi_labels)
        any_nz = any(kpi_values.get(l, 0) not in (0, None) for l in kpi_labels)

        if has_empty and rows == 0 and all_4 and not any_nz:
            passou(3, evids,
                   f"msg exata presente; 0 linhas; 4 KPIs=0 ({kpi_values}); "
                   f"email={novo_email}")
        elif not has_empty and rows == 0:
            falhou(3, evids, f"tabela vazia mas msg exata NAO encontrada")
        elif not all_4:
            falhou(3, evids, f"KPIs ausentes: {[l for l in kpi_labels if not kpi_found.get(l)]}")
        elif any_nz:
            falhou(3, evids, f"KPIs nao zerados: {kpi_values}")
        else:
            falhou(3, evids, f"fallback: msg={has_empty}, rows={rows}, kpi={kpi_values}")
    finally:
        ctx_novo.close()
        browser_novo.close()


# ─── Criar registro (seed) ─────────────────────────────────────────────────────

def preencher_creatable(page, input_id, valor):
    try:
        inp = page.locator(f"#{input_id}")
        if inp.count() == 0:
            return False
        inp.scroll_into_view_if_needed()
        inp.click(timeout=3000)
        page.wait_for_timeout(300)
        inp.fill(valor)
        page.wait_for_timeout(900)
        opcoes = page.locator("[class*='__option']").all()
        for op in opcoes:
            try:
                t = op.inner_text().strip()
                if valor.lower() in t.lower() and not re.search(r"criar|create", t, re.I):
                    op.click(timeout=3000)
                    page.wait_for_timeout(300)
                    return True
            except Exception:
                pass
        for op in opcoes:
            try:
                t = op.inner_text().strip()
                if re.search(r"criar|create", t, re.I):
                    op.click(timeout=3000)
                    page.wait_for_timeout(300)
                    return True
            except Exception:
                pass
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
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
    page.wait_for_timeout(200)
    preencher_creatable(page, "react-select-3-input", titulo)
    page.wait_for_timeout(200)

    try:
        inp = page.locator("#react-select-4-input")
        inp.scroll_into_view_if_needed()
        inp.click(timeout=3000)
        page.wait_for_timeout(500)
        opcoes = page.locator("[class*='__option']").all()
        if opcoes:
            opcoes[0].click(timeout=3000)
        else:
            inp.fill("Curso")
            page.wait_for_timeout(600)
            opcoes2 = page.locator("[class*='__option']").all()
            if opcoes2:
                opcoes2[0].click(timeout=3000)
            else:
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
        btn = page.get_by_role("button", name=re.compile(
            r"^Salvar$|^Enviar para aprovação$", re.I)).first
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


TITULOS = [
    ("QA11-F2-Alura-Python",       "Alura",             "10:00:00", "2025-01-15"),
    ("QA11-F2-Alura-Django",       "Alura",             "15:00:00", "2025-02-10"),
    ("QA11-F2-Alura-Docker",       "Alura",             "08:00:00", "2025-03-05"),
    ("QA11-F2-Alura-Git",          "Alura",             "06:00:00", "2025-04-12"),
    ("QA11-F2-Alura-React",        "Alura",             "18:00:00", "2025-05-10"),
    ("QA11-F2-Coursera-ML",        "Coursera",          "40:00:00", "2025-01-15"),
    ("QA11-F2-Coursera-DS",        "Coursera",          "60:00:00", "2025-02-28"),
    ("QA11-F2-Coursera-TF",        "Coursera",          "30:00:00", "2025-03-15"),
    ("QA11-F2-Coursera-NLP",       "Coursera",          "20:00:00", "2025-04-01"),
    ("QA11-F2-Coursera-Agile",     "Coursera",          "15:00:00", "2025-04-10"),
    ("QA11-F2-FGV-Gestao",         "FGV",               "45:00:00", "2025-01-10"),
    ("QA11-F2-FGV-Lideranca",      "FGV",               "08:00:00", "2025-02-15"),
    ("QA11-F2-FGV-Financas",       "FGV",               "60:00:00", "2025-03-20"),
    ("QA11-F2-Udemy-Excel",        "Udemy",             "12:00:00", "2025-01-05"),
    ("QA11-F2-Udemy-PowerBI",      "Udemy",             "16:00:00", "2025-02-10"),
    ("QA11-F2-Udemy-Node",         "Udemy",             "20:00:00", "2025-03-15"),
    ("QA11-F2-USP-Estatistica",    "USP",               "60:00:00", "2025-01-10"),
    ("QA11-F2-USP-Direito",        "USP",               "04:00:00", "2025-04-01"),
    ("QA11-F2-LI-Storytelling",    "LinkedIn Learning", "02:00:00", "2025-01-05"),
    ("QA11-F2-LI-Negociacao",      "LinkedIn Learning", "04:00:00", "2025-02-10"),
    ("QA11-F2-LI-Design",          "LinkedIn Learning", "06:00:00", "2025-03-01"),
    ("QA11-F2-LI-Comunicacao",     "LinkedIn Learning", "02:00:00", "2025-04-01"),
    ("QA11-F2-Alura-AWS",          "Alura",             "25:00:00", "2025-05-01"),
    ("QA11-F2-Extra-TypeScript",   "Alura",             "14:00:00", "2025-06-01"),
    ("QA11-F2-Extra-Kubernetes",   "Coursera",          "35:00:00", "2025-06-10"),
    ("QA11-F2-Extra-SQL-Avancado", "Udemy",             "18:00:00", "2025-06-15"),
    ("QA11-F2-Extra-Scrum",        "FGV",               "08:00:00", "2025-06-20"),
]


def semear(page):
    log("\n=== Semeando ===")
    ir_meu_historico(page)
    total_atual = page.locator("table tbody tr").count()
    log(f"  Inicial: {total_atual}")

    if total_atual >= 25:
        log("  Ja tem 25+ — TC11 deve funcionar")
        return 0, total_atual

    semeados = 0
    META = 26
    for i, (titulo, provedor, carga, data) in enumerate(TITULOS):
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
    tw.snap(page, EVID, "fechamento_seed_pos_semeia")
    log(f"  Pos-semeia: {semeados} OK, visivel={rows}")
    return semeados, rows


def run_tc11(page):
    log("\n=== TC11: Paginacao 25/50/100 ===")
    evids = []
    ir_meu_historico(page)

    rows_p1 = page.locator("table tbody tr").count()
    log(f"  Pag1: {rows_p1}")
    tw.snap(page, EVID, "fechamento_tc11_pag1")
    evids.append("fechamento_tc11_pag1.png")

    if rows_p1 < 25:
        falhou(11, evids, f"pag1={rows_p1} linhas (precisa 25+)")
        return

    default_25 = rows_p1 == 25

    # Encontra o select de por-pagina
    per_page_sel = None
    all_selects = page.locator("select").all()
    log(f"  Selects na pagina: {len(all_selects)}")
    for s in all_selects:
        try:
            if s.is_visible(timeout=1000):
                opts = s.evaluate("el => Array.from(el.options).map(o => o.value)")
                log(f"    Select opcoes: {opts}")
                if any(v in ["25", "50", "100"] for v in opts):
                    per_page_sel = s
                    log(f"    ESTE E O per-page select!")
                    break
        except Exception:
            pass

    tw.snap(page, EVID, "fechamento_tc11_controles")
    evids.append("fechamento_tc11_controles.png")

    has_pag = per_page_sel is not None

    # Pag 2 via JS
    pagina2_ok = False
    rows_p2 = 0
    try:
        clicou = page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(b => {
                const t = b.innerText?.trim();
                const al = b.getAttribute('aria-label') || '';
                return (t === '>' || al.toLowerCase().includes('pr') ||
                        al.toLowerCase().includes('next')) && !b.disabled;
            });
            if (b) { b.click(); return b.innerText + '|' + b.getAttribute('aria-label'); }
            return null;
        }""")
        log(f"  Botao pag2 clicado: {clicou!r}")
        if clicou:
            page.wait_for_timeout(2000)
            rows_p2 = page.locator("table tbody tr").count()
            log(f"  Pag2: {rows_p2}")
            tw.snap(page, EVID, "fechamento_tc11_pag2")
            evids.append("fechamento_tc11_pag2.png")
            pagina2_ok = rows_p2 > 0
    except Exception as e:
        log(f"  Pag2 erro: {e}")

    # Volta pag 1
    try:
        page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(b => {
                const t = b.innerText?.trim();
                const al = b.getAttribute('aria-label') || '';
                return (t === '<<' || t === '«' ||
                        al.toLowerCase().includes('primeira') ||
                        al.toLowerCase().includes('first'));
            });
            if (b) b.click();
        }""")
        page.wait_for_timeout(1000)
    except Exception:
        ir_meu_historico(page)

    # 50/pag
    pg50_ok = False
    rows_50 = 0
    if per_page_sel:
        try:
            per_page_sel.select_option("50")
            page.wait_for_timeout(2000)
            rows_50 = page.locator("table tbody tr").count()
            log(f"  50/pag: {rows_50}")
            tw.snap(page, EVID, "fechamento_tc11_50pag")
            evids.append("fechamento_tc11_50pag.png")
            pg50_ok = True
        except Exception as e:
            log(f"  50/pag erro: {e}")

    # 100/pag
    pg100_ok = False
    rows_100 = 0
    if per_page_sel and pg50_ok:
        try:
            per_page_sel.select_option("100")
            page.wait_for_timeout(2000)
            rows_100 = page.locator("table tbody tr").count()
            log(f"  100/pag: {rows_100}")
            tw.snap(page, EVID, "fechamento_tc11_100pag")
            evids.append("fechamento_tc11_100pag.png")
            pg100_ok = True
        except Exception as e:
            log(f"  100/pag erro: {e}")

    log(f"\n  Resumo: pag1={rows_p1}(def25={default_25}), pag2={pagina2_ok}({rows_p2}), "
        f"50={pg50_ok}({rows_50}), 100={pg100_ok}({rows_100}), has_pag={has_pag}")

    if default_25 and has_pag and pagina2_ok and pg50_ok and pg100_ok:
        passou(11, evids,
               f"pag1=25; pag2={rows_p2}; 50/pag={rows_50}; 100/pag={rows_100}")
    elif default_25 and has_pag and pagina2_ok and pg50_ok:
        falhou(11, evids,
               f"pag1=25 OK, pag2 OK({rows_p2}), 50/pag OK({rows_50}), "
               f"MAS 100/pag falhou (rows={rows_100})")
    elif default_25 and has_pag and pagina2_ok:
        falhou(11, evids,
               f"pag1=25 OK, pag2 OK, MAS 50/100 nao testavel (select nao encontrado)")
    elif default_25 and has_pag:
        falhou(11, evids,
               f"pag1=25 OK, has_pag OK, MAS pag2 NAO funcionou ({rows_p2})")
    else:
        falhou(11, evids,
               f"pag1={rows_p1}, default_25={default_25}, has_pag={has_pag}")


def main():
    log("=" * 60)
    log("fechamento_qa11_tc3_tc11.py")
    log(f"Org: {BASE_URL} / ID: {ORG_ID}")
    log("=" * 60)

    # TC3
    with tw.sync_playwright() as p1:
        run_tc3(p1)

    # Seed + TC11
    with tw.sync_playwright() as p2:
        browser, ctx, page = tw.nova_pagina(p2)
        try:
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
            log(f"Aluno logado: {page.url[:60]}")

            semeados, rows = semear(page)
            log(f"Semeados: {semeados}, visivel: {rows}")
            run_tc11(page)
        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("RESULTADOS:")
    for tc, r in sorted(RESULTADOS.items()):
        log(f"  TC{tc}: {r['veredito']} — {r['obs']}")
    log("=" * 60)


if __name__ == "__main__":
    main()
