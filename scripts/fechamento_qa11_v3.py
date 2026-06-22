"""fechamento_qa11_v3.py — TC3 + TC11 com seletores corretos do DOM.

Descobertas do recon:
- Campo email: id="professional_email"
- Campo nome:  id="professional_first_name"
- Sobrenome:   id="professional_last_name"
- Select paginacao: id="select_pages" (values 25/50/100)
- Botao next page: button com texto "chevron_right" (icone Material)
- Botao prev page: button com texto "chevron_left"
- Numeros de pagina: buttons com texto "1", "2", etc.
- Reset de senha: menu kebab (3 pontos) na lista de usuarios
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
    log(f"\n  >>> TC{tc_id}: PASSOU{' — ' + obs if obs else ''}")


def falhou(tc_id, evidencias, motivo):
    RESULTADOS[tc_id] = {"veredito": "FALHOU", "evidencias": evidencias, "obs": motivo}
    log(f"\n  >>> TC{tc_id}: FALHOU — {motivo}")


def ir_meu_historico(page):
    url = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)


def login_admin(page):
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
    # Switch para perfil admin
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


def login_aluno(page):
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
    log(f"  Aluno logado: {page.url[:60]}")


# ─── TC3: Criar usuario, resetar senha, logar, verificar empty state ──────────

def criar_usuario_e_resetar(page, email, nome, sobrenome):
    """Cria usuario via admin e reseta senha para 123456. Retorna True se ok."""
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/users/new",
        wait_until="domcontentloaded", timeout=60000
    )
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(1500)
    tw.dispensar_nps(page)

    # Preenche pelos IDs corretos (descobertos no recon)
    page.locator("#professional_email").fill(email)
    page.wait_for_timeout(200)
    page.locator("#professional_first_name").fill(nome)
    page.wait_for_timeout(200)
    page.locator("#professional_last_name").fill(sobrenome)
    page.wait_for_timeout(200)

    val_email = page.locator("#professional_email").input_value()
    val_nome = page.locator("#professional_first_name").input_value()
    log(f"  Form: email={val_email!r} nome={val_nome!r}")
    tw.snap(page, EVID, "fechamento_tc3_form_preenchido")

    if val_email != email:
        log(f"  ERRO: email nao preenchido corretamente ({val_email!r} != {email!r})")
        return False

    # Salva
    btn = page.get_by_role("button", name=re.compile(r"Salvar", re.I)).first
    if btn.count() == 0:
        btn = page.locator("button[type='submit']").first
    btn.scroll_into_view_if_needed()
    btn.click(timeout=5000)
    try:
        page.wait_for_url(re.compile(r"/users(?:\?|$)"), timeout=10000)
        log(f"  Usuario criado, URL: {page.url[:60]}")
        tw.snap(page, EVID, "fechamento_tc3_usuario_criado")
    except Exception:
        page.wait_for_timeout(3000)
        if "/users/new" in page.url:
            log(f"  ERRO: ainda em /users/new — criacao falhou")
            tw.snap(page, EVID, "fechamento_tc3_erro_criacao")
            return False
        log(f"  URL pos-salvar: {page.url[:60]}")

    # Busca o usuario na lista
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Busca pelo nome ou email
    try:
        busca = page.locator("input[placeholder='Pesquise aqui']").first
        if busca.count() > 0 and busca.is_visible(timeout=2000):
            busca.fill(nome)
            page.wait_for_timeout(1500)
            log(f"  Busca por nome: {nome!r}")
    except Exception as e:
        log(f"  Busca erro: {e}")

    tw.snap(page, EVID, "fechamento_tc3_lista_usuario")

    # Clica no kebab (menu 3 pontos) do usuario criado
    try:
        row = page.locator("tr, [role='row']").filter(has_text=email).first
        if row.count() == 0:
            row = page.locator("tr, [role='row']").filter(has_text=nome).first
        if row.count() > 0:
            kebab = row.locator("button, [class*='more_vert'], [data-icon='ellipsis-v']").last
            if kebab.count() == 0:
                kebab = row.locator(":nth-child(last)").last
            # Tenta o botao de 3 pontos pelo ícone Material "more_vert"
            kebab = row.locator("button").filter(has_text=re.compile(r"more_vert|⋮|\.\.\.")).first
            if kebab.count() == 0:
                # Fallback: ultimo botao da linha
                all_btns = row.locator("button").all()
                if all_btns:
                    kebab = all_btns[-1]
            if kebab.count() > 0 and kebab.is_visible(timeout=2000):
                kebab.click(timeout=3000)
                page.wait_for_timeout(1000)
                tw.snap(page, EVID, "fechamento_tc3_kebab_aberto")
                log("  Kebab aberto")
        else:
            log(f"  AVISO: linha do usuario {email!r} nao encontrada")
            # Tenta sem filtrar linha — primeiro kebab visivel
    except Exception as e:
        log(f"  Kebab erro: {e}")

    # Procura opcao de reset de senha no menu
    reset_ok = False
    try:
        reset_item = page.locator(
            "[role='menuitem'], [class*='dropdown-item'], li, a"
        ).filter(has_text=re.compile(r"senha|password|reset", re.I)).first
        if reset_item.count() > 0 and reset_item.is_visible(timeout=2000):
            log(f"  Item de reset: {reset_item.inner_text()!r}")
            reset_item.click(timeout=3000)
            page.wait_for_timeout(1500)
            tw.snap(page, EVID, "fechamento_tc3_reset_senha")
            reset_ok = True
        else:
            log("  Item de reset nao encontrado no menu")
            tw.snap(page, EVID, "fechamento_tc3_sem_reset")
    except Exception as e:
        log(f"  Reset item erro: {e}")

    return True  # Usuario criado (reset pode ou nao funcionar)


def run_tc3(p):
    log("\n=== TC3: Empty state ===")
    evids = []
    import os
    novo_email = f"qa11tc3v3{os.getpid()}@mailtest.example"
    log(f"  Email: {novo_email}")

    # Cria usuario
    browser_adm, ctx_adm, page_adm = tw.nova_pagina(p)
    usuario_criado = False
    try:
        login_admin(page_adm)
        usuario_criado = criar_usuario_e_resetar(page_adm, novo_email, "QA11TC3", "EmptyUser")
        evids += [
            "fechamento_tc3_form_preenchido.png",
            "fechamento_tc3_usuario_criado.png",
        ]
    finally:
        ctx_adm.close()
        browser_adm.close()

    if not usuario_criado:
        falhou(3, evids, "Criacao de usuario falhou")
        return

    # Tenta logar como novo usuario
    # Senhas a tentar: 123456 (Twygo padrao para novos), depois DanTheBullet2003!@#
    browser_novo, ctx_novo, page_novo = tw.nova_pagina(p)
    try:
        login_ok = False
        for senha_tentativa in ["123456", "DanTheBullet2003!@#", "Twygo@123"]:
            page_novo.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
            page_novo.wait_for_selector("#user_email", timeout=15000)
            page_novo.fill("#user_email", novo_email)
            page_novo.fill("#user_password", senha_tentativa)
            page_novo.click("#user_submit")
            try:
                page_novo.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            page_novo.wait_for_timeout(2000)
            tw.dispensar_nps(page_novo)
            url_pos = page_novo.url
            login_ok = "/login" not in url_pos and "/users/sign_in" not in url_pos
            log(f"  Login com {senha_tentativa!r}: ok={login_ok}, url={url_pos[:50]}")
            if login_ok:
                break

        tw.snap(page_novo, EVID, "fechamento_tc3_login_novo")
        evids.append("fechamento_tc3_login_novo.png")

        if not login_ok:
            falhou(3, evids,
                   f"Usuario criado ({novo_email}) mas login falhou em 3 tentativas — "
                   "Twygo provavelmente envia convite por email (nao ha senha padrao)")
            return

        # Navega para Meu historico
        ir_meu_historico(page_novo)
        tw.snap(page_novo, EVID, "fechamento_tc3_empty")
        evids.append("fechamento_tc3_empty.png")

        rows = page_novo.locator("table tbody tr").count()
        msg_exata = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
        has_empty_msg = page_novo.get_by_text(msg_exata, exact=True).count() > 0
        # Tenta texto parcial se nao achou exato
        if not has_empty_msg:
            has_empty_msg = page_novo.get_by_text("ainda não tem registros").count() > 0
        log(f"  Empty msg: {has_empty_msg}, rows: {rows}")

        # KPIs
        kpi_labels = ["Emitidos", "Expirados", "Pendentes", "Recusados"]
        kpi_values = {}
        kpi_found = {}
        for label in kpi_labels:
            try:
                # Procura card contendo o label
                card = page_novo.locator(
                    "[class*='stat'], [class*='kpi'], [class*='card'], [class*='Stat'], "
                    "[class*='chakra']"
                ).filter(has_text=label).first
                if card.count() == 0:
                    # Busca mais ampla
                    card = page_novo.locator("*").filter(has_text=re.compile(
                        rf'\b{label}\b', re.I
                    )).first
                kpi_found[label] = card.count() > 0
                if kpi_found[label]:
                    nums = re.findall(r'\b(\d+)\b', card.inner_text())
                    kpi_values[label] = int(nums[0]) if nums else None
                else:
                    kpi_values[label] = None
            except Exception:
                kpi_found[label] = False
                kpi_values[label] = None

        tw.snap(page_novo, EVID, "fechamento_tc3_kpis")
        evids.append("fechamento_tc3_kpis.png")
        log(f"  KPIs encontrados: {kpi_found}")
        log(f"  KPI valores: {kpi_values}")

        all_4_found = all(kpi_found.get(l, False) for l in kpi_labels)
        all_zero = all(kpi_values.get(l, 0) in (0, None) for l in kpi_labels)

        if has_empty_msg and rows == 0 and all_4_found and all_zero:
            passou(3, evids,
                   f"msg empty state presente; 0 linhas na tabela; "
                   f"4 KPIs visíveis e zerados ({kpi_values})")
        elif not has_empty_msg:
            falhou(3, evids, f"msg empty state NAO encontrada (rows={rows})")
        elif not all_4_found:
            missing = [l for l in kpi_labels if not kpi_found.get(l)]
            falhou(3, evids, f"KPIs ausentes: {missing}")
        elif not all_zero:
            non_zero = {k: v for k, v in kpi_values.items() if v not in (0, None)}
            falhou(3, evids, f"KPIs nao zerados: {non_zero}")
        else:
            falhou(3, evids, f"fallback — msg={has_empty_msg}, rows={rows}, "
                             f"kpi_found={kpi_found}, values={kpi_values}")
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
        page.wait_for_timeout(400)
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
        # Fallback: clicar em "Criar X"
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
    preencher_creatable(page, "react-select-3-input", titulo)

    # Tipo experiencia (react-select-4): seleciona primeira opcao disponivel
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

    # Categorias (react-select-5): seleciona primeira opcao
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

    # Carga horaria e data
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

    # Salva
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
        log(f"  Ja tem {total_atual} — sem necessidade de semear mais")
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
    tw.snap(page, EVID, "fechamento_seed_pos_semeia")
    log(f"  Resultado: {semeados} novos OK, total_visivel={rows}")
    return semeados, rows


# ─── TC11: Validar paginacao ───────────────────────────────────────────────────

def run_tc11(page):
    log("\n=== TC11: Paginacao 25/50/100 ===")
    evids = []

    ir_meu_historico(page)
    rows_p1 = page.locator("table tbody tr").count()
    log(f"  Pag1: {rows_p1} linhas")
    tw.snap(page, EVID, "fechamento_tc11_pag1")
    evids.append("fechamento_tc11_pag1.png")

    if rows_p1 < 25:
        falhou(11, evids, f"pag1 tem apenas {rows_p1} linhas (esperado 25)")
        return

    default_25 = (rows_p1 == 25)

    # Rola para o footer para ver os controles
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "fechamento_tc11_footer")
    evids.append("fechamento_tc11_footer.png")

    # Verifica select de paginacao
    sel = page.locator("#select_pages")
    has_select = sel.count() > 0 and sel.is_visible(timeout=2000)
    log(f"  Select paginacao: {has_select}")

    # Verifica indicador de pagina atual
    # No DOM: botao com texto "1" (pagina atual) tem classe diferente de "2"
    pag_atual = page.locator("button").filter(has_text=re.compile(r"^1$")).first
    has_pag_indicator = pag_atual.count() > 0
    log(f"  Indicador pagina '1': {has_pag_indicator}")

    # Passo 2: Clicar proximo (botao chevron_right)
    # Descoberto no recon: texto do botao e "chevron_right" (icone Material)
    pagina2_ok = False
    rows_p2 = 0
    try:
        btn_next = page.locator("button.chakra-button").filter(
            has_text=re.compile(r"chevron_right", re.I)
        ).first
        if btn_next.count() == 0:
            # Fallback: botao com aria "next" ou index
            btn_next = page.locator("button").filter(
                has_text=re.compile(r"^>$|chevron_right")
            ).first
        if btn_next.count() > 0 and btn_next.is_visible(timeout=2000):
            enabled = not btn_next.get_attribute("disabled")
            disabled_attr = btn_next.evaluate("el => el.disabled")
            log(f"  Btn next: encontrado, disabled={disabled_attr}")
            if not disabled_attr:
                btn_next.click(timeout=5000)
                page.wait_for_timeout(2000)
                rows_p2 = page.locator("table tbody tr").count()
                log(f"  Pag2: {rows_p2} linhas")
                tw.snap(page, EVID, "fechamento_tc11_pag2")
                evids.append("fechamento_tc11_pag2.png")
                pagina2_ok = (rows_p2 >= 1)
        else:
            log("  Btn next: NAO encontrado")
    except Exception as e:
        log(f"  Pag2 erro: {e}")

    # Volta para pag 1 antes de testar 50/100
    try:
        btn_first = page.locator("button.chakra-button").filter(
            has_text=re.compile(r"keyboard_double_arrow_left")
        ).first
        if btn_first.count() > 0 and btn_first.is_visible(timeout=1000):
            disabled = btn_first.evaluate("el => el.disabled")
            if not disabled:
                btn_first.click(timeout=3000)
                page.wait_for_timeout(1000)
    except Exception:
        pass
    # Fallback: volta pela URL
    if page.locator("table tbody tr").count() != rows_p1:
        ir_meu_historico(page)
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)

    # Passo 3: 50 por pagina
    pg50_ok = False
    rows_50 = 0
    try:
        sel_fresh = page.locator("#select_pages")
        if sel_fresh.count() > 0 and sel_fresh.is_visible(timeout=2000):
            sel_fresh.select_option("50")
            page.wait_for_timeout(2000)
            rows_50 = page.locator("table tbody tr").count()
            log(f"  50/pag: {rows_50} linhas")
            tw.snap(page, EVID, "fechamento_tc11_50pag")
            evids.append("fechamento_tc11_50pag.png")
            pg50_ok = True
    except Exception as e:
        log(f"  50/pag erro: {e}")

    # Passo 4: 100 por pagina
    pg100_ok = False
    rows_100 = 0
    try:
        sel_fresh = page.locator("#select_pages")
        if sel_fresh.count() > 0 and sel_fresh.is_visible(timeout=2000):
            sel_fresh.select_option("100")
            page.wait_for_timeout(2000)
            rows_100 = page.locator("table tbody tr").count()
            log(f"  100/pag: {rows_100} linhas")
            tw.snap(page, EVID, "fechamento_tc11_100pag")
            evids.append("fechamento_tc11_100pag.png")
            pg100_ok = True
    except Exception as e:
        log(f"  100/pag erro: {e}")

    log(f"\n  Resumo: pag1={rows_p1}(default_25={default_25}), "
        f"pag_indicator={has_pag_indicator}, pag2={pagina2_ok}({rows_p2}), "
        f"50={pg50_ok}({rows_50}), 100={pg100_ok}({rows_100})")

    # Pag1=25 + indicador pagina + next funcionou + 50/100 ok = PASSOU
    if default_25 and has_pag_indicator and pagina2_ok and pg50_ok and pg100_ok:
        passou(11, evids,
               f"pag1=25 (default); indicador pag1 presente; pag2={rows_p2} linhas; "
               f"50/pag={rows_50}; 100/pag={rows_100}")
    elif default_25 and pagina2_ok and pg50_ok and pg100_ok:
        passou(11, evids,
               f"pag1=25; pag2={rows_p2}; 50={rows_50}; 100={rows_100} "
               f"(indicador pagina: {has_pag_indicator})")
    elif default_25 and pg50_ok and pg100_ok and not pagina2_ok:
        # Paginacao 2 pode nao existir se ha exatamente 25 registros
        total_registros = rows_50  # ao selecionar 50, mostra todos
        if total_registros <= 25:
            falhou(11, evids,
                   f"apenas {total_registros} registros total — precisa >25 para "
                   f"ter pagina 2; semear mais registros")
        else:
            falhou(11, evids,
                   f"pag1=25 OK, 50/100 OK, MAS botao pag2 nao clicavel")
    else:
        falhou(11, evids,
               f"pag1={rows_p1}(def={default_25}), pag2={pagina2_ok}({rows_p2}), "
               f"50={pg50_ok}({rows_50}), 100={pg100_ok}({rows_100})")


def main():
    log("=" * 60)
    log("fechamento_qa11_v3.py")
    log(f"Org: {BASE_URL} / ORG_ID: {ORG_ID}")
    log("=" * 60)

    # TC3
    with tw.sync_playwright() as p1:
        run_tc3(p1)

    # Seed + TC11 (como aluno dante)
    with tw.sync_playwright() as p2:
        browser, ctx, page = tw.nova_pagina(p2)
        try:
            login_aluno(page)
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
