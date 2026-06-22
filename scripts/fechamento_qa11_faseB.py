"""fechamento_qa11_faseB.py — TC3 (usuario novo) + TC11 (paginacao) na org registrosf2.

Fase B (roda apos Fase A):
- TC3: cria usuario novo via admin, loga como ele, valida empty state.
- Semeia >= 26 registros com dante (para TC11).
- TC11: valida paginacao 25/50/100 com os registros semeados.

Org: registrosf2.stage.twygoead.com (org_id 37079)
Admin: dante.tavares@twygo.com / 123456
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

# ─── Constantes da org nova ────────────────────────────────────────────────────
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


# ─── Login helpers ─────────────────────────────────────────────────────────────

def login_admin(page):
    """Loga como admin e faz switch para perfil admin."""
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
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
        raise SystemExit("Login Admin falhou.")

    # Switch para admin
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded", timeout=30000
    )
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    log(f"  Admin logado: {page.url[:70]}")


def login_aluno(page, email, senha):
    """Loga como Aluno (sem switch admin)."""
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", email)
    page.fill("#user_password", senha)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)

    if "/users/login" in page.url:
        log(f"  Login falhou para {email}")
        return False
    log(f"  Aluno logado ({email}): {page.url[:60]}")
    return True


def ir_meu_historico(page):
    url = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)
    try:
        page.wait_for_selector("table, [class*='stat'], [class*='kpi']", timeout=8000)
    except Exception:
        pass


# ─── TC3: Criar usuario novo + validar empty state ─────────────────────────────

def criar_usuario_novo(page_admin):
    """Cria usuario novo via admin. Retorna (email, senha) ou (None, None)."""
    import os
    novo_email = f"qa11empty{os.getpid()}@mailnull.com"
    novo_senha = "TwygoQA2025"

    log(f"\n=== TC3: Criando usuario novo: {novo_email} ===")

    usuarios_url = f"{BASE_URL}/o/{ORG_ID}/users"
    page_admin.goto(usuarios_url, wait_until="domcontentloaded", timeout=25000)
    try:
        page_admin.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page_admin.wait_for_timeout(2000)
    tw.dispensar_nps(page_admin)
    tw.snap(page_admin, EVID, "fechamento_tc3_admin_usuarios")

    # Botao "+ Adicionar" na pagina de usuarios (nao o link "Segurança" da sidebar)
    # Seletores em ordem de especificidade
    btn_novo = None
    for sel in [
        "a[href*='/users/new']",
        "button:has-text('Adicionar')",
        "a:has-text('Adicionar')",
        "[data-testid*='add'], [data-testid*='new']",
    ]:
        try:
            el = page_admin.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=1500):
                btn_novo = el
                log(f"  Botao Adicionar encontrado via: {sel}")
                break
        except Exception:
            pass

    if not btn_novo:
        # Fallback: botao com texto "Adicionar" na area principal (nao sidebar)
        try:
            btn_novo = page_admin.locator("main button, .content button, [class*='container'] button").filter(
                has_text=re.compile(r"Adicionar", re.I)
            ).first
            if btn_novo.count() == 0 or not btn_novo.is_visible(timeout=1000):
                btn_novo = None
        except Exception:
            pass

    if not btn_novo:
        log("  Botao de criar usuario nao encontrado")
        return None, None

    btn_novo.click(timeout=5000)
    page_admin.wait_for_timeout(2000)
    tw.dispensar_nps(page_admin)
    tw.snap(page_admin, EVID, "fechamento_tc3_form_usuario")
    log(f"  URL apos click: {page_admin.url[:60]}")

    criado = False
    try:
        # Nome
        for lbl in ["Nome", "Name", "First Name", "first_name"]:
            campo = page_admin.get_by_label(re.compile(rf"^{lbl}$", re.I)).first
            if campo.count() == 0:
                campo = page_admin.locator(f"input[name*='first'], input[name*='nome'], input[placeholder*='{lbl}']").first
            if campo.count() > 0 and campo.is_visible(timeout=1000):
                campo.fill("QA11")
                break

        # Sobrenome
        for lbl in ["Sobrenome", "Last Name", "Surname"]:
            campo = page_admin.get_by_label(re.compile(rf"^{lbl}$", re.I)).first
            if campo.count() == 0:
                campo = page_admin.locator("input[name*='last'], input[name*='sobrenome']").first
            if campo.count() > 0 and campo.is_visible(timeout=1000):
                campo.fill("EmptyTest")
                break

        # E-mail — campo tem placeholder "Ex: joao@email.com"
        email_filled = False
        for sel in [
            "input[placeholder*='joao@'], input[placeholder*='email'], input[placeholder*='@']",
            "input[type='email']",
            "input[name='email']", "input[name*='email']",
            "input[id*='email'], input[id*='Email']",
        ]:
            try:
                campos = page_admin.locator(sel).all()
                for campo in campos:
                    if campo.is_visible(timeout=500):
                        campo.click(timeout=2000)
                        campo.fill(novo_email)
                        page_admin.wait_for_timeout(300)
                        email_filled = True
                        log(f"  Email preenchido via: {sel}")
                        break
            except Exception:
                pass
            if email_filled:
                break

        if not email_filled:
            # Fallback: primeiro input sem valor na area do form
            all_inputs = page_admin.locator("form input:visible, main input:visible").all()
            for inp in all_inputs:
                try:
                    if inp.get_attribute("type") not in ("hidden", "submit", "checkbox"):
                        val = inp.input_value()
                        if not val:  # vazio
                            inp.click(timeout=1000)
                            inp.fill(novo_email)
                            page_admin.wait_for_timeout(200)
                            # Verifica se aceitou
                            if inp.input_value() == novo_email:
                                email_filled = True
                                log("  Email preenchido via fallback input vazio")
                                break
                except Exception:
                    pass

        # Senha (pode nao ter — alguns flows mandam email de boas-vindas)
        for sel in ["input[type='password']", "input[name*='password']", "input[name*='senha']"]:
            campos_senha = page_admin.locator(sel).all()
            for cs in campos_senha:
                try:
                    if cs.is_visible(timeout=500):
                        cs.fill(novo_senha)
                except Exception:
                    pass

        tw.snap(page_admin, EVID, "fechamento_tc3_form_preenchido")

        # Salva
        btn_s = page_admin.get_by_role("button", name=re.compile(
            r"Salvar|Criar|Convidar|Enviar|Send|Adicionar", re.I)).first
        if btn_s.count() > 0 and btn_s.is_visible(timeout=2000):
            btn_s.click(timeout=5000)
            page_admin.wait_for_timeout(3000)
            tw.dispensar_nps(page_admin)

            # Verifica sucesso
            toast_ok = page_admin.get_by_text(
                re.compile(r"criado|salvo|adicionado|enviado|convidado|sucesso", re.I)
            ).count() > 0
            redirect_ok = "/users/" in page_admin.url and "/new" not in page_admin.url
            criado = toast_ok or redirect_ok
            log(f"  Criado: {criado} (toast={toast_ok}, redirect={redirect_ok})")
            log(f"  URL apos salvar: {page_admin.url[:60]}")
            tw.snap(page_admin, EVID, "fechamento_tc3_apos_criar")
    except Exception as e:
        log(f"  Erro ao criar usuario: {e}")

    if criado:
        return novo_email, novo_senha
    return None, None


def run_tc3(page_admin):
    log("\n=== TC3: Empty state (usuario novo) ===")
    evids = []

    novo_email, novo_senha = criar_usuario_novo(page_admin)
    if not novo_email:
        falhou(3, ["fechamento_tc3_admin_usuarios.png"],
               "nao foi possivel criar usuario novo via admin")
        return

    # Abre nova pagina para logar como usuario novo
    ctx = page_admin.context
    page_novo = ctx.new_page()
    try:
        login_ok = login_aluno(page_novo, novo_email, novo_senha)

        if not login_ok:
            # Pode ser que a senha nao foi aceita (politica de senha fraca)
            # Tenta com senha mais forte
            log("  Tentando login com senha alternativa...")
            login_ok = login_aluno(page_novo, novo_email, "TwygoQA2025!")

        if not login_ok:
            # Verifica se ha redirect de troca de senha forcada
            if "password" in page_novo.url.lower() or "change" in page_novo.url.lower():
                log("  Troca de senha forcada detectada")
                try:
                    campos = page_novo.locator("input[type='password']").all()
                    nova_s = "TwygoQA123!"
                    for cs in campos:
                        if cs.is_visible(timeout=500):
                            cs.fill(nova_s)
                    btn = page_novo.get_by_role("button", name=re.compile(r"Salvar|Confirmar", re.I)).first
                    if btn.count() > 0:
                        btn.click(timeout=5000)
                        page_novo.wait_for_timeout(3000)
                        tw.dispensar_nps(page_novo)
                        novo_senha = nova_s
                        login_ok = "/users/login" not in page_novo.url
                        log(f"  Apos troca senha: login_ok={login_ok}")
                except Exception as ex:
                    log(f"  Erro troca senha: {ex}")

        if not login_ok:
            falhou(3, ["fechamento_tc3_apos_criar.png"],
                   f"login com usuario novo falhou ({novo_email})")
            return

        # Navega para Meu historico
        ir_meu_historico(page_novo)
        tw.snap(page_novo, EVID, "fechamento_tc3_empty")
        evids.append("fechamento_tc3_empty.png")

        # Verifica URL e heading
        log(f"  URL Meu historico: {page_novo.url[:60]}")

        # Passo 1: mensagem exata
        msg_exata = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
        has_empty = page_novo.get_by_text(msg_exata).count() > 0
        rows = page_novo.locator("table tbody tr").count()
        log(f"  Mensagem empty state: {has_empty}, linhas tabela: {rows}")

        # Passo 2: 4 KPI cards com 0
        kpi_labels = ["Emitidos", "Expirados", "Pendentes", "Recusados"]
        kpi_found = {}
        kpi_values = {}

        for label in kpi_labels:
            try:
                # Busca pelo card que contem o label
                card = page_novo.locator(
                    "[class*='stat'], [class*='kpi'], [class*='card'], [class*='Stat'], "
                    "[class*='chakra-stat']"
                ).filter(has_text=label).first
                if card.count() > 0:
                    kpi_found[label] = True
                    card_text = card.inner_text()
                    nums = re.findall(r'\b(\d+)\b', card_text)
                    kpi_values[label] = int(nums[0]) if nums else None
                else:
                    # Tenta encontrar o numero proximo ao label
                    kpi_found[label] = False
                    kpi_values[label] = None
            except Exception as e:
                kpi_found[label] = False
                kpi_values[label] = None
                log(f"  KPI '{label}' erro: {e}")

        log(f"  KPI encontrados: {kpi_found}")
        log(f"  KPI valores: {kpi_values}")

        # Screenshot adicional focado nos KPIs
        tw.snap(page_novo, EVID, "fechamento_tc3_kpis")
        evids.append("fechamento_tc3_kpis.png")

        all_4_found = all(kpi_found.get(l, False) for l in kpi_labels)
        any_nonzero = any(kpi_values.get(l, 0) not in (0, None) for l in kpi_labels)

        # Veredito
        if has_empty and rows == 0 and all_4_found and not any_nonzero:
            passou(3, evids,
                   f"mensagem exata presente; 0 linhas; 4 KPIs visiveis com 0 "
                   f"({kpi_values}); email={novo_email}")
        elif not has_empty and rows == 0:
            falhou(3, evids,
                   f"tabela vazia mas mensagem exata NAO encontrada "
                   f"('{msg_exata}')")
        elif not all_4_found:
            missing = [l for l in kpi_labels if not kpi_found.get(l, False)]
            if has_empty:
                falhou(3, evids,
                       f"mensagem empty state OK, mas KPIs ausentes: {missing}")
            else:
                falhou(3, evids,
                       f"mensagem NAO encontrada E KPIs ausentes: {missing}")
        elif any_nonzero:
            falhou(3, evids,
                   f"KPIs presentes mas algum != 0: {kpi_values}")
        else:
            falhou(3, evids,
                   f"has_empty={has_empty}, rows={rows}, kpi_found={kpi_found}, "
                   f"kpi_vals={kpi_values}")
    finally:
        page_novo.close()


# ─── Semear registros com Aluno (dante) ────────────────────────────────────────

MASSA_SEED = [
    # (titulo, provedor, tipo_exp, carga_h_hhmmss, data_term_iso, data_val_iso)
    ("QA11-F2-Alura-Python",        "Alura",             "Curso",     "10:00:00", "2025-01-15", None),
    ("QA11-F2-Alura-Django",        "Alura",             "Curso",     "15:00:00", "2025-02-10", None),
    ("QA11-F2-Alura-Docker",        "Alura",             "Workshop",  "08:00:00", "2025-03-05", "2026-03-05"),
    ("QA11-F2-Alura-Git",           "Alura",             "Curso",     "06:00:00", "2025-04-12", None),
    ("QA11-F2-Alura-React",         "Alura",             "Trilha",    "18:00:00", "2025-05-10", "2026-05-10"),
    ("QA11-F2-Coursera-ML",         "Coursera",          "Curso",     "40:00:00", "2025-01-15", None),
    ("QA11-F2-Coursera-DS",         "Coursera",          "Trilha",    "60:00:00", "2025-02-28", "2026-02-28"),
    ("QA11-F2-Coursera-TF",         "Coursera",          "Curso",     "30:00:00", "2025-03-15", None),
    ("QA11-F2-Coursera-NLP",        "Coursera",          "Aula",      "20:00:00", "2025-04-01", None),
    ("QA11-F2-Coursera-Agile",      "Coursera",          "Curso",     "15:00:00", "2025-04-10", "2026-04-10"),
    ("QA11-F2-FGV-Gestao",          "FGV",               "Curso",     "45:00:00", "2025-01-10", None),
    ("QA11-F2-FGV-Lideranca",       "FGV",               "Workshop",  "08:00:00", "2025-02-15", "2026-02-15"),
    ("QA11-F2-FGV-Financas",        "FGV",               "Curso",     "60:00:00", "2025-03-20", None),
    ("QA11-F2-FGV-MBA",             "FGV",               "Trilha",    "12:00:00", "2025-04-01", "2027-04-01"),
    ("QA11-F2-Udemy-Excel",         "Udemy",             "Curso",     "12:00:00", "2025-01-05", None),
    ("QA11-F2-Udemy-PowerBI",       "Udemy",             "Curso",     "16:00:00", "2025-02-10", "2026-02-10"),
    ("QA11-F2-Udemy-Node",          "Udemy",             "Curso",     "20:00:00", "2025-03-15", None),
    ("QA11-F2-USP-Estatistica",     "USP",               "Curso",     "60:00:00", "2025-01-10", None),
    ("QA11-F2-USP-Direito",         "USP",               "Palestra",  "04:00:00", "2025-04-01", None),
    ("QA11-F2-LI-Storytelling",     "LinkedIn Learning", "Palestra",  "02:00:00", "2025-01-05", None),
    ("QA11-F2-LI-Negociacao",       "LinkedIn Learning", "Workshop",  "04:00:00", "2025-02-10", None),
    ("QA11-F2-LI-Design",           "LinkedIn Learning", "Curso",     "06:00:00", "2025-03-01", "2026-03-01"),
    ("QA11-F2-LI-OKR",              "LinkedIn Learning", "Mentoria",  "03:00:00", "2025-03-15", None),
    ("QA11-F2-LI-Comunicacao",      "LinkedIn Learning", "Evento",    "02:00:00", "2025-04-01", None),
    ("QA11-F2-Alura-AWS",           "Alura",             "Curso",     "25:00:00", "2025-05-01", None),
    ("QA11-F2-Extra-React-Native",  "Alura",             "Curso",     "22:00:00", "2025-05-20", None),
    ("QA11-F2-Extra-TypeScript",    "Alura",             "Curso",     "14:00:00", "2025-06-01", None),
    ("QA11-F2-Extra-Kubernetes",    "Coursera",          "Curso",     "35:00:00", "2025-06-10", None),
    ("QA11-F2-Extra-SQL-Avancado",  "Udemy",             "Curso",     "18:00:00", "2025-06-15", None),
    ("QA11-F2-Extra-Scrum",         "FGV",               "Workshop",  "08:00:00", "2025-06-20", "2026-06-20"),
]


def preencher_creatable(page, input_id, valor):
    """Preenche react-select criavel pelo ID do input."""
    try:
        inp = page.locator(f"#{input_id}")
        if inp.count() == 0:
            return False
        inp.click(timeout=3000)
        page.wait_for_timeout(300)
        inp.fill(valor)
        page.wait_for_timeout(800)

        # Opções disponíveis
        opcoes = page.locator(
            "[class*='creatable-select-field__option'], [class*='__option']"
        ).all()

        for op in opcoes:
            try:
                t = op.inner_text().strip()
                if valor.lower() in t.lower() and "Criar" not in t and "criar" not in t:
                    op.click(timeout=3000)
                    page.wait_for_timeout(300)
                    return True
            except Exception:
                pass

        # Opção "Criar X"
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
        log(f"    creatable_select erro (#{input_id}): {e}")
        return False


def criar_registro(page, titulo, provedor, tipo_exp, carga_hhmmss, data_term_iso, data_val_iso=None):
    """Cria 1 registro via form /records/new. Retorna True se criou com sucesso."""
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/records/new?in_use_mode_layout=true",
        wait_until="domcontentloaded", timeout=25000
    )
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1500)
    tw.dispensar_nps(page)

    # Provedor
    prov_ok = preencher_creatable(page, "react-select-2-input", provedor)
    page.wait_for_timeout(200)

    # Conteudo/Titulo
    cont_ok = preencher_creatable(page, "react-select-3-input", titulo)
    page.wait_for_timeout(200)

    # Tipo de experiencia
    tipo_ok = False
    try:
        inp = page.locator("#react-select-4-input")
        if inp.count() > 0:
            inp.click(timeout=3000)
            page.wait_for_timeout(300)
            inp.fill(tipo_exp[:4])
            page.wait_for_timeout(500)
            opcoes = page.locator("[class*='creatable-select-field__option'], [class*='__option']").all()
            for op in opcoes:
                t = op.inner_text().strip()
                if tipo_exp.lower() in t.lower():
                    op.click(timeout=3000)
                    tipo_ok = True
                    break
            if not tipo_ok and opcoes:
                opcoes[0].click(timeout=3000)
                tipo_ok = True
            page.wait_for_timeout(200)
    except Exception:
        pass

    # Categorias (campo obrigatorio)
    cat_ok = False
    try:
        inp = page.locator("#react-select-5-input")
        if inp.count() > 0:
            inp.click(timeout=3000)
            page.wait_for_timeout(300)
            opcoes = page.locator("[class*='creatable-select-field__option'], [class*='__option']").all()
            if opcoes:
                opcoes[0].click(timeout=3000)
                cat_ok = True
            page.wait_for_timeout(200)
    except Exception:
        pass

    # Carga horaria (HH:MM:SS)
    try:
        carga_input = page.locator("#workload_seconds")
        if carga_input.count() > 0:
            carga_input.fill(carga_hhmmss)
    except Exception:
        pass

    # Data de termino (yyyy-mm-dd)
    try:
        data_end = page.locator("#endDate")
        if data_end.count() > 0:
            data_end.fill(data_term_iso)
            page.wait_for_timeout(150)
    except Exception:
        pass

    # Data de validade (opcional)
    if data_val_iso:
        try:
            data_exp = page.locator("#expirationDate")
            if data_exp.count() > 0:
                data_exp.fill(data_val_iso)
                page.wait_for_timeout(150)
        except Exception:
            pass

    # Salva
    enviar_ok = False
    try:
        btn = page.get_by_role("button", name=re.compile(r"^Salvar$|^Enviar para aprovação$", re.I)).first
        if btn.count() == 0:
            btn = page.locator("button[type='submit']").first
        if btn.count() > 0 and btn.is_visible(timeout=2000):
            btn.click(timeout=5000)
            page.wait_for_timeout(2500)
            tw.dispensar_nps(page)

            toasts = ["enviado para aprovação", "adicionado", "salvo", "criado", "sucesso"]
            for t in toasts:
                if page.get_by_text(re.compile(t, re.I)).count() > 0:
                    enviar_ok = True
                    break

            if not enviar_ok and "/records" in page.url and "/records/new" not in page.url:
                enviar_ok = True
    except Exception as e:
        log(f"    Salvar erro: {e}")

    return enviar_ok


def semear_registros(page):
    """Semeia registros ate ter >= 26 total (contando os 7 ja existentes)."""
    log("\n=== Semeando registros (Aluno dante) ===")
    semeados = 0
    falhas = 0

    # Conta atual
    ir_meu_historico(page)
    total_atual = page.locator("table tbody tr").count()
    # Também verifica paginação — se já tem 25+ linhas pode estar paginado
    pag_info = page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button, [aria-label]'));
        const textos = btns.map(b => b.innerText?.trim()).filter(t => t);
        return textos;
    }""")
    log(f"  Total inicial visivel: {total_atual}")
    log(f"  URL: {page.url[:60]}")

    # Precisa de pelo menos 26 registros totais para paginacao funcionar (25/pagina)
    # Ja tem 7 → semeia 19+ para chegar a 26+, mas vamos ao 30 para ter margem
    META = 30

    for i, (titulo, provedor, tipo_exp, carga_h, data_term, data_val) in enumerate(MASSA_SEED):
        if semeados + total_atual >= META:
            log(f"  Meta {META} atingida: {total_atual + semeados} total")
            break

        log(f"  [{i+1:02d}] {titulo} | {provedor}")
        ok = criar_registro(page, titulo, provedor, tipo_exp, carga_h, data_term, data_val)

        if ok:
            semeados += 1
            log(f"    OK (semeado #{semeados})")
        else:
            falhas += 1
            log(f"    FALHOU")

        # A cada 5 registros, verifica o total atual
        if semeados % 5 == 0:
            ir_meu_historico(page)
            total_atual = page.locator("table tbody tr").count()
            log(f"  Total visivel: {total_atual}")

    # Verifica total final
    ir_meu_historico(page)
    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "fechamento_tc11_lista_apos_semeia")

    # Total pode estar paginado — pega de API ou verifica indicador de paginacao
    rows_visivel = page.locator("table tbody tr").count()
    log(f"  Semeio: {semeados} OK, {falhas} falhas, visivel: {rows_visivel}")
    return semeados, rows_visivel


