"""fechamento_qa11_final.py — TC3 (usuario novo) + Seed 26+ + TC11 paginacao.

Script FINAL baseado em debug real do form. Correcoes:
- Seed: apos salvar, aguarda redirect com wait_for_url em vez de timeout fixo
- TC3: cria usuario novo via admin + logar em browser separado
- TC11: testa 25/50/100 com select nativo e fallback Chakra
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
    print(msg)


def passou(tc_id, evidencias, obs=""):
    RESULTADOS[tc_id] = {"veredito": "PASSOU", "evidencias": evidencias, "obs": obs}
    log(f"  [TC{tc_id}] PASSOU{' — ' + obs if obs else ''}")


def falhou(tc_id, evidencias, motivo):
    RESULTADOS[tc_id] = {"veredito": "FALHOU", "evidencias": evidencias, "obs": motivo}
    log(f"  [TC{tc_id}] FALHOU — {motivo}")


# ─── Login ─────────────────────────────────────────────────────────────────────

def login_aluno(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    if "/users/login" in page.url:
        raise SystemExit("Login Aluno falhou.")
    log(f"  Aluno logado: {page.url[:60]}")


def login_admin(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    # Switch admin
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded", timeout=60000
    )
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    log(f"  Admin logado: {page.url[:60]}")


def ir_meu_historico(page):
    url = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)


# ─── Criar 1 registro (versao corrigida) ───────────────────────────────────────

def preencher_creatable(page, input_id, valor):
    """Preenche react-select criavel. Retorna True se preencheu."""
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

        # Tenta opcao existente (sem "Criar")
        for op in opcoes:
            try:
                t = op.inner_text().strip()
                if valor.lower() in t.lower() and not re.search(r"criar|create", t, re.I):
                    op.click(timeout=3000)
                    page.wait_for_timeout(300)
                    return True
            except Exception:
                pass

        # Tenta opcao "Criar X"
        for op in opcoes:
            try:
                t = op.inner_text().strip()
                if re.search(r"criar|create", t, re.I):
                    op.click(timeout=3000)
                    page.wait_for_timeout(300)
                    return True
            except Exception:
                pass

        # Fallback: Enter
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        return True
    except Exception as e:
        log(f"    preencher_creatable #{input_id} erro: {e}")
        return False


def criar_registro(page, titulo, provedor, carga_hhmmss, data_term_iso):
    """Cria 1 registro. Retorna True se criou com sucesso."""
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/records/new?in_use_mode_layout=true",
        wait_until="domcontentloaded", timeout=25000
    )
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Provedor
    preencher_creatable(page, "react-select-2-input", provedor)
    page.wait_for_timeout(200)

    # Conteudo
    preencher_creatable(page, "react-select-3-input", titulo)
    page.wait_for_timeout(200)

    # Tipo experiencia — seleciona primeiro disponivel sem digitar
    try:
        inp = page.locator("#react-select-4-input")
        inp.scroll_into_view_if_needed()
        inp.click(timeout=3000)
        page.wait_for_timeout(500)
        opcoes = page.locator("[class*='__option']").all()
        if opcoes:
            opcoes[0].click(timeout=3000)
        else:
            # Nada disponivel — cria "Curso"
            inp.fill("Curso")
            page.wait_for_timeout(600)
            opcoes2 = page.locator("[class*='__option']").all()
            if opcoes2:
                opcoes2[0].click(timeout=3000)
            else:
                page.keyboard.press("Enter")
        page.wait_for_timeout(200)
    except Exception as e:
        log(f"    tipo exp erro: {e}")

    # Categorias — seleciona primeiro disponivel
    try:
        inp = page.locator("#react-select-5-input")
        inp.scroll_into_view_if_needed()
        inp.click(timeout=3000)
        page.wait_for_timeout(500)
        opcoes = page.locator("[class*='__option']").all()
        if opcoes:
            opcoes[0].click(timeout=3000)
        page.wait_for_timeout(200)
    except Exception as e:
        log(f"    cat erro: {e}")

    # Carga horaria
    try:
        carga = page.locator("#workload_seconds")
        carga.scroll_into_view_if_needed()
        carga.fill(carga_hhmmss)
    except Exception:
        pass

    # Data de termino
    try:
        dt = page.locator("#endDate")
        dt.scroll_into_view_if_needed()
        dt.fill(data_term_iso)
        page.wait_for_timeout(200)
    except Exception:
        pass

    # Salva
    try:
        btn = page.get_by_role("button", name=re.compile(
            r"^Salvar$|^Enviar para aprovação$", re.I)).first
        if btn.count() == 0:
            btn = page.locator("button[type='submit']").first
        if btn.count() > 0 and btn.is_visible(timeout=2000):
            btn.scroll_into_view_if_needed()
            btn.click(timeout=5000)
            # Aguarda redirect com timeout generoso
            try:
                page.wait_for_url(
                    re.compile(r"/records\?|/records$"),
                    timeout=10000
                )
                return True
            except Exception:
                # Verifica URL manualmente
                page.wait_for_timeout(3000)
                if "/records" in page.url and "/records/new" not in page.url:
                    return True
                # Verifica toast
                return page.get_by_text(
                    re.compile(r"sucesso|adicionado|enviado|criado", re.I)
                ).count() > 0
    except Exception as e:
        log(f"    salvar erro: {e}")

    return False


# ─── TC3: Usuario novo via admin ───────────────────────────────────────────────

def run_tc3(page_admin):
    log("\n=== TC3: Empty state (usuario novo) ===")
    evids = []
    import os
    novo_email = f"qa11tc3{os.getpid()}@mailnull.com"
    novo_senha = "TwygoQA123!"

    log(f"  Criando usuario: {novo_email}")

    # Navega para Usuarios
    page_admin.goto(
        f"{BASE_URL}/o/{ORG_ID}/users",
        wait_until="domcontentloaded", timeout=25000
    )
    try:
        page_admin.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page_admin.wait_for_timeout(2000)
    tw.dispensar_nps(page_admin)

    # Clica em Adicionar
    btn = page_admin.locator("button:has-text('Adicionar')").first
    if btn.count() == 0 or not btn.is_visible(timeout=2000):
        btn = page_admin.locator("a[href*='/users/new']").first
    btn.click(timeout=5000)
    page_admin.wait_for_timeout(2000)
    tw.dispensar_nps(page_admin)
    log(f"  Form usuario URL: {page_admin.url[:60]}")

    # Preenche e-mail — campo com placeholder "Ex: joao@email.com"
    email_ok = False
    try:
        campo_email = page_admin.locator(
            "input[placeholder*='joao@'], input[placeholder*='email.com']"
        ).first
        if campo_email.count() == 0:
            campo_email = page_admin.locator("input[type='email']").first
        if campo_email.count() > 0 and campo_email.is_visible(timeout=2000):
            campo_email.scroll_into_view_if_needed()
            campo_email.click(timeout=2000)
            campo_email.fill(novo_email)
            page_admin.wait_for_timeout(300)
            email_ok = True
            log(f"  Email preenchido: {campo_email.input_value()}")
    except Exception as e:
        log(f"  Email erro: {e}")

    # Nome
    try:
        nome = page_admin.locator("input[placeholder*='João'], input[placeholder*='joao'], input[placeholder*='Nome'], input[placeholder*='nome']").first
        if nome.count() == 0:
            # Pega pelo label
            nome = page_admin.get_by_label(re.compile(r"^Nome\s*\*?$", re.I)).first
        if nome.count() > 0 and nome.is_visible(timeout=1000):
            nome.fill("QA11TC3")
    except Exception:
        pass

    # Sobrenome
    try:
        sob = page_admin.get_by_label(re.compile(r"^Sobrenome\s*\*?$", re.I)).first
        if sob.count() > 0 and sob.is_visible(timeout=1000):
            sob.fill("Empty")
    except Exception:
        pass

    tw.snap(page_admin, EVID, "fechamento_tc3_form_novo_usuario")
    evids.append("fechamento_tc3_form_novo_usuario.png")

    # Salva
    criado = False
    try:
        btn_s = page_admin.get_by_role("button", name=re.compile(
            r"Salvar|Criar|Convidar|Enviar|Adicionar", re.I)).first
        if btn_s.count() > 0 and btn_s.is_visible(timeout=2000):
            btn_s.click(timeout=5000)
            # Aguarda redirect para /users ou sucesso
            try:
                page_admin.wait_for_url(
                    re.compile(r"/users(?!/new)"),
                    timeout=8000
                )
                criado = True
            except Exception:
                page_admin.wait_for_timeout(3000)
                if "/users/new" not in page_admin.url:
                    criado = True
            log(f"  Criado: {criado}, URL: {page_admin.url[:60]}")
            tw.snap(page_admin, EVID, "fechamento_tc3_apos_criar_usuario")
    except Exception as e:
        log(f"  Salvar usuario erro: {e}")

    if not criado or not email_ok:
        falhou(3, evids,
               f"criacao de usuario falhou (email_ok={email_ok}, criado={criado})")
        return

    # Login como usuario novo em pagina separada do mesmo contexto
    ctx = page_admin.context
    page_novo = ctx.new_page()
    try:
        # Logout primeiro para garantir sessao limpa nesta aba
        page_novo.goto(
            f"{BASE_URL}/users/sign_out",
            wait_until="domcontentloaded", timeout=15000
        )
        page_novo.wait_for_timeout(1000)

        page_novo.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
        try:
            page_novo.wait_for_selector("#user_email", timeout=10000)
        except Exception:
            log("  Tela de login nao carregou")
            falhou(3, evids, "tela de login nao carregou na aba nova")
            return

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
        log(f"  Login novo usuario: ok={login_ok}, URL={page_novo.url[:60]}")
        tw.snap(page_novo, EVID, "fechamento_tc3_login_novo_usuario")

        if not login_ok:
            # Pode ser politica de senha — tenta com a senha padrao
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
                   f"login com usuario novo falhou ({novo_email})")
            return

        # Navega para Meu historico
        url_hist = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
        page_novo.goto(url_hist, wait_until="domcontentloaded", timeout=25000)
        try:
            page_novo.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page_novo.wait_for_timeout(2500)
        tw.dispensar_nps(page_novo)
        tw.snap(page_novo, EVID, "fechamento_tc3_empty")
        evids.append("fechamento_tc3_empty.png")

        log(f"  Meu historico URL: {page_novo.url[:60]}")

        # Passo 1: mensagem exata
        msg_exata = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
        has_empty = page_novo.get_by_text(msg_exata).count() > 0
        rows = page_novo.locator("table tbody tr").count()
        log(f"  Mensagem empty state: {has_empty}, linhas: {rows}")

        # Passo 2: 4 KPI cards com 0
        kpi_labels = ["Emitidos", "Expirados", "Pendentes", "Recusados"]
        kpi_found = {}
        kpi_values = {}

        for label in kpi_labels:
            try:
                card = page_novo.locator(
                    "[class*='stat'], [class*='kpi'], [class*='card'], "
                    "[class*='chakra-stat'], [class*='Stat']"
                ).filter(has_text=label).first
                if card.count() > 0:
                    kpi_found[label] = True
                    nums = re.findall(r'\b(\d+)\b', card.inner_text())
                    kpi_values[label] = int(nums[0]) if nums else None
                else:
                    kpi_found[label] = False
                    kpi_values[label] = None
            except Exception as e:
                kpi_found[label] = False
                kpi_values[label] = None

        log(f"  KPIs encontrados: {kpi_found}")
        log(f"  KPIs valores: {kpi_values}")

        tw.snap(page_novo, EVID, "fechamento_tc3_kpis")
        evids.append("fechamento_tc3_kpis.png")

        all_4_found = all(kpi_found.get(l, False) for l in kpi_labels)
        any_nonzero = any(kpi_values.get(l, 0) not in (0, None) for l in kpi_labels)

        if has_empty and rows == 0 and all_4_found and not any_nonzero:
            passou(3, evids,
                   f"mensagem exata presente; 0 linhas; 4 KPIs=0 ({kpi_values}); "
                   f"email={novo_email}")
        elif not has_empty and rows == 0:
            falhou(3, evids,
                   f"tabela vazia mas mensagem exata NAO encontrada")
        elif not all_4_found:
            missing = [l for l in kpi_labels if not kpi_found.get(l, False)]
            falhou(3, evids,
                   f"msg={has_empty}; KPIs ausentes: {missing}")
        elif any_nonzero:
            falhou(3, evids,
                   f"KPIs presentes mas nao zerados: {kpi_values}")
        else:
            falhou(3, evids,
                   f"has_empty={has_empty}, rows={rows}, kpi={kpi_values}")
    finally:
        page_novo.close()


# ─── Seed 26+ registros ────────────────────────────────────────────────────────

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
    ("QA11-F2-Extra-DevOps",       "Alura",             "22:00:00", "2025-07-01"),
    ("QA11-F2-Extra-GraphQL",      "Udemy",             "10:00:00", "2025-07-10"),
    ("QA11-F2-Extra-Terraform",    "Coursera",          "16:00:00", "2025-07-15"),
]


def semear(page):
    """Semeia registros ate ter >= 26 (ja tem alguns existentes). Retorna total semeado."""
    log("\n=== Semeando registros (meta: >= 26 total) ===")

    ir_meu_historico(page)
    total_atual = page.locator("table tbody tr").count()
    log(f"  Total inicial visivel: {total_atual}")

    # Se ja tem 25+ visiveis, pode ja estar paginado (pagina mostra 25 max)
    if total_atual >= 25:
        log("  Ja tem 25+ linhas — provavelmente ja tem paginacao. Pulando seed.")
        return 0, total_atual

    semeados = 0
    falhas = 0
    META = 26  # minimo absoluto para paginar (25 por pagina + 1 na pag 2)

    for i, (titulo, provedor, carga, data) in enumerate(TITULOS):
        if total_atual + semeados >= META:
            log(f"  Meta {META} atingida: {total_atual + semeados} estimado")
            break

        log(f"  [{i+1:02d}] {titulo}")
        ok = criar_registro(page, titulo, provedor, carga, data)

        if ok:
            semeados += 1
            log(f"    OK #{semeados}")
        else:
            falhas += 1
            log(f"    FALHOU")
            # Pausa e tenta de novo uma vez
            page.wait_for_timeout(1000)
            ok2 = criar_registro(page, f"{titulo}-v2", provedor, carga, data)
            if ok2:
                semeados += 1
                log(f"    OK no retry #{semeados}")
            else:
                log(f"    Retry tambem falhou")

    # Verifica total final
    ir_meu_historico(page)
    page.wait_for_timeout(1500)
    rows_visivel = page.locator("table tbody tr").count()
    tw.snap(page, EVID, "fechamento_tc11_lista_pos_semeia")
    log(f"  Semeados: {semeados}, falhas: {falhas}, visivel: {rows_visivel}")
    return semeados, rows_visivel


# ─── TC11: Paginacao ───────────────────────────────────────────────────────────

def run_tc11(page):
    log("\n=== TC11: Paginacao 25/50/100 ===")
    evids = []
    ir_meu_historico(page)

    rows_p1 = page.locator("table tbody tr").count()
    log(f"  Linhas pagina 1: {rows_p1}")
    tw.snap(page, EVID, "fechamento_tc11_pag1")
    evids.append("fechamento_tc11_pag1.png")

    if rows_p1 < 25:
        falhou(11, evids,
               f"apenas {rows_p1} linhas na pagina 1 — precisa >= 26 registros para paginar")
        return

    # Verifica controles de paginacao
    # O screenshot do gate mostrou: botoes << < 1 > >> e dropdown "25 por pagina"
    pag_next = page.locator("[aria-label*='Próxima' i], [aria-label*='next' i]").first
    if pag_next.count() == 0:
        # Tenta pelo botao ">>"
        pag_next = page.locator("button").filter(has_text=re.compile(r"^>$|^›$")).first
    # Tenta por posicao — botao apos "1"
    if pag_next.count() == 0:
        pag_buttons = page.locator("nav button, [class*='pagination'] button").all()
        log(f"  Botoes paginacao: {[b.inner_text()[:10] for b in pag_buttons[:8]]}")

    # O gate mostrou "25 por página" com dropdown chevron — provavelmente um <select>
    per_page_select = None
    for sel in [
        "select",
        "nav select",
        "[class*='pagination'] select",
        "[class*='per-page'] select",
    ]:
        try:
            s = page.locator(sel).first
            if s.count() > 0 and s.is_visible(timeout=1500):
                per_page_select = s
                log(f"  Select por-pagina via: {sel}")
                break
        except Exception:
            pass

    # Verifica texto "por pagina"
    por_pag_txt = page.get_by_text(re.compile(r"por página|per page", re.I)).first
    log(f"  Controles: next={pag_next.count()>0}, select={per_page_select is not None}, "
        f"por_pag_txt={por_pag_txt.count()>0}")

    tw.snap(page, EVID, "fechamento_tc11_controles")
    evids.append("fechamento_tc11_controles.png")

    has_pag = pag_next.count() > 0 or per_page_select is not None or por_pag_txt.count() > 0
    default_25 = rows_p1 == 25

    # Passo 2: proxima pagina
    pagina2_ok = False
    rows_p2 = 0
    if pag_next.count() > 0 and pag_next.is_visible(timeout=1500):
        try:
            pag_next.click(timeout=5000)
            page.wait_for_timeout(2000)
            rows_p2 = page.locator("table tbody tr").count()
            log(f"  Pagina 2: {rows_p2} linhas")
            tw.snap(page, EVID, "fechamento_tc11_pag2")
            evids.append("fechamento_tc11_pag2.png")
            pagina2_ok = rows_p2 > 0
        except Exception as e:
            log(f"  Erro pag2: {e}")
    else:
        # Tenta clicar no botao ">" (proximo)
        try:
            pag_prox = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const b = btns.find(b => b.innerText.trim() === '>' || b.getAttribute('aria-label')?.includes('Próxima') || b.getAttribute('aria-label')?.includes('next'));
                if (b) { b.click(); return true; }
                return false;
            }""")
            if pag_prox:
                page.wait_for_timeout(2000)
                rows_p2 = page.locator("table tbody tr").count()
                log(f"  Pagina 2 (via JS): {rows_p2}")
                tw.snap(page, EVID, "fechamento_tc11_pag2")
                evids.append("fechamento_tc11_pag2.png")
                pagina2_ok = rows_p2 > 0
        except Exception as e:
            log(f"  Erro pag2 JS: {e}")

    # Volta para pagina 1
    try:
        page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(b => b.innerText.trim() === '<<' || b.innerText.trim() === '«' || b.getAttribute('aria-label')?.includes('primeira') || b.getAttribute('aria-label')?.includes('first'));
            if (b) b.click();
        }""")
        page.wait_for_timeout(1000)
    except Exception:
        ir_meu_historico(page)

    # Passo 3: 50 por pagina
    pg50_ok = False
    rows_50 = 0
    if per_page_select:
        try:
            per_page_select.select_option("50")
            page.wait_for_timeout(2000)
            rows_50 = page.locator("table tbody tr").count()
            log(f"  50/pag: {rows_50} linhas")
            tw.snap(page, EVID, "fechamento_tc11_50pag")
            evids.append("fechamento_tc11_50pag.png")
            pg50_ok = True
        except Exception as e:
            log(f"  50/pag erro (select): {e}")
    else:
        # Tenta via JS diretamente no select
        try:
            result = page.evaluate("""() => {
                const selects = Array.from(document.querySelectorAll('select'));
                for (const s of selects) {
                    const opts = Array.from(s.options).map(o => o.value);
                    if (opts.includes('50') || opts.includes('50')) {
                        s.value = '50';
                        s.dispatchEvent(new Event('change', {bubbles: true}));
                        return 'ok';
                    }
                }
                return 'no_select';
            }""")
            log(f"  50/pag JS: {result}")
            if result == 'ok':
                page.wait_for_timeout(2000)
                rows_50 = page.locator("table tbody tr").count()
                log(f"  50/pag (JS): {rows_50} linhas")
                tw.snap(page, EVID, "fechamento_tc11_50pag")
                evids.append("fechamento_tc11_50pag.png")
                pg50_ok = True
        except Exception as e:
            log(f"  50/pag JS erro: {e}")

    # Passo 4: 100 por pagina
    pg100_ok = False
    rows_100 = 0
    if per_page_select and pg50_ok:
        try:
            per_page_select.select_option("100")
            page.wait_for_timeout(2000)
            rows_100 = page.locator("table tbody tr").count()
            log(f"  100/pag: {rows_100} linhas")
            tw.snap(page, EVID, "fechamento_tc11_100pag")
            evids.append("fechamento_tc11_100pag.png")
            pg100_ok = True
        except Exception as e:
            log(f"  100/pag erro: {e}")
    elif pg50_ok:
        try:
            result = page.evaluate("""() => {
                const selects = Array.from(document.querySelectorAll('select'));
                for (const s of selects) {
                    const opts = Array.from(s.options).map(o => o.value);
                    if (opts.includes('100')) {
                        s.value = '100';
                        s.dispatchEvent(new Event('change', {bubbles: true}));
                        return 'ok';
                    }
                }
                return 'no_select';
            }""")
            if result == 'ok':
                page.wait_for_timeout(2000)
                rows_100 = page.locator("table tbody tr").count()
                tw.snap(page, EVID, "fechamento_tc11_100pag")
                evids.append("fechamento_tc11_100pag.png")
                pg100_ok = True
        except Exception as e:
            log(f"  100/pag JS erro: {e}")

    log(f"\n  Resumo TC11:")
    log(f"    pag1={rows_p1} linhas (default 25: {default_25})")
    log(f"    has_paginacao: {has_pag}")
    log(f"    pag2: {pagina2_ok} ({rows_p2} linhas)")
    log(f"    50/pag: {pg50_ok} ({rows_50} linhas)")
    log(f"    100/pag: {pg100_ok} ({rows_100} linhas)")

    if default_25 and has_pag and pagina2_ok and pg50_ok and pg100_ok:
        passou(11, evids,
               f"pag1=25; pag2={rows_p2}; 50/pag={rows_50}; 100/pag={rows_100}")
    elif default_25 and has_pag and pagina2_ok and pg50_ok:
        falhou(11, evids,
               f"pag1=25 OK, pag2 OK, 50/pag OK ({rows_50}), "
               f"MAS 100/pag NAO funcionou (rows={rows_100})")
    elif default_25 and has_pag and pagina2_ok:
        falhou(11, evids,
               f"pag1=25 OK, pag2 OK, MAS dropdown 50/100 NAO funcionou")
    elif default_25 and has_pag:
        falhou(11, evids,
               f"pag1=25 OK, controles presentes, MAS pag2 NAO funcionou ({rows_p2})")
    elif not default_25 and rows_p1 >= 25:
        falhou(11, evids,
               f"pag1 mostra {rows_p1} linhas (esperava default=25); pag2={pagina2_ok}")
    else:
        falhou(11, evids,
               f"pag1={rows_p1} (precisa 25); has_pag={has_pag}")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("fechamento_qa11_final.py")
    log(f"Org: {BASE_URL} / ID: {ORG_ID}")
    log("=" * 60)

    # === BROWSER 1: Admin — TC3 ===
    with tw.sync_playwright() as p1:
        browser_adm, ctx_adm, page_adm = tw.nova_pagina(p1)
        try:
            log("\n--- TC3 (admin cria usuario) ---")
            login_admin(page_adm)
            run_tc3(page_adm)
        finally:
            ctx_adm.close()
            browser_adm.close()

    # === BROWSER 2: Aluno (dante) — Seed + TC11 ===
    with tw.sync_playwright() as p2:
        browser_alu, ctx_alu, page_alu = tw.nova_pagina(p2)
        try:
            log("\n--- Seed + TC11 (aluno dante) ---")
            login_aluno(page_alu)
            semeados, rows_visivel = semear(page_alu)
            log(f"  Semeados: {semeados}, visivel: {rows_visivel}")
            run_tc11(page_alu)
        finally:
            ctx_alu.close()
            browser_alu.close()

    log("\n" + "=" * 60)
    log("RESULTADOS FINAIS:")
    for tc, r in sorted(RESULTADOS.items()):
        log(f"  TC{tc}: {r['veredito']} — {r['obs']}")
    log("=" * 60)


if __name__ == "__main__":
    main()
