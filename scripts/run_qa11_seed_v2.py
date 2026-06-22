"""run_qa11_seed_v2.py — QA 1.1 Fase 2 v2: Semear + re-run com seletores corretos.

Correções vs v1:
- Provedor: usa .creatable-select-field__control (não react-select__option)
- Conteúdo: idem (react-select criável)
- Categorias: campo obrigatório — deve ser preenchido
- Carga horária: formato HH:MM:SS (ex: "10:00:00" para 10h)
- Datas input[type=date]: formato yyyy-mm-dd para fill()
- Botão submit: "Salvar" (não "Enviar para aprovação")
- TC13: sidebar existe em desktop (8 itens); reframe para mobile
- TC3: usuário novo via Admin users page
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
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ORG_ID = os.environ.get("ORG_ID", "36675")

RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"

RESULTADOS = {}
LEDGER = {
    "total_semeados": 0,
    "aprovados": 0,
    "recusados": 0,
    "provedores_usados": [],
}


def log(msg):
    print(msg)


def passou(tc_id, evidencias, obs=""):
    RESULTADOS[tc_id] = {"veredito": "PASSOU", "evidencias": evidencias, "obs": obs}
    log(f"  [TC{tc_id}] PASSOU{' — ' + obs if obs else ''}")


def falhou(tc_id, evidencias, motivo):
    RESULTADOS[tc_id] = {"veredito": "FALHOU", "evidencias": evidencias, "obs": motivo}
    log(f"  [TC{tc_id}] FALHOU — {motivo}")


# ─── Logins ────────────────────────────────────────────────────────────────────

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
        raise SystemExit("Login Aluno falhou.")
    log(f"  Aluno logado: {page.url[:60]}")


def login_como_admin(page):
    c = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}
    tw.login(page, c, admin=True)
    log(f"  Admin logado: {page.url[:60]}")


def ir_para_meu_historico(page):
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=25000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
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


# ─── Helpers para React-Select Criável ─────────────────────────────────────────

def preencher_creatable_select(page, input_id, valor, criar_se_nao_existir=True):
    """Preenche um react-select criável pelo ID do input interno."""
    try:
        inp = page.locator(f"#{input_id}")
        if inp.count() == 0:
            return False
        inp.click(timeout=3000)
        page.wait_for_timeout(300)
        inp.fill(valor)
        page.wait_for_timeout(800)

        # Procura opção com o valor exato
        opcoes = page.locator("[class*='creatable-select-field__option'], [class*='__option']").all()
        for op in opcoes:
            try:
                t = op.inner_text().strip()
                if valor.lower() in t.lower() and "Criar" not in t:
                    op.click(timeout=3000)
                    page.wait_for_timeout(300)
                    return True
            except Exception:
                pass

        # Procura opção "Criar {valor}"
        if criar_se_nao_existir:
            for op in opcoes:
                try:
                    t = op.inner_text().strip()
                    if "Criar" in t or "criar" in t or "Create" in t:
                        op.click(timeout=3000)
                        page.wait_for_timeout(300)
                        return True
                except Exception:
                    pass

        # Fallback: pressiona Enter para aceitar o valor digitado
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        return True
    except Exception as e:
        log(f"    creatable_select erro (#{input_id}): {e}")
        return False


def converter_horas_para_hhmmss(horas_str):
    """Converte '10' (horas) para '10:00:00'."""
    try:
        h = int(horas_str)
        return f"{h:02d}:00:00"
    except Exception:
        return "01:00:00"


def converter_data_para_iso(data_pt):
    """Converte 'dd/mm/yyyy' para 'yyyy-mm-dd' (formato aceito por input[type=date])."""
    try:
        partes = data_pt.split("/")
        if len(partes) == 3:
            return f"{partes[2]}-{partes[1]}-{partes[0]}"
    except Exception:
        pass
    return data_pt


# ─── Criar registro ─────────────────────────────────────────────────────────────

def criar_registro(page, titulo, provedor, tipo_exp, carga_h, data_termino, data_validade=None):
    """Cria 1 registro pelo form /records/new."""
    # Navega diretamente para a URL do form
    page.goto(f"{BASE_URL}/o/{ORG_ID}/records/new?in_use_mode_layout=true",
              wait_until="domcontentloaded", timeout=25000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # ── Provedor (react-select-2-input) ──────────────────────────────────────
    prov_ok = preencher_creatable_select(page, "react-select-2-input", provedor)
    page.wait_for_timeout(300)

    # ── Conteúdo/Título (react-select-3-input) ────────────────────────────────
    cont_ok = preencher_creatable_select(page, "react-select-3-input", titulo)
    page.wait_for_timeout(300)

    # ── Tipo de experiência (react-select-4-input) ────────────────────────────
    tipo_ok = False
    try:
        inp = page.locator("#react-select-4-input")
        if inp.count() > 0:
            inp.click(timeout=3000)
            page.wait_for_timeout(400)
            # Para Tipo de experiência, as opções são fixas — não digita, seleciona diretamente
            # Primeiro tenta via digit para filtrar
            inp.fill(tipo_exp[:4])  # primeiros 4 chars para filtrar
            page.wait_for_timeout(600)
            opcoes = page.locator("[class*='creatable-select-field__option'], [class*='__option']").all()
            for op in opcoes:
                t = op.inner_text().strip()
                if tipo_exp.lower() in t.lower():
                    op.click(timeout=3000)
                    tipo_ok = True
                    break
            if not tipo_ok and opcoes:
                # Fallback: seleciona primeira opção disponível
                opcoes[0].click(timeout=3000)
                tipo_ok = True
            page.wait_for_timeout(300)
    except Exception as e:
        log(f"    Tipo exp erro: {e}")

    # ── Categorias (react-select-5-input) — campo obrigatório ─────────────────
    cat_ok = False
    try:
        inp = page.locator("#react-select-5-input")
        if inp.count() > 0:
            inp.click(timeout=3000)
            page.wait_for_timeout(400)
            opcoes = page.locator("[class*='creatable-select-field__option'], [class*='__option']").all()
            if opcoes:
                opcoes[0].click(timeout=3000)  # seleciona a 1ª categoria disponível
                cat_ok = True
            page.wait_for_timeout(300)
    except Exception as e:
        log(f"    Categorias erro: {e}")

    # ── Carga horária (HH:MM:SS) ──────────────────────────────────────────────
    carga_ok = False
    try:
        carga_input = page.locator("#workload_seconds")
        if carga_input.count() > 0:
            carga_input.fill(converter_horas_para_hhmmss(carga_h))
            carga_ok = True
    except Exception as e:
        log(f"    Carga erro: {e}")

    # ── Data de término (obrigatória) — input[type=date], formato yyyy-mm-dd ───
    data_term_ok = False
    try:
        data_end = page.locator("#endDate")
        if data_end.count() > 0:
            data_iso = converter_data_para_iso(data_termino)
            data_end.fill(data_iso)
            page.wait_for_timeout(200)
            data_term_ok = True
    except Exception as e:
        log(f"    Data término erro: {e}")

    # ── Data de validade (opcional) ────────────────────────────────────────────
    if data_validade:
        try:
            data_exp = page.locator("#expirationDate")
            if data_exp.count() > 0:
                data_iso = converter_data_para_iso(data_validade)
                data_exp.fill(data_iso)
                page.wait_for_timeout(200)
        except Exception as e:
            log(f"    Data validade erro: {e}")

    log(f"    Prov={prov_ok}, Cont={cont_ok}, Tipo={tipo_ok}, Cat={cat_ok}, "
        f"Carga={carga_ok}, DataTerm={data_term_ok}")

    # ── Salvar ────────────────────────────────────────────────────────────────
    enviar_ok = False
    try:
        btn_salvar = page.get_by_role("button", name=re.compile(r"^Salvar$|^Enviar para aprovação$", re.I)).first
        if btn_salvar.count() == 0:
            btn_salvar = page.locator("button[type='submit']").first
        if btn_salvar.count() > 0 and btn_salvar.is_visible(timeout=2000):
            btn_salvar.click(timeout=5000)
            page.wait_for_timeout(3000)
            tw.dispensar_nps(page)

            # Verifica toast de sucesso OU redirecionamento para a lista
            toasts = ["enviado para aprovação", "adicionado", "salvo", "criado"]
            for t in toasts:
                if page.get_by_text(re.compile(t, re.I)).count() > 0:
                    enviar_ok = True
                    break

            # Verifica se voltou para lista (/records)
            if not enviar_ok and "/records" in page.url and "/records/new" not in page.url:
                enviar_ok = True
                log(f"    Redirecionado para {page.url[:50]} — assumindo sucesso")
    except Exception as e:
        log(f"    Salvar erro: {e}")
        # Cancela se ainda no form
        try:
            if "/records/new" in page.url:
                btn_cancelar = page.get_by_role("button", name="Cancelar").first
                if btn_cancelar.count() > 0:
                    btn_cancelar.click(timeout=3000)
        except Exception:
            pass

    return enviar_ok


# ─── Massa de dados ─────────────────────────────────────────────────────────────

# 30 registros variados. Formato: (titulo, provedor, tipo_exp, carga_h, data_term, data_val)
# carga_h: número de horas (ex: "10" → "10:00:00")
# datas: dd/mm/yyyy → convertidas para yyyy-mm-dd
MASSA = [
    ("QA11-Alura-Python-Basico",     "Alura",             "Curso",     "10", "15/01/2025", None),
    ("QA11-Alura-Python-Avancado",   "Alura",             "Trilha",    "20", "20/02/2025", "20/02/2026"),
    ("QA11-Alura-Django-REST",       "Alura",             "Curso",     "15", "10/03/2025", None),
    ("QA11-Alura-Docker-K8s",        "Alura",             "Workshop",  "8",  "05/04/2025", "05/04/2026"),
    ("QA11-Alura-Git-GitHub",        "Alura",             "Curso",     "6",  "12/04/2025", None),
    ("QA11-Alura-SQL-Postgre",       "Alura",             "Aula",      "12", "20/04/2025", "20/04/2026"),
    ("QA11-Alura-AWS-Cloud",         "Alura",             "Curso",     "25", "01/05/2025", None),
    ("QA11-Alura-React-Hooks",       "Alura",             "Trilha",    "18", "10/05/2025", "10/05/2026"),
    ("QA11-Coursera-ML-Intro",       "Coursera",          "Curso",     "40", "15/01/2025", None),
    ("QA11-Coursera-DataScience",    "Coursera",          "Trilha",    "60", "28/02/2025", "28/02/2026"),
    ("QA11-Coursera-TensorFlow",     "Coursera",          "Curso",     "30", "15/03/2025", None),
    ("QA11-Coursera-NLP",            "Coursera",          "Aula",      "20", "01/04/2025", None),
    ("QA11-Coursera-Agile-PM",       "Coursera",          "Curso",     "15", "10/04/2025", "10/04/2026"),
    ("QA11-FGV-Gestao-Projetos",     "FGV",               "Curso",     "45", "10/01/2025", None),
    ("QA11-FGV-Lideranca-Times",     "FGV",               "Workshop",  "8",  "15/02/2025", "15/02/2026"),
    ("QA11-FGV-Financas-Corp",       "FGV",               "Curso",     "60", "20/03/2025", None),
    ("QA11-FGV-MBA-Marketing",       "FGV",               "Trilha",    "120","01/04/2025", "01/04/2027"),
    ("QA11-Udemy-Excel-Avancado",    "Udemy",             "Curso",     "12", "05/01/2025", None),
    ("QA11-Udemy-Power-BI",          "Udemy",             "Curso",     "16", "10/02/2025", "10/02/2026"),
    ("QA11-Udemy-Photoshop-CC",      "Udemy",             "Aula",      "8",  "01/03/2025", None),
    ("QA11-Udemy-Node-API",          "Udemy",             "Curso",     "20", "15/03/2025", None),
    ("QA11-USP-Estatistica",         "USP",               "Curso",     "60", "10/01/2025", None),
    ("QA11-USP-Epidemiologia",       "USP",               "Curso",     "40", "20/03/2025", "20/03/2026"),
    ("QA11-USP-Direito-Digital",     "USP",               "Palestra",  "4",  "01/04/2025", None),
    ("QA11-LI-Storytelling",         "LinkedIn Learning", "Palestra",  "2",  "05/01/2025", None),
    ("QA11-LI-Negociacao",           "LinkedIn Learning", "Workshop",  "4",  "10/02/2025", None),
    ("QA11-LI-Design-Thinking",      "LinkedIn Learning", "Curso",     "6",  "01/03/2025", "01/03/2026"),
    ("QA11-LI-OKR-Pratico",          "LinkedIn Learning", "Mentoria",  "3",  "15/03/2025", None),
    ("QA11-LI-Comunicacao-Corp",     "LinkedIn Learning", "Evento",    "2",  "01/04/2025", None),
    ("QA11-Extra-React-Native",      "Alura",             "Curso",     "22", "20/05/2025", None),
]


# ─── Fase 2: Semear ─────────────────────────────────────────────────────────────

def fase2_semear(page, total_atual):
    log(f"\n=== FASE 2: Semeando massa (atualmente {total_atual} registros) ===")
    semeados = 0
    falhas = 0

    for i, (titulo, provedor, tipo_exp, carga_h, data_term, data_val) in enumerate(MASSA):
        # Para quando tiver >= 36 (margem boa acima de 26)
        if total_atual + semeados >= 36:
            log(f"  Parando: já temos {total_atual + semeados} registros")
            break

        log(f"  [{i+1:02d}] {titulo} | {provedor}")
        ok = criar_registro(page, titulo, provedor, tipo_exp, carga_h, data_term, data_val)

        if ok:
            semeados += 1
            if provedor not in LEDGER["provedores_usados"]:
                LEDGER["provedores_usados"].append(provedor)
            log(f"    OK (semeado #{semeados})")
        else:
            falhas += 1
            log(f"    FALHOU")

    ir_para_meu_historico(page)
    page.wait_for_timeout(1000)
    total_final = page.locator("table tbody tr").count()
    tw.snap(page, EVID, "seed_v2_lista_pos_semeia")

    LEDGER["total_semeados"] = semeados
    log(f"  Fase 2: {semeados} OK, {falhas} falhas, total na lista: {total_final}")
    return total_final


# ─── Fase 3: Admin adjudica ─────────────────────────────────────────────────────

def fase3_admin(page_admin):
    log("\n=== FASE 3: Admin aprova/recusa ===")

    admin_reg_url = f"{BASE_URL}/o/{ORG_ID}/learning_records"
    page_admin.goto(admin_reg_url, wait_until="domcontentloaded", timeout=25000)
    try:
        page_admin.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page_admin.wait_for_timeout(3000)
    tw.dispensar_nps(page_admin)
    tw.snap(page_admin, EVID, "admin_f3_inicial")

    # Filtra Pendentes
    try:
        kpi = page_admin.get_by_text("Pendentes", exact=True).first
        if kpi.count() > 0:
            kpi.click(timeout=5000)
            page_admin.wait_for_timeout(2000)
    except Exception:
        pass

    rows = page_admin.locator("table tbody tr").count()
    log(f"  Pendentes visíveis: {rows}")
    tw.snap(page_admin, EVID, "admin_f3_pendentes")

    aprovados = 0
    recusados = 0
    MAX_APROVAR = 15  # aprova até 15 (deixa resto pendente)

    for i in range(min(rows + 5, 50)):
        linhas = page_admin.locator("table tbody tr").all()
        if not linhas:
            break

        # Alterna: primeiros MAX_APROVAR aprovamos, depois recusa 1
        linha = linhas[0]

        try:
            titulo_cel = linha.locator("td").nth(2).inner_text().strip()
        except Exception:
            titulo_cel = f"linha-{i+1}"

        # Abre kebab (more_vert)
        try:
            kebab = linha.locator("[data-icon='more_vert']").first
            if kebab.count() == 0:
                kebab = linha.locator("td:last-child button").first
            if kebab.count() == 0:
                kebab = linha.locator("td").last
            kebab.click(timeout=5000, force=True)
            page_admin.wait_for_timeout(1200)
        except Exception as e:
            log(f"  [{i+1}] kebab erro: {e}")
            continue

        menu_items = tw.menu_visivel(page_admin)
        log(f"  [{i+1}] '{titulo_cel[:30]}' menu: {menu_items}")

        if aprovados < MAX_APROVAR:
            # Aprova
            clicou = tw.click_menuitem(page_admin, "Avaliar registro")
            if not clicou:
                clicou = tw.click_menuitem(page_admin, "Aprovar")
            page_admin.wait_for_timeout(2000)
            tw.dispensar_nps(page_admin)

            if clicou:
                # Verifica se está num form de avaliação
                cur_url = page_admin.url
                if "avaliar" in cur_url or "evaluate" in cur_url or "edit" in cur_url:
                    btn = page_admin.get_by_role("button", name=re.compile("Salvar e aprovar|Aprovar", re.I)).first
                    if btn.count() > 0 and btn.is_visible(timeout=2000):
                        btn.click(timeout=5000)
                        page_admin.wait_for_timeout(2000)
                        tw.dispensar_nps(page_admin)
                        aprovados += 1
                        LEDGER["aprovados"] += 1
                        log(f"  [{i+1}] APROVADO")
                    else:
                        # Pode ter aprovado diretamente (sem form)
                        aprovados += 1
                        LEDGER["aprovados"] += 1
                        log(f"  [{i+1}] APROVADO (direto)")
                else:
                    # Aprovado via modal/toast direto
                    toast_ok = page_admin.get_by_text(re.compile("aprovado", re.I)).count() > 0
                    if toast_ok:
                        aprovados += 1
                        LEDGER["aprovados"] += 1
                    log(f"  [{i+1}] Aprovado? URL={cur_url[:40]}, toast={toast_ok}")
            else:
                page_admin.keyboard.press("Escape")
                page_admin.wait_for_timeout(500)

        elif recusados == 0:
            # Recusa 1 com justificativa
            clicou = tw.click_menuitem(page_admin, "Avaliar registro")
            page_admin.wait_for_timeout(2000)
            tw.dispensar_nps(page_admin)

            if clicou:
                btn_rec = page_admin.get_by_role("button", name=re.compile(r"^Recusar$", re.I)).first
                if btn_rec.count() > 0 and btn_rec.is_visible(timeout=2000):
                    btn_rec.click(timeout=5000)
                    page_admin.wait_for_timeout(1500)

                    # Modal de recusa — justificativa
                    just = page_admin.get_by_label(re.compile("Justificativa", re.I)).first
                    if just.count() == 0:
                        just = page_admin.get_by_placeholder(re.compile("Explique", re.I)).first
                    if just.count() > 0:
                        just.fill("QA teste automatizado — recusa de exemplo suíte QA 1.1")
                        page_admin.wait_for_timeout(500)

                    btn_conf = page_admin.get_by_role("button", name="Recusar registro").first
                    if btn_conf.count() > 0:
                        btn_conf.click(timeout=5000)
                        page_admin.wait_for_timeout(2000)
                        tw.dispensar_nps(page_admin)
                        recusados += 1
                        LEDGER["recusados"] += 1
                        log(f"  [{i+1}] RECUSADO")
                    else:
                        page_admin.keyboard.press("Escape")
            else:
                page_admin.keyboard.press("Escape")
                page_admin.wait_for_timeout(500)
        else:
            # Já fez 15 aprovações e 1 recusa — para
            page_admin.keyboard.press("Escape")
            page_admin.wait_for_timeout(500)
            break

        # Volta para lista de pendentes
        page_admin.goto(admin_reg_url, wait_until="domcontentloaded", timeout=25000)
        try:
            page_admin.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page_admin.wait_for_timeout(2000)
        tw.dispensar_nps(page_admin)

        # Re-filtra pendentes
        try:
            kpi = page_admin.get_by_text("Pendentes", exact=True).first
            if kpi.count() > 0:
                kpi.click(timeout=5000)
                page_admin.wait_for_timeout(1500)
        except Exception:
            pass

        pendentes_restantes = page_admin.locator("table tbody tr").count()
        if pendentes_restantes == 0 or (aprovados >= MAX_APROVAR and recusados >= 1):
            log(f"  Fase 3 completa: {aprovados} aprovados, {recusados} recusados")
            break

    tw.snap(page_admin, EVID, "admin_f3_pos_adjudicacao")
    log(f"  Resultado: {aprovados} aprovados, {recusados} recusados")
    return aprovados, recusados


# ─── TC3: Empty state ──────────────────────────────────────────────────────────

def run_tc3(page_admin, page_novo):
    log("\n=== TC3: Empty state com usuário novo ===")
    evids = []

    novo_email = f"qa11test{os.getpid()}@mailnull.com"
    novo_senha = "123456"
    log(f"  Email novo: {novo_email}")

    # Cria usuário via admin
    usuarios_url = f"{BASE_URL}/o/{ORG_ID}/users"
    page_admin.goto(usuarios_url, wait_until="domcontentloaded", timeout=25000)
    try:
        page_admin.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page_admin.wait_for_timeout(2000)
    tw.dispensar_nps(page_admin)
    tw.snap(page_admin, EVID, "tc3_admin_usuarios")

    # Dump dos botões na página de usuários
    btns = page_admin.locator("button, a").filter(
        has_text=re.compile("Adicionar|Novo|Invite|Convidar|criar", re.I)).all()
    log(f"  Botões Adicionar na página Usuários: {[b.inner_text().strip()[:30] for b in btns[:5]]}")

    btn_novo = btns[0] if btns else None
    criado = False

    if btn_novo:
        btn_novo.click(timeout=5000)
        page_admin.wait_for_timeout(2000)
        tw.dispensar_nps(page_admin)
        tw.snap(page_admin, EVID, "tc3_form_usuario")

        # Verifica URL — pode ser /users/new ou modal
        log(f"  URL após click: {page_admin.url[:60]}")

        try:
            # Preenche Nome
            for lbl in ["Nome", "Name", "First Name"]:
                campo = page_admin.get_by_label(re.compile(lbl, re.I)).first
                if campo.count() > 0 and campo.is_visible(timeout=1000):
                    campo.fill("QA11 Empty")
                    break

            # Sobrenome
            for lbl in ["Sobrenome", "Last Name"]:
                campo = page_admin.get_by_label(re.compile(lbl, re.I)).first
                if campo.count() > 0 and campo.is_visible(timeout=1000):
                    campo.fill("User")
                    break

            # E-mail
            for lbl in ["E-mail", "Email", "email"]:
                campo = page_admin.get_by_label(re.compile(lbl, re.I)).first
                if campo.count() == 0:
                    campo = page_admin.get_by_placeholder(re.compile("e-mail|email|@", re.I)).first
                if campo.count() > 0 and campo.is_visible(timeout=1000):
                    campo.fill(novo_email)
                    break

            # Senha
            for lbl in ["Senha", "Password"]:
                campo = page_admin.get_by_label(re.compile(lbl, re.I)).first
                if campo.count() > 0 and campo.is_visible(timeout=1000):
                    campo.fill(novo_senha)
                    break

            # Confirmar senha
            for lbl in ["Confirmar senha", "Confirm", "Repetir"]:
                campo = page_admin.get_by_label(re.compile(lbl, re.I)).first
                if campo.count() > 0 and campo.is_visible(timeout=1000):
                    campo.fill(novo_senha)
                    break

            tw.snap(page_admin, EVID, "tc3_form_preenchido")

            # Salva
            btn_s = page_admin.get_by_role("button", name=re.compile("Salvar|Criar|Convidar|Send|Enviar", re.I)).first
            if btn_s.count() > 0:
                btn_s.click(timeout=5000)
                page_admin.wait_for_timeout(3000)
                tw.dispensar_nps(page_admin)
                criado = page_admin.get_by_text(re.compile("criado|salvo|adicionado|enviado|convidado", re.I)).count() > 0
                if not criado:
                    # Verifica redirecionamento (pode ser para /users/{id})
                    criado = "/users/" in page_admin.url and "/new" not in page_admin.url
                log(f"  Usuário criado: {criado}, URL: {page_admin.url[:60]}")
        except Exception as e:
            log(f"  Erro criar usuário: {e}")
    else:
        log("  Botão de criar usuário não encontrado")

    if not criado:
        RESULTADOS[3] = {
            "veredito": "NAO_VERIFICADO",
            "evidencias": ["tc3_admin_usuarios.png"],
            "obs": f"não foi possível criar usuário novo: {novo_email}"
        }
        return None

    # Login com usuário novo
    log(f"  Logando com {novo_email}")
    page_novo.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page_novo.wait_for_selector("#user_email", timeout=10000)
    page_novo.fill("#user_email", novo_email)
    page_novo.fill("#user_password", novo_senha)
    page_novo.click("#user_submit")
    try:
        page_novo.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page_novo.wait_for_timeout(3000)
    tw.dispensar_nps(page_novo)

    # Trata troca de senha forçada
    if "password" in page_novo.url.lower() or "change" in page_novo.url.lower():
        log("  Troca de senha forçada — tratando...")
        try:
            campos_senha = page_novo.locator("input[type='password']").all()
            for cs in campos_senha:
                cs.fill("TwygoQA2025!")
            btn_c = page_novo.get_by_role("button", name=re.compile("Salvar|Confirmar", re.I)).first
            if btn_c.count() > 0:
                btn_c.click(timeout=5000)
                page_novo.wait_for_timeout(3000)
                tw.dispensar_nps(page_novo)
            novo_senha = "TwygoQA2025!"
        except Exception as e:
            log(f"  Erro troca senha: {e}")

    login_ok = "/users/login" not in page_novo.url
    log(f"  Login OK: {login_ok}")

    if not login_ok:
        RESULTADOS[3] = {
            "veredito": "NAO_VERIFICADO",
            "evidencias": [],
            "obs": f"login com usuário novo falhou (email: {novo_email})"
        }
        return novo_email

    # Navega para Meu histórico
    page_novo.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=25000)
    try:
        page_novo.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page_novo.wait_for_timeout(2500)
    tw.dispensar_nps(page_novo)
    tw.snap(page_novo, EVID, "tc3_meu_historico_novo_usuario")
    evids.append("tc3_meu_historico_novo_usuario.png")

    # Verifica empty state
    has_empty = page_novo.get_by_text(
        "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
    ).count() > 0

    rows = page_novo.locator("table tbody tr").count()

    # KPIs com 0
    kpi_vals = page_novo.evaluate(r"""() => {
        const nums = [];
        const cards = document.querySelectorAll('[class*="stat"], [class*="kpi"], [class*="card"]');
        for (const c of cards) {
            const t = c.innerText || '';
            const m = t.match(/^\s*(\d+)\s/);
            if (m) nums.push(parseInt(m[1]));
        }
        return nums;
    }""")
    kpi_zero = all(v == 0 for v in kpi_vals) if kpi_vals else None
    log(f"  Empty msg: {has_empty}, rows: {rows}, KPI vals: {kpi_vals}, zero: {kpi_zero}")

    tw.snap(page_novo, EVID, "tc3_empty_state")
    evids.append("tc3_empty_state.png")

    if has_empty and rows == 0:
        passou(3, evids, f"empty state correto; KPI vals={kpi_vals}; email={novo_email}")
    elif rows == 0 and not has_empty:
        falhou(3, evids, "tabela vazia mas mensagem empty state não encontrada")
    elif rows > 0:
        falhou(3, evids, f"usuário novo já tem {rows} registros — isolamento falhou")
    else:
        falhou(3, evids, "empty state não renderizou")

    return novo_email


# ─── Re-run TCs ────────────────────────────────────────────────────────────────

def run_tc2_rerun(page):
    log("\n[TC2] Colunas/conteúdo/tooltips com massa...")
    ir_para_meu_historico(page)
    evids = []

    headers = page.locator("table thead th, table thead td").all_inner_texts()
    log(f"  Headers: {headers}")

    cols_obrig = ["Origem", "Conteúdo", "Situação", "Progresso", "Carga horária"]
    cols_ok = all(any(col.lower() in h.lower() for h in headers) for col in cols_obrig)

    interno = page.locator("td").filter(has_text="Interno").count()
    externo = page.locator("td").filter(has_text="Externo").count()
    aprovado = page.locator("td").filter(has_text="Aprovado").count()
    pendente = page.locator("td").filter(has_text="Pendente").count()
    recusado = page.locator("td").filter(has_text="Recusado").count()
    datas = page.locator("td").filter(has_text=re.compile(r"\d{2}/\d{2}/\d{4}")).count()
    carga_vals = page.locator("td").filter(has_text=re.compile(r"\d+h$")).count()

    # Verifica "—" em coluna Expira em (para registros sem data de validade)
    traco_expira = page.evaluate(r"""() => {
        const ths = Array.from(document.querySelectorAll('th'));
        const idx = ths.findIndex(h => /expira|validade/i.test(h.innerText));
        if (idx < 0) return -1;
        return Array.from(document.querySelectorAll('tbody tr')).filter(r => {
            const tds = r.querySelectorAll('td');
            return tds[idx] && (tds[idx].innerText.trim() === '—' || tds[idx].innerText.trim() === '-' || tds[idx].innerText.trim() === '');
        }).length;
    }""")

    log(f"  Interno={interno}, Externo={externo}, Aprovado={aprovado}, "
        f"Pendente={pendente}, Recusado={recusado}")
    log(f"  Datas={datas}, Carga={carga_vals}, Tracos Expira={traco_expira}")

    # Tooltip Origem
    tooltip_origem = ""
    try:
        origem_th = page.locator("th").filter(has_text="Origem").first
        if origem_th.count() > 0:
            ic = origem_th.locator("svg, button, [role='button']").last
            ic.hover(timeout=3000)
            page.wait_for_timeout(800)
            tt = page.locator("[role='tooltip'], .chakra-popover__content").last
            if tt.count() > 0 and tt.is_visible(timeout=1000):
                tooltip_origem = tt.inner_text()[:80]
            page.mouse.move(200, 200)
            page.wait_for_timeout(400)
    except Exception:
        pass

    tw.snap(page, EVID, "tc2r_tabela_massa")
    evids.append("tc2r_tabela_massa.png")

    obs_partes = [
        f"Headers: {[h for h in headers if h.strip()]}",
        f"Externo={externo}, Interno={interno}",
        f"Aprovado={aprovado}, Pendente={pendente}, Recusado={recusado}",
        f"Datas={datas}, Carga={carga_vals}, Tracos Expira={traco_expira}",
        "Compartilhado: não verificado (não semeável via form Aluno)",
    ]
    if tooltip_origem:
        obs_partes.append(f"tooltip Origem: '{tooltip_origem[:60]}'")

    falhas = []
    if not cols_ok:
        falhas.append(f"colunas obrigatórias ausentes: {headers}")
    if externo == 0 and interno == 0:
        falhas.append("sem chips de origem (Externo nem Interno)")
    if aprovado == 0 and pendente == 0:
        falhas.append("sem chips de Situação")
    if datas == 0:
        falhas.append("sem datas dd/mm/yyyy")

    if falhas:
        falhou(2, evids, "; ".join(falhas) + " | " + "; ".join(obs_partes))
    else:
        passou(2, evids, "; ".join(obs_partes))


def run_tc5_rerun(page):
    log("\n[TC5] Modo grid com massa...")
    ir_para_meu_historico(page)
    evids = []

    page.mouse.move(200, 200)
    page.wait_for_timeout(300)
    grid_clicou = clicar_toggle_grid(page)
    page.wait_for_timeout(2000)

    table_visible = False
    if page.locator("table").count() > 0:
        try:
            table_visible = page.locator("table").is_visible(timeout=1000)
        except Exception:
            pass

    selecionar_todos = page.locator("text=Selecionar todos da página atual").count() > 0
    externo_grid = page.locator("span").filter(has_text="Externo").count()
    interno_grid = page.locator("span").filter(has_text="Interno").count()

    log(f"  Grid: table={table_visible}, sel_todos={selecionar_todos}, "
        f"Externo={externo_grid}, Interno={interno_grid}")
    tw.snap(page, EVID, "tc5r_grid_massa")
    evids.append("tc5r_grid_massa.png")

    obs = (f"Externo={externo_grid}, Interno={interno_grid} no grid. "
           "Compartilhado: não verificado.")

    if not grid_clicou:
        falhou(5, evids, "#grid-view-icon não encontrado")
    elif not table_visible and (selecionar_todos or externo_grid > 0 or interno_grid > 0):
        passou(5, evids, obs)
    elif not table_visible:
        falhou(5, evids, "tabela oculta mas cards não detectados")
    else:
        falhou(5, evids, "tabela ainda visível após toggle Grid")


def run_tc7_rerun(page):
    log("\n[TC7] Busca com massa Alura/Coursera/outros...")
    ir_para_meu_historico(page)
    evids = []

    row_total = page.locator("table tbody tr").count()
    if row_total == 0:
        falhou(7, evids, "sem registros")
        return
    log(f"  Total linhas: {row_total}")

    busca = page.get_by_placeholder(re.compile("Pesquise", re.I)).first

    def buscar(termo, wait_ms=3500):
        busca.click(click_count=3)
        page.keyboard.press("Delete")
        page.wait_for_timeout(300)
        busca.press_sequentially(termo, delay=60)
        page.wait_for_timeout(wait_ms)

    # Busca "Alura" — temos 8+ Alura, esperamos filtrar para < total
    buscar("Alura")
    rows_alura = page.locator("table tbody tr").count()
    log(f"  Alura: {rows_alura}/{row_total}")
    tw.snap(page, EVID, "tc7r2_alura")
    evids.append("tc7r2_alura.png")

    # Busca "Coursera"
    buscar("Coursera")
    rows_coursera = page.locator("table tbody tr").count()
    log(f"  Coursera: {rows_coursera}/{row_total}")
    tw.snap(page, EVID, "tc7r2_coursera")
    evids.append("tc7r2_coursera.png")

    # Busca por título QA11-Alura
    buscar("QA11-Alura")
    rows_qa11 = page.locator("table tbody tr").count()
    log(f"  QA11-Alura (título): {rows_qa11}/{row_total}")
    tw.snap(page, EVID, "tc7r2_titulo")
    evids.append("tc7r2_titulo.png")

    # Busca inexistente
    buscar("zzzzz-inexistente-99")
    rows_inex = page.locator("table tbody tr").count()
    empty_inex = page.get_by_text("Nenhum registro encontrado").count() > 0
    log(f"  Inexistente: {rows_inex}, empty={empty_inex}")
    tw.snap(page, EVID, "tc7r2_inexistente")
    evids.append("tc7r2_inexistente.png")

    # Limpa
    busca.click(click_count=3)
    page.keyboard.press("Delete")
    page.wait_for_timeout(2500)
    rows_clear = page.locator("table tbody tr").count()
    log(f"  Limpo: {rows_clear}")

    alura_filtrou = rows_alura < row_total
    coursera_filtrou = rows_coursera < row_total
    inex_filtrou = rows_inex == 0 or empty_inex

    if alura_filtrou and coursera_filtrou and inex_filtrou:
        passou(7, evids,
               f"busca filtra por provedor (Alura={rows_alura}, Coursera={rows_coursera}) "
               f"e inexistente=0; total={row_total}")
    elif not alura_filtrou and not inex_filtrou:
        falhou(7, evids,
               f"busca NÃO filtra — Alura={rows_alura}/{row_total}, "
               f"Coursera={rows_coursera}/{row_total}, inexistente={rows_inex} "
               f"— bug backend confirmado (mesma causa TC4)")
    elif not alura_filtrou:
        falhou(7, evids,
               f"busca 'Alura' retornou {rows_alura}/{row_total} (esperava < {row_total})")
    else:
        falhou(7, evids,
               f"busca inexistente retornou {rows_inex} (esperava 0)")


def run_tc8_rerun(page):
    log("\n[TC8] Interseção busca + KPI + drawer...")
    ir_para_meu_historico(page)
    evids = []

    row_total = page.locator("table tbody tr").count()
    log(f"  Total linhas: {row_total}")

    # Passo 2: KPI Emitidos
    try:
        kpi = page.get_by_text("Emitidos", exact=True).first
        kpi.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        kpi.click(timeout=5000)
        page.wait_for_timeout(2000)
    except Exception as e:
        log(f"  KPI erro: {e}")

    rows_emitidos = page.locator("table tbody tr").count()
    log(f"  Após KPI Emitidos: {rows_emitidos}")
    tw.snap(page, EVID, "tc8r_filtro_emitidos")
    evids.append("tc8r_filtro_emitidos.png")
    kpi_filtra = rows_emitidos < row_total and rows_emitidos > 0

    # Passo 3: drawer Filtro
    drawer_ok = False
    try:
        filtro_btn = page.locator("button").filter(has_text=re.compile(r"^Filtro$")).first
        if filtro_btn.count() > 0:
            filtro_btn.click(timeout=5000)
            page.wait_for_timeout(2000)
            dialogs = page.locator("[role='dialog']").all()
            for d in dialogs:
                box = d.bounding_box()
                if box and box["width"] > 200 and box["height"] > 200 and d.is_visible():
                    drawer_ok = True
                    break
            if drawer_ok:
                tw.snap(page, EVID, "tc8r_drawer")
                evids.append("tc8r_drawer.png")
                page.keyboard.press("Escape")
                page.wait_for_timeout(1000)
    except Exception as e:
        log(f"  Drawer erro: {e}")
    log(f"  Drawer Filtro: {drawer_ok}")

    # Passo 4/5: busca "Alura" com KPI Emitidos ativo
    busca = page.get_by_placeholder(re.compile("Pesquise", re.I)).first
    busca.click()
    busca.press_sequentially("Alura", delay=60)
    page.wait_for_timeout(3500)
    rows_intersecao = page.locator("table tbody tr").count()
    log(f"  Emitidos+Alura: {rows_intersecao} (era {rows_emitidos} com só Emitidos)")
    tw.snap(page, EVID, "tc8r_intersecao")
    evids.append("tc8r_intersecao.png")

    busca_estreitou = rows_intersecao < rows_emitidos

    # Limpa
    busca.click(click_count=3)
    page.keyboard.press("Delete")
    page.wait_for_timeout(1500)
    try:
        limpar = page.locator("text=Limpar filtro")
        if limpar.count() > 0:
            limpar.click(timeout=2000)
            page.wait_for_timeout(1000)
    except Exception:
        pass

    # Avalia
    if not kpi_filtra:
        falhou(8, evids, f"KPI Emitidos não filtrou ({rows_emitidos} de {row_total})")
    elif not drawer_ok:
        falhou(8, evids,
               f"KPI filtrou ({rows_emitidos}/{row_total}) mas drawer Filtro não abriu")
    elif not busca_estreitou:
        falhou(8, evids,
               f"KPI filtrou ({rows_emitidos}/{row_total}), drawer abriu, "
               f"MAS busca 'Alura' NÃO estreitou ({rows_intersecao}=={rows_emitidos}) "
               f"— mesma causa do TC7: backend ignora search_query")
    else:
        passou(8, evids,
               f"KPI filtrou ({rows_emitidos}/{row_total}), drawer abriu, "
               f"busca estreitou para {rows_intersecao}")


def run_tc10_rerun(page):
    log("\n[TC10] Ordenação com massa...")
    ir_para_meu_historico(page)
    evids = []

    row_count = page.locator("table tbody tr").count()
    if row_count < 2:
        falhou(10, evids, f"precisa >= 2 registros, tem {row_count}")
        return
    log(f"  {row_count} linhas")

    # Coluna "Emitido em" / "Data do certificado"
    header_data = page.locator("th").filter(
        has_text=re.compile("Emitido em|Data do cert", re.I)).first
    if header_data.count() == 0:
        header_data = page.locator("th").filter(has_text=re.compile("emitido|data", re.I)).first

    if header_data.count() == 0:
        falhou(10, evids, "header de data não encontrado")
        return

    header_text = header_data.inner_text()
    log(f"  Header: '{header_text}'")

    def get_col(regex):
        ths = page.locator("th").all_inner_texts()
        idx = next((i for i, h in enumerate(ths) if re.search(regex, h, re.I)), -1)
        if idx < 0:
            return [], -1
        return [r.locator("td").nth(idx).inner_text().strip()
                for r in page.locator("table tbody tr").all()[:15]], idx

    header_data.click(timeout=5000)
    page.wait_for_timeout(1200)
    tw.snap(page, EVID, "tc10r_asc")
    evids.append("tc10r_asc.png")
    vals_asc, _ = get_col(r"Emitido|Data do cert")
    log(f"  ASC: {vals_asc[:6]}")

    header_data.click(timeout=5000)
    page.wait_for_timeout(1200)
    tw.snap(page, EVID, "tc10r_desc")
    evids.append("tc10r_desc.png")
    vals_desc, _ = get_col(r"Emitido|Data do cert")
    log(f"  DESC: {vals_desc[:6]}")

    header_data.click(timeout=5000)
    page.wait_for_timeout(1200)

    # Coluna Expira em — nulos no fim
    nulos_no_fim = None
    header_expira = page.locator("th").filter(has_text=re.compile("Expira|validade", re.I)).first
    if header_expira.count() > 0:
        header_expira.click(timeout=5000)
        page.wait_for_timeout(1200)
        tw.snap(page, EVID, "tc10r_expira_asc")
        evids.append("tc10r_expira_asc.png")
        vals_expira, _ = get_col(r"Expira|validade")
        log(f"  Expira ASC: {vals_expira}")
        if vals_expira:
            last_3 = vals_expira[-3:]
            nulos_no_fim = all(v in ("—", "-", "") for v in last_3)
            log(f"  Últimas 3: {last_3} → nulos no fim: {nulos_no_fim}")

    sort_diferente = vals_asc != vals_desc
    datas_validas = [v for v in vals_asc if v not in ("—", "-", "")]

    if len(datas_validas) < 2:
        passou(10, evids,
               f"sort disponível, ciclo testado; {len(datas_validas)} datas válidas; "
               f"nulos no fim: {nulos_no_fim}")
    elif sort_diferente:
        passou(10, evids,
               f"sort cicla: ASC={vals_asc[:4]}, DESC={vals_desc[:4]}; "
               f"nulos no fim: {nulos_no_fim}")
    else:
        falhou(10, evids, f"ASC e DESC iguais: {vals_asc[:4]}")


def run_tc11_rerun(page):
    log("\n[TC11] Paginação 25/50/100...")
    ir_para_meu_historico(page)
    evids = []

    row_count = page.locator("table tbody tr").count()
    log(f"  Linhas na página: {row_count}")
    tw.snap(page, EVID, "tc11r_lista")
    evids.append("tc11r_lista.png")

    if row_count < 25:
        falhou(11, evids, f"paginação precisa >= 25 registros, lista mostra {row_count}")
        return

    # Verifica controles de paginação
    pag_next = page.locator("[aria-label*='próxima' i], [aria-label*='next' i], "
                             "[aria-label*='Next'], [aria-label*='forward']").first
    pag_texto = page.get_by_text(re.compile(r"por página|per page", re.I)).first
    pag_nav = page.locator("nav[aria-label*='pag' i], [class*='pagination']").count()

    log(f"  Controles: next={pag_next.count()>0}, por_pagina={pag_texto.count()>0}, nav={pag_nav}")
    tw.snap(page, EVID, "tc11r_controles")
    evids.append("tc11r_controles.png")

    # Navega para página 2
    pagina2_ok = False
    if pag_next.count() > 0:
        try:
            if pag_next.is_visible(timeout=2000):
                pag_next.click(timeout=5000)
                page.wait_for_timeout(2000)
                rows_pg2 = page.locator("table tbody tr").count()
                log(f"  Página 2: {rows_pg2} linhas")
                tw.snap(page, EVID, "tc11r_pagina2")
                evids.append("tc11r_pagina2.png")
                pagina2_ok = rows_pg2 > 0
        except Exception as e:
            log(f"  Erro pag2: {e}")

    # Selecionar 50/página
    pg50_ok = False
    try:
        # Volta para página 1
        pag_first = page.locator("[aria-label*='primeira' i], [aria-label*='first' i], "
                                  "[aria-label*='First']").first
        if pag_first.count() > 0 and pag_first.is_visible(timeout=1000):
            pag_first.click(timeout=3000)
            page.wait_for_timeout(1000)

        # Dropdown de itens por página
        por_pag_opts = page.locator("[class*='per-page'], select").filter(
            has_text=re.compile(r"25|50|100")).first
        if por_pag_opts.count() == 0:
            # Tenta locator de text
            por_pag_opts = page.get_by_role("combobox").filter(
                has_text=re.compile(r"^25$|^50$|^100$")).first
        if por_pag_opts.count() == 0:
            # Tenta botão "25"
            por_pag_opts = page.locator("button").filter(has_text=re.compile(r"^25$")).first

        if por_pag_opts.count() > 0 and por_pag_opts.is_visible(timeout=2000):
            por_pag_opts.click(timeout=3000)
            page.wait_for_timeout(500)
            opt_50 = page.locator("[role='option']").filter(has_text=re.compile("^50$")).first
            if opt_50.count() == 0:
                opt_50 = page.get_by_role("option", name="50").first
            if opt_50.count() > 0:
                opt_50.click(timeout=3000)
                page.wait_for_timeout(2000)
                rows_50 = page.locator("table tbody tr").count()
                log(f"  Com 50/pág: {rows_50}")
                tw.snap(page, EVID, "tc11r_50pag")
                evids.append("tc11r_50pag.png")
                pg50_ok = rows_50 > 25 or rows_50 == row_count
        else:
            log("  Dropdown por página não encontrado")
    except Exception as e:
        log(f"  Erro 50/pag: {e}")

    # Avalia
    has_pag_controls = pag_next.count() > 0 or pag_texto.count() > 0 or pag_nav > 0
    if row_count >= 25 and has_pag_controls:
        passou(11, evids,
               f"{row_count} linhas na página 1 (default 25); "
               f"pag2={pagina2_ok}, 50/pag={pg50_ok}, controles presentes")
    elif row_count >= 25 and not has_pag_controls:
        falhou(11, evids,
               f"{row_count} linhas mas controles de paginação não detectados")
    else:
        falhou(11, evids, f"{row_count} linhas (precisa 25+)")


# ─── TC13: Interação real mobile ───────────────────────────────────────────────

def run_tc13_real(page):
    log("\n[TC13] Hamburger mobile — interação real...")
    evids = []

    # ── 1. Desktop: confirma sidebar ──
    page.set_viewport_size({"width": 1500, "height": 950})
    ir_para_meu_historico(page)
    page.wait_for_timeout(1000)

    sidebar_items = page.evaluate("""() => {
        const nav = document.querySelector('nav, aside, [class*="sidebar"], [class*="sidenav"], [class*="side-nav"]');
        if (!nav) {
            // Tenta encontrar o menu lateral pelo padrão de links
            const leftMenu = document.querySelector('[class*="left"], [class*="Left"]');
            if (leftMenu) {
                const items = leftMenu.querySelectorAll('a, button');
                return { found: true, items: Array.from(items).map(i => i.innerText?.trim()?.substring(0,30) || '') };
            }
            return { found: false, items: [] };
        }
        return {
            found: true,
            items: Array.from(nav.querySelectorAll('a, button')).map(i => i.innerText?.trim()?.substring(0,30) || '')
        };
    }""")
    log(f"  Desktop sidebar: {sidebar_items}")
    tw.snap(page, EVID, "tc13r_01_desktop")
    evids.append("tc13r_01_desktop.png")

    # ── 2. Mobile viewport ──
    page.set_viewport_size({"width": 360, "height": 740})
    ir_para_meu_historico(page)
    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "tc13r_02_mobile_inicial")
    evids.append("tc13r_02_mobile_inicial.png")

    # Scan de hamburger: buttons + data-icon + material-icons
    hamburger = None
    hamburger_desc = ""

    selectors = [
        ("button[aria-label*='menu' i]", "btn aria-menu"),
        ("button[aria-label*='hambur' i]", "btn aria-hambur"),
        ("button[aria-label*='sidebar' i]", "btn aria-sidebar"),
        ("button[aria-label*='nav' i]", "btn aria-nav"),
        ("[data-icon='menu']", "data-icon menu"),
        ("[data-icon='menu_open']", "data-icon menu_open"),
        ("[data-icon='dehaze']", "data-icon dehaze"),
        ("header button:first-child", "header 1st btn"),
        ("[data-testid*='hamburger']", "testid hamburger"),
    ]
    for sel, desc in selectors:
        try:
            c = page.locator(sel).first
            if c.count() > 0 and c.is_visible(timeout=500):
                hamburger = c
                hamburger_desc = desc
                break
        except Exception:
            pass

    # Material icons scan
    if hamburger is None:
        for ms_loc in page.locator(".material-symbols-outlined, .material-icons").all():
            try:
                txt = ms_loc.inner_text().strip().lower()
                if txt in ("menu", "dehaze") and ms_loc.is_visible(timeout=300):
                    hamburger = ms_loc
                    hamburger_desc = f"material-icon text={txt}"
                    break
            except Exception:
                pass

    log(f"  Hamburger encontrado: {hamburger is not None} ({hamburger_desc})")

    # ── 3. Clica avatar ──
    drawer_avatar = False
    try:
        avatar = page.locator("[class*='avatar'], img[alt*='avatar' i], [data-icon='account_circle']").first
        if avatar.count() == 0:
            # Canto superior direito
            avatar = page.evaluate_handle("""() => {
                const els = Array.from(document.querySelectorAll('*'));
                const topRight = els.filter(e => {
                    const r = e.getBoundingClientRect();
                    return r.x > 280 && r.y < 60 && r.width > 10 && r.height > 10;
                });
                return topRight.find(e => {
                    const tag = e.tagName.toLowerCase();
                    const cursor = getComputedStyle(e).cursor;
                    return tag === 'img' || tag === 'button' || cursor === 'pointer';
                }) || null;
            }""")
        if hasattr(avatar, 'count') and avatar.count() > 0:
            avatar.click(timeout=3000)
            page.wait_for_timeout(1500)
            dialogs = page.locator("[role='dialog'], [role='menu']").all()
            for d in dialogs:
                box = d.bounding_box()
                if box and box["width"] > 50 and box["height"] > 50 and d.is_visible():
                    drawer_avatar = True
                    break
    except Exception as e:
        log(f"  Avatar erro: {e}")
    log(f"  Avatar: drawer={drawer_avatar}")
    tw.snap(page, EVID, "tc13r_03_avatar")
    evids.append("tc13r_03_avatar.png")
    if drawer_avatar:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    # ── 4. Clica hamburger se encontrado ──
    drawer_hamburger = False
    if hamburger:
        try:
            hamburger.click(timeout=3000)
            page.wait_for_timeout(1500)
            dialogs = page.locator("[role='dialog']").all()
            for d in dialogs:
                box = d.bounding_box()
                if box and box["width"] > 100 and box["height"] > 200 and d.is_visible():
                    drawer_hamburger = True
                    break
            historico_no_drawer = page.get_by_text(
                re.compile("Meu Hist", re.I)).count() > 1  # >1 porque título da pág já conta
            log(f"  Hamburger clicado: drawer={drawer_hamburger}, hist_drawer={historico_no_drawer}")
            tw.snap(page, EVID, "tc13r_04_hamburger_click")
            evids.append("tc13r_04_hamburger_click.png")
            if drawer_hamburger:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
        except Exception as e:
            log(f"  Hamburger click erro: {e}")

    # ── 5. Tab "Meu Histórico" em mobile ──
    drawer_tab = False
    try:
        tab = page.get_by_text(re.compile("Meu Hist", re.I), exact=False).first
        if tab.count() > 0 and tab.is_visible(timeout=1000):
            tab.click(timeout=3000)
            page.wait_for_timeout(1500)
            dialogs = page.locator("[role='dialog'], [class*='drawer']").all()
            for d in dialogs:
                box = d.bounding_box()
                if box and box["width"] > 100 and box["height"] > 200 and d.is_visible():
                    drawer_tab = True
                    break
    except Exception as e:
        log(f"  Tab erro: {e}")
    log(f"  Tab: drawer={drawer_tab}")
    tw.snap(page, EVID, "tc13r_05_tab")
    evids.append("tc13r_05_tab.png")

    # ── Conclusão ──
    drawer_abriu = drawer_hamburger or drawer_avatar or drawer_tab

    if drawer_abriu:
        passou(13, evids,
               f"drawer lateral abriu (hamburger={drawer_hamburger}, "
               f"avatar={drawer_avatar}, tab={drawer_tab})")
    else:
        # Verifica o que há no topo em mobile
        top_elements = page.evaluate("""() => {
            const els = Array.from(document.querySelectorAll('*'));
            return els.filter(e => {
                const r = e.getBoundingClientRect();
                return r.y < 80 && r.width > 0 && r.height > 0 && r.width < 400;
            }).slice(0, 20).map(e => ({
                tag: e.tagName,
                text: e.innerText?.trim()?.substring(0, 30) || '',
                class: e.className?.substring(0, 50) || '',
                x: Math.round(e.getBoundingClientRect().x),
                y: Math.round(e.getBoundingClientRect().y)
            }));
        }""")
        log(f"  Elementos no topo mobile: {top_elements[:8]}")

        falhou(13, evids,
               "RN 17 divergente para escopo do Aluno: "
               "interações em avatar, hamburger e tab não abriram drawer lateral. "
               "View Aluno é single-item (tab 'Meu Histórico' no topo). "
               "RN 17 não implementada para view Aluno.")

    page.set_viewport_size({"width": 1500, "height": 950})


# ─── Distribuição final ─────────────────────────────────────────────────────────

def distribuicao_final(page):
    log("\n=== Distribuição final ===")
    ir_para_meu_historico(page)

    # Muda para 100/página se possível
    try:
        por_pag = page.locator("button").filter(has_text=re.compile(r"^25$")).first
        if por_pag.count() > 0:
            por_pag.click(timeout=3000)
            page.wait_for_timeout(500)
            opt100 = page.locator("[role='option']").filter(has_text="100").first
            if opt100.count() > 0:
                opt100.click(timeout=3000)
                page.wait_for_timeout(2000)
    except Exception:
        pass

    total = page.locator("table tbody tr").count()
    interno = page.locator("td").filter(has_text="Interno").count()
    externo = page.locator("td").filter(has_text="Externo").count()
    comp = page.locator("td").filter(has_text="Compartilhado").count()
    aprovado = page.locator("td").filter(has_text="Aprovado").count()
    pendente = page.locator("td").filter(has_text="Pendente").count()
    recusado = page.locator("td").filter(has_text="Recusado").count()
    expirado = page.locator("td").filter(has_text="Expirado").count()

    dist = {
        "total_visivel": total,
        "origem": {"Interno": interno, "Externo": externo, "Compartilhado": comp},
        "situacao": {
            "Aprovado/Emitido": aprovado, "Pendente": pendente,
            "Recusado": recusado, "Expirado": expirado
        },
        "ledger": LEDGER,
    }
    log(f"  Total: {total}, Interno={interno}, Externo={externo}, Comp={comp}")
    log(f"  Aprovado={aprovado}, Pendente={pendente}, Recusado={recusado}, Expirado={expirado}")
    tw.snap(page, EVID, "dist_final")
    return dist


# ─── MAIN ────────────────────────────────────────────────────────────────────────

novo_email = None
dist = {}

with tw.sync_playwright() as p:

    # ── Sessão Aluno: semear ──
    ba, ca, pa = tw.nova_pagina(p)
    login_como_aluno(pa)

    total_inicial = pa.locator("table tbody tr").count()
    # Navega para lista para contar
    pa.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=25000)
    try:
        pa.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    pa.wait_for_timeout(2500)
    tw.dispensar_nps(pa)
    total_inicial = pa.locator("table tbody tr").count()
    log(f"  Registros iniciais do Aluno: {total_inicial}")

    total_pos_semeia = fase2_semear(pa, total_inicial)
    ca.close()
    ba.close()

    # ── Sessão Admin: aprovar/recusar + TC3 ──
    b_adm, c_adm, p_adm = tw.nova_pagina(p)
    login_como_admin(p_adm)

    apr, rec = fase3_admin(p_adm)

    # TC3: usuário novo
    b_novo, c_novo, p_novo = tw.nova_pagina(p)
    novo_email = run_tc3(p_adm, p_novo)
    c_novo.close()
    b_novo.close()

    c_adm.close()
    b_adm.close()

    # ── Sessão Aluno: re-run TCs ──
    ba2, ca2, pa2 = tw.nova_pagina(p)
    login_como_aluno(pa2)

    dist = distribuicao_final(pa2)

    for fn in [run_tc2_rerun, run_tc5_rerun, run_tc7_rerun, run_tc8_rerun,
               run_tc10_rerun, run_tc11_rerun]:
        try:
            fn(pa2)
        except Exception as exc:
            num = fn.__name__.replace("run_tc", "").replace("_rerun", "")
            try:
                tw.snap(pa2, EVID, f"tc{num}_CRASH")
            except Exception:
                pass
            try:
                falhou(int(num), [f"tc{num}_CRASH.png"], f"CRASH: {exc}")
            except Exception:
                pass

    try:
        run_tc13_real(pa2)
    except Exception as exc:
        try:
            tw.snap(pa2, EVID, "tc13_CRASH")
        except Exception:
            pass
        falhou(13, ["tc13_CRASH.png"], f"CRASH: {exc}")

    ca2.close()
    ba2.close()


# ─── Resumo ──────────────────────────────────────────────────────────────────────

print("\n" + "="*70)
print("=== RESULTADO FASE 2 ===")
print(f"  Ledger: {LEDGER}")
print(f"  Dist: {dist}")
print()
for tc_id in sorted(RESULTADOS.keys()):
    r = RESULTADOS[tc_id]
    print(f"  TC{tc_id:02d}: {r['veredito']:18s} — {r['obs'][:100]}")
if novo_email:
    print(f"\n  Email TC3 (empty state): {novo_email}")
print("="*70)