# ─── TC11: Paginacao ───────────────────────────────────────────────────────────

def run_tc11(page, rows_visivel):
    log("\n=== TC11: Paginacao 25/50/100 ===")
    evids = []
    ir_meu_historico(page)

    rows_p1 = page.locator("table tbody tr").count()
    log(f"  Linhas pagina 1: {rows_p1}")
    tw.snap(page, EVID, "fechamento_tc11_pag1")
    evids.append("fechamento_tc11_pag1.png")

    # Verifica paginacao disponivel (controles presentes)
    pag_controls = page.locator("nav[aria-label*='pag' i], [class*='pagination']").count()
    pag_next = page.locator(
        "[aria-label*='próxima' i], [aria-label*='next' i], [aria-label*='Next']"
    ).first

    # Tambem verifica o dropdown "X por pagina"
    dropdown_per_page = page.locator("select").filter(
        has_text=re.compile(r"25|50|100")
    ).first
    if dropdown_per_page.count() == 0:
        # Tenta por combobox/select com opcoes de paginacao
        dropdown_per_page = page.get_by_role("combobox").first

    por_pagina_texto = page.get_by_text(re.compile(r"por página|per page", re.I)).first

    log(f"  Controles: nav/pag_class={pag_controls}, next={pag_next.count()>0}, "
        f"dropdown={dropdown_per_page.count()>0}, por_pagina_txt={por_pagina_texto.count()>0}")

    tw.snap(page, EVID, "fechamento_tc11_controles")
    evids.append("fechamento_tc11_controles.png")

    # Se nao tem 25+ linhas e nao ha controles de paginacao, falha imediata
    if rows_p1 < 25 and pag_controls == 0 and pag_next.count() == 0:
        falhou(11, evids,
               f"apenas {rows_p1} linhas visiveis e sem controles de paginacao "
               f"(precisa >= 26 registros para paginar)")
        return

    # Passo 1: pagina default mostra 25 linhas + controle de paginacao com pagina 1
    default_25 = rows_p1 == 25
    has_pagination = pag_controls > 0 or pag_next.count() > 0 or por_pagina_texto.count() > 0
    log(f"  Pagina 1 tem 25 linhas: {default_25}, tem paginacao: {has_pagination}")

    # Passo 2: proxima pagina
    pagina2_ok = False
    rows_p2 = 0
    if pag_next.count() > 0:
        try:
            if pag_next.is_visible(timeout=2000):
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
        log("  Botao proxima pagina nao encontrado")

    # Volta para pagina 1 para testar dropdown
    try:
        pag_first = page.locator(
            "[aria-label*='primeira' i], [aria-label*='first' i], [aria-label*='First']"
        ).first
        if pag_first.count() > 0 and pag_first.is_visible(timeout=1000):
            pag_first.click(timeout=3000)
            page.wait_for_timeout(1000)
        else:
            # Volta pela URL
            ir_meu_historico(page)
    except Exception:
        ir_meu_historico(page)

    # Passo 3: selecionar 50 por pagina
    pg50_ok = False
    rows_50 = 0
    try:
        # Localiza o dropdown/select de por-pagina
        # O screenshot mostra "25 por página" com seta — provavelmente um <select>
        per_page_sel = page.locator("select").filter(
            has_text=re.compile(r"25")
        ).first
        if per_page_sel.count() == 0:
            per_page_sel = page.locator("[class*='per-page'] select, [class*='perPage'] select").first
        if per_page_sel.count() == 0:
            # Tenta qualquer select na area de paginacao
            per_page_sel = page.locator("nav select, [class*='pagination'] select").first
        if per_page_sel.count() == 0:
            # Ultimo recurso: qualquer select na pagina que tenha 25 como opcao
            for sel in page.locator("select").all():
                try:
                    if sel.inner_text().find("25") >= 0 or "25" in sel.evaluate("el => el.value"):
                        per_page_sel = sel
                        break
                except Exception:
                    pass

        if per_page_sel.count() > 0 and per_page_sel.is_visible(timeout=2000):
            log("  Dropdown por pagina encontrado (select)")
            per_page_sel.select_option("50")
            page.wait_for_timeout(2000)
            rows_50 = page.locator("table tbody tr").count()
            log(f"  Com 50/pag: {rows_50}")
            tw.snap(page, EVID, "fechamento_tc11_50pag")
            evids.append("fechamento_tc11_50pag.png")
            pg50_ok = True  # O fato de selecionar e a tabela responder e suficiente
        else:
            log("  Dropdown select nao encontrado — tenta botao/dropdown Chakra")
            # Tenta via button "25 por página" (padrao Chakra)
            btn_25 = page.locator("button").filter(has_text=re.compile(r"^25 por p", re.I)).first
            if btn_25.count() == 0:
                btn_25 = page.get_by_text(re.compile(r"25 por página", re.I)).first
            if btn_25.count() > 0:
                btn_25.click(timeout=3000)
                page.wait_for_timeout(500)
                opt_50 = page.locator("[role='option']").filter(has_text=re.compile(r"^50")).first
                if opt_50.count() == 0:
                    opt_50 = page.get_by_role("option", name=re.compile(r"^50")).first
                if opt_50.count() > 0:
                    opt_50.click(timeout=3000)
                    page.wait_for_timeout(2000)
                    rows_50 = page.locator("table tbody tr").count()
                    log(f"  Com 50/pag (Chakra): {rows_50}")
                    tw.snap(page, EVID, "fechamento_tc11_50pag")
                    evids.append("fechamento_tc11_50pag.png")
                    pg50_ok = True
                else:
                    log("  Opcao 50 nao encontrada no dropdown")
            else:
                log("  Nenhum controle de por-pagina encontrado")
    except Exception as e:
        log(f"  Erro 50/pag: {e}")

    # Passo 4: selecionar 100 por pagina
    pg100_ok = False
    rows_100 = 0
    try:
        # Re-localiza o select (pode ter mudado apos 50/pag)
        per_page_sel2 = page.locator("select").filter(
            has_text=re.compile(r"50")
        ).first
        if per_page_sel2.count() == 0:
            per_page_sel2 = page.locator("nav select, [class*='pagination'] select").first
        if per_page_sel2.count() == 0:
            per_page_sel2 = page.locator("select").first

        if per_page_sel2.count() > 0 and per_page_sel2.is_visible(timeout=2000):
            per_page_sel2.select_option("100")
            page.wait_for_timeout(2000)
            rows_100 = page.locator("table tbody tr").count()
            log(f"  Com 100/pag: {rows_100}")
            tw.snap(page, EVID, "fechamento_tc11_100pag")
            evids.append("fechamento_tc11_100pag.png")
            pg100_ok = True
        else:
            # Tenta via botao/dropdown (pode agora mostrar "50 por pagina")
            btn_50 = page.get_by_text(re.compile(r"50 por página", re.I)).first
            if btn_50.count() > 0:
                btn_50.click(timeout=3000)
                page.wait_for_timeout(500)
                opt_100 = page.locator("[role='option']").filter(has_text=re.compile(r"^100")).first
                if opt_100.count() == 0:
                    opt_100 = page.get_by_role("option", name=re.compile(r"^100")).first
                if opt_100.count() > 0:
                    opt_100.click(timeout=3000)
                    page.wait_for_timeout(2000)
                    rows_100 = page.locator("table tbody tr").count()
                    log(f"  Com 100/pag (Chakra): {rows_100}")
                    tw.snap(page, EVID, "fechamento_tc11_100pag")
                    evids.append("fechamento_tc11_100pag.png")
                    pg100_ok = True
    except Exception as e:
        log(f"  Erro 100/pag: {e}")

    log(f"\n  RESUMO TC11:")
    log(f"    Pag1 (25 linhas default): {default_25} ({rows_p1} linhas)")
    log(f"    Controles paginacao presentes: {has_pagination}")
    log(f"    Pag2 OK: {pagina2_ok} ({rows_p2} linhas)")
    log(f"    50/pag OK: {pg50_ok} ({rows_50} linhas)")
    log(f"    100/pag OK: {pg100_ok} ({rows_100} linhas)")

    # Veredito
    if default_25 and has_pagination and pagina2_ok:
        if pg50_ok and pg100_ok:
            passou(11, evids,
                   f"pag1=25 linhas; pag2={rows_p2} linhas; "
                   f"50/pag={rows_50}; 100/pag={rows_100}")
        elif pg50_ok:
            # 100/pag nao funcionou mas 50 funcionou
            falhou(11, evids,
                   f"pag1=25 OK, pag2={rows_p2} OK, 50/pag={rows_50} OK, "
                   f"MAS 100/pag NAO verificavel (controle nao encontrado ou nao respondeu)")
        else:
            falhou(11, evids,
                   f"pag1=25 OK, pag2={rows_p2} OK, "
                   f"MAS dropdown 50/100 por pagina NAO encontrado/nao funcionou")
    elif default_25 and has_pagination and not pagina2_ok:
        falhou(11, evids,
               f"pag1=25 OK, controles presentes, MAS botao proxima pagina NAO funcionou "
               f"(rows_p2={rows_p2})")
    elif not default_25 and rows_p1 >= 25:
        # Exibe mais de 25 na pagina 1 — pode ser configuracao diferente
        if has_pagination:
            falhou(11, evids,
                   f"pagina 1 exibe {rows_p1} linhas (esperava 25 como default); "
                   f"controles presentes; pag2={rows_p2}")
        else:
            falhou(11, evids,
                   f"pagina 1 exibe {rows_p1} linhas mas sem controles de paginacao")
    else:
        falhou(11, evids,
               f"pag1={rows_p1} linhas, has_pag={has_pagination}, pag2={pagina2_ok}")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("fechamento_qa11_faseB.py — TC3 (usuario novo) + TC11 (paginacao)")
    log(f"Org: {BASE_URL} / ID: {ORG_ID}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        # Browser 1: Admin (para criar usuario TC3 + validar TC3 com pagina nova no mesmo browser)
        browser_admin, ctx_admin, page_admin = tw.nova_pagina(p)
        try:
            # --- TC3: Precisa do admin para criar usuario novo ---
            log("\n--- Parte 1: TC3 (admin cria usuario novo) ---")
            login_admin(page_admin)
            run_tc3(page_admin)
        finally:
            ctx_admin.close()
            browser_admin.close()

        # Browser 2: Aluno (dante) — contexto limpo, sem cookies do admin
        browser_aluno, ctx_aluno, page_aluno = tw.nova_pagina(p)
        try:
            # --- Seed: Aluno (dante) semeia registros para TC11 ---
            log("\n--- Parte 2: Seed (Aluno dante) ---")
            login_ok = login_aluno(page_aluno, ADMIN_EMAIL, ADMIN_SENHA)
            if not login_ok:
                log("  ERRO: login como aluno falhou — TC11 nao pode ser executado")
                RESULTADOS[11] = {
                    "veredito": "FALHOU",
                    "evidencias": [],
                    "obs": "login como aluno (dante) falhou — semeia nao iniciado"
                }
            else:
                semeados, rows_visivel = semear_registros(page_aluno)
                log(f"\n  Semeados: {semeados}, visiveis: {rows_visivel}")

                # --- TC11 ---
                log("\n--- Parte 3: TC11 (paginacao) ---")
                run_tc11(page_aluno, rows_visivel)
        finally:
            ctx_aluno.close()
            browser_aluno.close()

    log("\n" + "=" * 60)
    log("RESULTADOS FASE B:")
    for tc, r in RESULTADOS.items():
        log(f"  TC{tc}: {r['veredito']} — {r['obs']}")
    log("=" * 60)


if __name__ == "__main__":
    main()
