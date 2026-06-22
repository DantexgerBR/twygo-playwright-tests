"""fechamento_qa11_v2.py — TC3 + Seed + TC11.

Estrategia simplificada:
- TC3: Tenta logar como usuario existente da org que provavelmente tem zero registros.
  Org registrosf2 tem: julia@sophia.tech.com.br, vanessa@sophia.tech.com.br, etc.
  Senha padrao da org: 123456.
  Falha => reporta BLOQUEADO com justificativa.
- Seed: Usa dante (27+ registros) para TC11.
- TC11: Valida paginacao 25/50/100.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
DANTE_EMAIL = "dante.tavares@twygo.com"
DANTE_SENHA = "123456"
ORG_ID = "37079"

# Candidatos a usuario com ZERO registros na org
CANDIDATOS_TC3 = [
    ("julia@sophia.tech.com.br",   "123456"),
    ("vanessa@sophia.tech.com.br", "123456"),
    ("gabriel@sophia.tech.com.br", "123456"),
    ("carla@sophia.tech.com.br",   "123456"),
    ("danilo@sophia.tech.com.br",  "123456"),
    ("usuario.trial@sophia.tech.com.br", "123456"),
    ("richard.sebold@twygo.com",   "123456"),
]

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


def bloqueado(tc_id, evidencias, motivo):
    RESULTADOS[tc_id] = {"veredito": "BLOQUEADO", "evidencias": evidencias, "obs": motivo}
    log(f"  [TC{tc_id}] BLOQUEADO — {motivo}")


def ir_meu_historico(page):
    url = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)


# ─── TC3: Tentar usuario existente sem registros ───────────────────────────────

def run_tc3(p):
    log("\n=== TC3: Empty state ===")
    evids = []

    for email, senha in CANDIDATOS_TC3:
        log(f"  Tentando: {email}")

        browser, ctx, page = tw.nova_pagina(p)
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("#user_email", timeout=15000)
            page.fill("#user_email", email)
            page.fill("#user_password", senha)
            page.click("#user_submit")
            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            if "/users/login" in page.url or "/login" in page.url:
                log(f"    Login falhou — senha errada ou usuario invalido")
                continue

            log(f"    Login OK: {page.url[:50]}")

            # Navega para Meu historico
            ir_meu_historico(page)
            rows = page.locator("table tbody tr").count()
            log(f"    Registros: {rows}")

            if rows > 0:
                log(f"    Tem {rows} registros — descartando (precisa zero)")
                tw.snap(page, EVID, f"fechamento_tc3_cand_{email.split('@')[0]}_nao_zero")
                continue

            # Zero registros — valida TC3!
            log(f"    ZERO registros — validando TC3!")
            tw.snap(page, EVID, "fechamento_tc3_empty")
            evids.append("fechamento_tc3_empty.png")

            msg_exata = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
            has_empty = page.get_by_text(msg_exata).count() > 0
            log(f"    Mensagem empty state: {has_empty}")

            # KPI cards
            kpi_labels = ["Emitidos", "Expirados", "Pendentes", "Recusados"]
            kpi_found = {}
            kpi_values = {}

            for label in kpi_labels:
                try:
                    card = page.locator(
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
                except Exception:
                    kpi_found[label] = False
                    kpi_values[label] = None

            log(f"    KPIs: {kpi_found}")
            log(f"    KPI valores: {kpi_values}")

            tw.snap(page, EVID, "fechamento_tc3_kpis")
            evids.append("fechamento_tc3_kpis.png")

            all_4_found = all(kpi_found.get(l, False) for l in kpi_labels)
            any_nonzero = any(kpi_values.get(l, 0) not in (0, None) for l in kpi_labels)

            if has_empty and rows == 0 and all_4_found and not any_nonzero:
                passou(3, evids,
                       f"mensagem exata presente; 0 linhas; 4 KPIs=0 ({kpi_values}); "
                       f"usuario={email}")
            elif not has_empty and rows == 0:
                falhou(3, evids,
                       f"tabela vazia mas mensagem exata NAO encontrada "
                       f"(usuario={email})")
            elif not all_4_found:
                missing = [l for l in kpi_labels if not kpi_found.get(l)]
                falhou(3, evids, f"KPIs ausentes: {missing} (usuario={email})")
            elif any_nonzero:
                falhou(3, evids, f"KPIs nao zerados: {kpi_values}")
            else:
                falhou(3, evids, f"fallback: msg={has_empty}, rows={rows}, kpi={kpi_values}")
            return  # TC3 avaliado (independente do veredito)
        finally:
            ctx.close()
            browser.close()

    # Nenhum candidato funcionou
    bloqueado(3, [],
              "nenhum usuario candidato acessivel com senha 123456 "
              "E com zero registros — impossivel validar TC3 sem criar usuario via admin")


# ─── Criar 1 registro ─────────────────────────────────────────────────────────

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
    except Exception as e:
        log(f"    #{input_id} erro: {e}")
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

    # Tipo experiencia — seleciona primeira disponivel
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

    # Categorias
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

    # Carga horaria
    try:
        page.locator("#workload_seconds").scroll_into_view_if_needed()
        page.locator("#workload_seconds").fill(carga_hhmmss)
    except Exception:
        pass

    # Data de termino
    try:
        page.locator("#endDate").scroll_into_view_if_needed()
        page.locator("#endDate").fill(data_iso)
        page.wait_for_timeout(150)
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
            try:
                page.wait_for_url(
                    re.compile(r"/records(\?|$)"),
                    timeout=12000
                )
                return True
            except Exception:
                page.wait_for_timeout(3000)
                return "/records" in page.url and "/records/new" not in page.url
    except Exception as e:
        log(f"    salvar erro: {e}")
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
    log("\n=== Semeando (meta: >= 26 total) ===")
    ir_meu_historico(page)
    total_atual = page.locator("table tbody tr").count()
    log(f"  Inicial visivel: {total_atual}", flush=True)

    if total_atual >= 25:
        log("  Ja tem 25+ — verificando total com paginacao")
        # Conta paginas
        return 0, total_atual

    semeados = 0
    falhas = 0
    META = 26

    for i, (titulo, provedor, carga, data) in enumerate(TITULOS):
        if total_atual + semeados >= META:
            log(f"  Meta {META} atingida")
            break
        log(f"  [{i+1:02d}] {titulo}", flush=True)
        ok = criar_registro(page, titulo, provedor, carga, data)
        if ok:
            semeados += 1
            log(f"    OK #{semeados}")
        else:
            falhas += 1
            log(f"    FALHOU")

    ir_meu_historico(page)
    page.wait_for_timeout(1500)
    rows = page.locator("table tbody tr").count()
    tw.snap(page, EVID, "fechamento_seed_pos_semeia")
    log(f"  Resultado: {semeados} OK, {falhas} falhas, visivel={rows}")
    return semeados, rows


# ─── TC11: Paginacao ───────────────────────────────────────────────────────────

def run_tc11(page):
    log("\n=== TC11: Paginacao 25/50/100 ===", flush=True)
    evids = []
    ir_meu_historico(page)

    rows_p1 = page.locator("table tbody tr").count()
    log(f"  Linhas pag1: {rows_p1}")
    tw.snap(page, EVID, "fechamento_tc11_pag1")
    evids.append("fechamento_tc11_pag1.png")

    if rows_p1 < 25:
        falhou(11, evids, f"apenas {rows_p1} linhas na pag1 (precisa 25+)")
        return

    default_25 = rows_p1 == 25

    # Detecta controles de paginacao
    per_page_sel = None
    for sel in ["select", "nav select", "[class*='pagination'] select"]:
        try:
            s = page.locator(sel).first
            if s.count() > 0 and s.is_visible(timeout=1500):
                # Verifica se tem opcoes de paginacao
                opts = s.evaluate("el => Array.from(el.options).map(o => o.value)")
                if any(v in ["25", "50", "100"] for v in opts):
                    per_page_sel = s
                    log(f"  Select por-pagina encontrado: {sel}, opcoes={opts}")
                    break
        except Exception:
            pass

    por_pag_txt = page.get_by_text(re.compile(r"por página", re.I)).first
    log(f"  per_page_sel={per_page_sel is not None}, por_pag_txt={por_pag_txt.count()>0}")

    tw.snap(page, EVID, "fechamento_tc11_controles")
    evids.append("fechamento_tc11_controles.png")

    has_pag = per_page_sel is not None or por_pag_txt.count() > 0

    # Proxima pagina via JS (mais confiavel)
    pagina2_ok = False
    rows_p2 = 0
    try:
        clicou = page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            // Procura botao ">", "›", aria-label próxima
            const b = btns.find(b =>
                b.innerText?.trim() === '>' ||
                b.getAttribute('aria-label')?.toLowerCase().includes('pr') ||
                b.getAttribute('aria-label')?.toLowerCase().includes('next')
            );
            if (b && !b.disabled) { b.click(); return true; }
            return false;
        }""")
        if clicou:
            page.wait_for_timeout(2000)
            rows_p2 = page.locator("table tbody tr").count()
            log(f"  Pag2: {rows_p2} linhas")
            tw.snap(page, EVID, "fechamento_tc11_pag2")
            evids.append("fechamento_tc11_pag2.png")
            pagina2_ok = rows_p2 > 0
        else:
            log("  Botao proxima pagina nao encontrado via JS")
    except Exception as e:
        log(f"  Pag2 erro: {e}")

    # Volta pag 1
    try:
        page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(b =>
                b.innerText?.trim() === '<<' || b.innerText?.trim() === '«' ||
                b.getAttribute('aria-label')?.toLowerCase().includes('primeira') ||
                b.getAttribute('aria-label')?.toLowerCase().includes('first')
            );
            if (b) b.click();
        }""")
        page.wait_for_timeout(1000)
    except Exception:
        ir_meu_historico(page)

    # 50/pagina via select
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

    # 100/pagina
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

    log(f"\n  Resumo: pag1={rows_p1} (default25={default_25}), pag2={pagina2_ok}({rows_p2}), "
        f"50={pg50_ok}({rows_50}), 100={pg100_ok}({rows_100})")

    if default_25 and has_pag and pagina2_ok and pg50_ok and pg100_ok:
        passou(11, evids,
               f"pag1=25; pag2={rows_p2}; 50/pag={rows_50}; 100/pag={rows_100}")
    elif default_25 and has_pag and pagina2_ok and pg50_ok:
        falhou(11, evids,
               f"pag1=25 OK, pag2 OK({rows_p2}), 50/pag OK({rows_50}), "
               f"MAS 100/pag NAO verificado ({rows_100})")
    elif default_25 and has_pag and pagina2_ok:
        falhou(11, evids,
               f"pag1=25 OK, pag2 OK({rows_p2}), MAS 50/100 nao testavel")
    elif default_25 and has_pag:
        falhou(11, evids,
               f"pag1=25 OK, controles OK, MAS pag2 NAO funcionou ({rows_p2})")
    else:
        falhou(11, evids,
               f"pag1={rows_p1}, default_25={default_25}, has_pag={has_pag}")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60, flush=True)
    log("fechamento_qa11_v2.py", flush=True)
    log(f"Org: {BASE_URL} / ID: {ORG_ID}", flush=True)
    log("=" * 60, flush=True)

    # TC3 — em browser separado para cada candidato
    with tw.sync_playwright() as p:
        run_tc3(p)

    # Seed + TC11 — Aluno dante
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            log("\n--- Login Aluno (dante) ---", flush=True)
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("#user_email", timeout=15000)
            page.fill("#user_email", DANTE_EMAIL)
            page.fill("#user_password", DANTE_SENHA)
            page.click("#user_submit")
            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            log(f"  Logado: {page.url[:60]}", flush=True)

            semeados, rows = semear(page)
            log(f"  Semeados: {semeados}, visivel: {rows}", flush=True)

            run_tc11(page)
        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60, flush=True)
    log("RESULTADOS FINAIS:", flush=True)
    for tc, r in sorted(RESULTADOS.items()):
        log(f"  TC{tc}: {r['veredito']} — {r['obs']}", flush=True)
    log("=" * 60, flush=True)


if __name__ == "__main__":
    main()
