"""run_qa11_debug2.py — Debug: verifica estado admin dos registros e cria usuário."""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "registros-f2-qa11"
EVID = tw.ROOT / "evidencias" / SLUG
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ALUNO_EMAIL = os.environ.get("ALUNO_EMAIL", "")
ORG_ID = os.environ.get("ORG_ID", "36675")
RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"


def log(msg):
    print(msg)


with tw.sync_playwright() as p:
    ba, ca, pa = tw.nova_pagina(p)

    # Admin
    c = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}
    tw.login(pa, c, admin=True)
    log(f"Admin: {pa.url[:60]}")

    # 1. Verifica registros do Aluno no admin
    # Tenta rota learning_records
    pa.goto(f"{BASE_URL}/o/{ORG_ID}/learning_records", wait_until="domcontentloaded", timeout=25000)
    try:
        pa.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    pa.wait_for_timeout(3000)
    tw.dispensar_nps(pa)
    tw.snap(pa, EVID, "debug_admin_lr_url")
    log(f"URL: {pa.url}")

    rows = pa.locator("table tbody tr").count()
    log(f"Linhas na lista admin: {rows}")

    # Verifica KPIs
    for kpi in ["Emitidos", "Expirados", "Pendentes", "Recusados"]:
        el = pa.get_by_text(kpi, exact=True).first
        if el.count() > 0:
            try:
                parent = pa.evaluate(
                    "el => el.parentElement?.innerText?.trim()?.substring(0, 40) || ''",
                    el.element_handle()
                )
                log(f"  KPI {kpi}: '{parent}'")
            except Exception:
                pass

    # Tenta filtrar por "Pendentes"
    kpi_pend = pa.get_by_text("Pendentes", exact=True).first
    if kpi_pend.count() > 0:
        kpi_pend.click(timeout=5000)
        pa.wait_for_timeout(2000)
        rows_pend = pa.locator("table tbody tr").count()
        log(f"Pendentes: {rows_pend}")
        tw.snap(pa, EVID, "debug_admin_pendentes")

        # Lista primeiro pendente
        if rows_pend > 0:
            primeira = pa.locator("table tbody tr").first
            cells = [primeira.locator("td").nth(i).inner_text().strip()[:30]
                     for i in range(min(6, primeira.locator("td").count()))]
            log(f"  Primeiro pendente: {cells}")

    # Filtra por Aluno especificamente
    # Busca pelo email do aluno
    busca = pa.get_by_placeholder(re.compile("Pesquise", re.I)).first
    if busca.count() > 0:
        busca.click()
        busca.fill(ALUNO_EMAIL.split("@")[0])  # parte antes do @
        pa.wait_for_timeout(3000)
        rows_aluno = pa.locator("table tbody tr").count()
        log(f"Busca por aluno '{ALUNO_EMAIL.split('@')[0]}': {rows_aluno} registros")
        tw.snap(pa, EVID, "debug_admin_busca_aluno")
        busca.click(click_count=3)
        pa.keyboard.press("Delete")
        pa.wait_for_timeout(1500)

    # 2. Usuarios admin — dump da página
    pa.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=25000)
    try:
        pa.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    pa.wait_for_timeout(2000)
    tw.dispensar_nps(pa)
    tw.snap(pa, EVID, "debug_usuarios_page")
    log(f"\nURL Usuários: {pa.url}")

    # Botões na página de usuários
    btns = pa.evaluate("""() => {
        return Array.from(document.querySelectorAll('button, a[href*="new"], a[href*="create"]')).filter(b => {
            const r = b.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        }).slice(0, 20).map(b => ({
            tag: b.tagName,
            text: b.innerText?.trim()?.substring(0, 50) || '',
            href: b.getAttribute('href') || '',
            x: Math.round(b.getBoundingClientRect().x),
            y: Math.round(b.getBoundingClientRect().y)
        }));
    }""")
    log(f"Botões/links na página Usuários:")
    for b in btns:
        log(f"  [{b['y']:4d},{b['x']:4d}] {b['tag']}: '{b['text']}' href={b['href']}")

    # Tenta link /users/new
    new_user_url = f"{BASE_URL}/o/{ORG_ID}/users/new"
    pa.goto(new_user_url, wait_until="domcontentloaded", timeout=25000)
    try:
        pa.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    pa.wait_for_timeout(2000)
    tw.dispensar_nps(pa)
    log(f"\nURL /users/new: {pa.url}")
    tw.snap(pa, EVID, "debug_users_new")

    campos = pa.evaluate("""() => {
        return Array.from(document.querySelectorAll('input, select')).filter(i => {
            const r = i.getBoundingClientRect();
            return r.width > 0;
        }).map(i => ({
            type: i.type,
            name: i.name,
            id: i.id,
            placeholder: i.placeholder?.substring(0, 40),
            label: (() => {
                const lbl = document.querySelector(`label[for="${i.id}"]`);
                return lbl ? lbl.innerText?.trim() : '';
            })()
        }));
    }""")
    log(f"Campos /users/new: {campos[:15]}")

    btns_new = pa.evaluate("""() => {
        return Array.from(document.querySelectorAll('button')).filter(b => {
            const r = b.getBoundingClientRect();
            return r.width > 0;
        }).map(b => ({
            text: b.innerText?.trim()?.substring(0, 40),
            type: b.type,
            disabled: b.disabled
        }));
    }""")
    log(f"Botões /users/new: {[b for b in btns_new if b['text']][:10]}")

    ca.close()
    ba.close()

    # 3. Verifica estado do Aluno: lista atual
    ba2, ca2, pa2 = tw.nova_pagina(p)
    pa2.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    pa2.wait_for_selector("#user_email", timeout=10000)
    pa2.fill("#user_email", ALUNO_EMAIL)
    pa2.fill("#user_password", ADMIN_PASSWORD)
    pa2.click("#user_submit")
    try:
        pa2.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    pa2.wait_for_timeout(2000)
    tw.dispensar_nps(pa2)

    pa2.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=25000)
    try:
        pa2.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    pa2.wait_for_timeout(2500)
    tw.dispensar_nps(pa2)
    tw.snap(pa2, EVID, "debug_aluno_lista_atual")

    rows_aluno = pa2.locator("table tbody tr").count()
    log(f"\nRegistros do Aluno: {rows_aluno}")

    # Status dos registros
    for status in ["Aprovado", "Pendente", "Recusado", "Expirado"]:
        n = pa2.locator("td").filter(has_text=status).count()
        log(f"  {status}: {n}")

    # Primeiras 5 linhas
    for i in range(min(5, rows_aluno)):
        linha = pa2.locator("table tbody tr").nth(i)
        cells = [linha.locator("td").nth(j).inner_text().strip()[:25]
                 for j in range(min(7, linha.locator("td").count()))]
        log(f"  Linha {i+1}: {cells}")

    ca2.close()
    ba2.close()

log("Debug concluído")
