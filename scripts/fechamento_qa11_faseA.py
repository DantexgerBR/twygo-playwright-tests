"""fechamento_qa11_faseA.py — Gate + TC3 empty state na org registrosf2.

Fase A: roda ANTES de semear qualquer registro.
- GATE: loga como Aluno (dante.tavares), abre "Meu historico", confirma feature
  habilitada + visao Aluno + conta registros atuais.
- TC3: se Aluno tiver 0 registros, valida empty state diretamente.
         se Aluno ja tiver registros, reporta BLOQUEADO (nao cria usuario novo aqui).

Org: registrosf2.stage.twygoead.com
Senha aluno: 123456 (hardcoded — org nova, nao usa .env)
Sem admin redirect (visao Aluno).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

# ─── Constantes da org nova (NÃO usa .env para esta org) ─────────────────────
BASE_URL = "https://registrosf2.stage.twygoead.com"
ALUNO_EMAIL = "dante.tavares@twygo.com"
ALUNO_SENHA = "123456"

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


def bloqueado(tc_id, evidencias, motivo):
    RESULTADOS[tc_id] = {"veredito": "BLOQUEADO", "evidencias": evidencias, "obs": motivo}
    log(f"  [TC{tc_id}] BLOQUEADO — {motivo}")


def login_aluno(page):
    """Loga como Aluno (sem switch admin)."""
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", ALUNO_EMAIL)
    page.fill("#user_password", ALUNO_SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    if "/users/login" in page.url:
        log("ERRO: login falhou (sessao concorrente ou credencial incorreta)")
        log(f"  URL atual: {page.url}")
        raise SystemExit("Login Aluno falhou — verificar sessao concorrente.")
    log(f"  Login OK: {page.url[:70]}")


def descobrir_org_id(page):
    """Extrai org_id da URL atual (/o/<id>/)."""
    m = re.search(r"/o/(\d+)/", page.url)
    if m:
        return m.group(1)
    # Tenta navegar para a home e re-capturar
    try:
        page.goto(f"{BASE_URL}/dashboard_students", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
        m = re.search(r"/o/(\d+)/", page.url)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "DESCONHECIDO"


def ir_meu_historico(page, org_id):
    """Navega para a tela 'Meu historico' do Aluno."""
    url = f"{BASE_URL}/o/{org_id}/records?in_use_mode_layout=true"
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)
    # Aguarda a tela renderizar (tabela OU mensagem empty state OU KPI cards)
    try:
        page.wait_for_selector("table, [class*='stat'], [class*='kpi']", timeout=8000)
    except Exception:
        pass


# ─── GATE ─────────────────────────────────────────────────────────────────────

def run_gate(page):
    log("\n=== GATE: Feature + visao Aluno + contagem de registros ===")

    login_aluno(page)

    # Descobre org_id
    org_id = descobrir_org_id(page)
    log(f"  Org ID detectado: {org_id}")

    # Navega para Meu historico
    ir_meu_historico(page, org_id)
    tw.snap(page, EVID, "fechamento_gate_meu_historico")

    # (a) Feature habilitada?
    titulo_page = page.title()
    url_ok = "/records" in page.url
    heading = ""
    for sel in ["h1", "h2", "[class*='heading']", "[class*='title']"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=1000):
                heading = el.inner_text().strip()
                break
        except Exception:
            pass

    sidebar_item = page.get_by_text(re.compile(r"Meu hist.rico", re.I)).count() > 0
    feature_ok = url_ok or sidebar_item

    log(f"  URL: {page.url[:70]}")
    log(f"  Titulo pagina: {titulo_page}")
    log(f"  Heading: {heading}")
    log(f"  Sidebar 'Meu historico': {sidebar_item}")
    log(f"  Feature OK: {feature_ok}")

    if not feature_ok:
        log("BLOQUEIO: feature 'Meu historico' nao habilitada nesta org.")
        log("  Verifique a flag na org registrosf2.")
        tw.snap(page, EVID, "fechamento_gate_feature_off")
        raise SystemExit("GATE FALHOU: feature desabilitada.")

    # (b) Visao Aluno (nao admin)?
    visao_aluno = "in_use_mode_layout=true" in page.url
    admin_badge = page.get_by_text(re.compile(r"Aprendizagem.{0,5}Registros", re.I)).count() > 0
    visao_ok = visao_aluno and not admin_badge
    log(f"  Visao Aluno OK: {visao_ok} (in_use_mode_layout={visao_aluno}, admin_badge={admin_badge})")

    # (c) Contagem de registros
    rows = page.locator("table tbody tr").count()
    empty_msg = page.get_by_text(
        "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
    ).count() > 0
    log(f"  Registros (linhas na tabela): {rows}")
    log(f"  Empty state msg visivel: {empty_msg}")

    tw.snap(page, EVID, "fechamento_gate_overview")

    return {
        "org_id": org_id,
        "feature_ok": feature_ok,
        "visao_aluno_ok": visao_ok,
        "rows": rows,
        "empty_msg": empty_msg,
    }


# ─── TC3: Empty state ──────────────────────────────────────────────────────────

def run_tc3(page, gate_info):
    log("\n=== TC3: Empty state sem registros ===")
    evids = []
    org_id = gate_info["org_id"]

    # Se ja tem registros, TC3 fica BLOQUEADO
    if gate_info["rows"] > 0:
        tw.snap(page, EVID, "fechamento_tc3_nao_zero")
        evids.append("fechamento_tc3_nao_zero.png")
        bloqueado(3, evids,
                  f"Aluno ja tem {gate_info['rows']} registros — "
                  "nao e possivel validar empty state com este usuario. "
                  "Necessario usuario com ZERO registros.")
        return

    # Aluno tem 0 registros — valida diretamente
    ir_meu_historico(page, org_id)
    tw.snap(page, EVID, "fechamento_tc3_empty")
    evids.append("fechamento_tc3_empty.png")

    # Passo 1: mensagem exata
    msg_exata = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
    has_empty = page.get_by_text(msg_exata).count() > 0
    log(f"  Mensagem empty state presente: {has_empty}")

    # Passo 2: 4 KPI cards com 0
    # Busca os 4 cards pelos labels literais da AT
    kpi_labels = ["Emitidos", "Expirados", "Pendentes", "Recusados"]
    kpi_found = {}
    kpi_values = {}

    for label in kpi_labels:
        # Encontra o card pelo label e pega o numero dentro dele
        try:
            card = page.locator(
                f"[class*='stat'], [class*='kpi'], [class*='card'], [class*='Stat']"
            ).filter(has_text=label).first
            if card.count() > 0:
                kpi_found[label] = True
                # Extrai o numero do card
                card_text = card.inner_text()
                nums = re.findall(r'\d+', card_text)
                kpi_values[label] = int(nums[0]) if nums else None
            else:
                kpi_found[label] = False
                kpi_values[label] = None
        except Exception as e:
            kpi_found[label] = False
            kpi_values[label] = None
            log(f"  KPI '{label}' erro: {e}")

    log(f"  KPI encontrados: {kpi_found}")
    log(f"  KPI valores: {kpi_values}")

    # Verifica os 4 cards sao visiveis
    all_4_found = all(kpi_found.get(l, False) for l in kpi_labels)
    all_zero = all(kpi_values.get(l) == 0 for l in kpi_labels if kpi_values.get(l) is not None)
    any_nonzero = any(kpi_values.get(l, 0) not in (0, None) for l in kpi_labels)

    # Screenshot adicional com zoom nos KPIs
    tw.snap(page, EVID, "fechamento_tc3_kpis")
    evids.append("fechamento_tc3_kpis.png")

    rows = page.locator("table tbody tr").count()
    log(f"  Linhas na tabela: {rows}")
    log(f"  4 KPIs presentes: {all_4_found}, todos zero: {all_zero}, algum nao-zero: {any_nonzero}")

    # Veredito
    if has_empty and rows == 0 and all_4_found and not any_nonzero:
        passou(3, evids,
               f"mensagem exata presente; 0 linhas; 4 KPIs visiveis com 0 "
               f"({kpi_values})")
    elif not has_empty and rows == 0:
        falhou(3, evids,
               f"tabela vazia mas mensagem '{msg_exata}' NAO encontrada")
    elif not all_4_found:
        # Mensagem pode estar certa mas KPIs ausentes/incompletos
        missing = [l for l in kpi_labels if not kpi_found.get(l, False)]
        if has_empty:
            falhou(3, evids,
                   f"mensagem empty state OK, mas KPI cards ausentes: {missing} "
                   f"(encontrados: {kpi_found})")
        else:
            falhou(3, evids,
                   f"mensagem empty state NAO encontrada E KPI cards ausentes: {missing}")
    elif any_nonzero:
        falhou(3, evids,
               f"KPI cards presentes mas algum nao e 0: {kpi_values}")
    else:
        falhou(3, evids,
               f"has_empty={has_empty}, rows={rows}, kpi_found={kpi_found}, kpi_vals={kpi_values}")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("fechamento_qa11_faseA.py — Gate + TC3")
    log(f"Org: {BASE_URL}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            gate_info = run_gate(page)
            run_tc3(page, gate_info)
        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("RESULTADOS FASE A:")
    for tc, r in RESULTADOS.items():
        log(f"  TC{tc}: {r['veredito']} — {r['obs']}")

    # Salva resultado parcial em arquivo para Fase B ler
    saida = EVID / "faseA_resultado.txt"
    with open(saida, "w", encoding="utf-8") as f:
        for k, v in RESULTADOS.items():
            f.write(f"TC{k}|{v['veredito']}|{v['obs']}\n")
    log(f"\nResultado salvo em: {saida}")
    log("=" * 60)


if __name__ == "__main__":
    main()
