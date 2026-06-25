# -*- coding: utf-8 -*-
"""
QA 1.16 v2 — Escopo do Líder, Inativados e Origem Compartilhado
Card Artia: 19903 — Projeto Registros F2
Org: 37079 (registrosf2.stage.twygoead.com)

TCs cobertos:
  TC1  (RN 93) — Admin vê tudo; Líder puro vê só liderados
  TC2  (RN 94) — Líder tenta aprovar registro fora da equipe → 403
  TC3  (RN 95) — Aprovação → remove liderado → admin preserva, líder não vê
  TC4  (RN 96) — Inativação: KPIs decrementam, registros somem da lista
  TC5  (RN 96.5)— KPI sum = total paginado (já passou; re-check)
  TC6-TC10      — SharedEvent / multi-org: tentar, documentar bloqueio

Pré-condições criadas por este script:
  - qaliderpuro@teste.com (SOMENTE Gestor de Turma, senha 123456)
  - liderado1@teste.com já existe (senha desconhecida, usamos como subordinado)
  - organograma: qaliderpuro -> liderado1
  - 1 registro externo para liderado1 (via UI ou POST API)
  - 1 registro externo para usuário fora do time (devtestes@teste.com)
  - 1 usuário descartável qainativo_<rand>@twygotest.com + 2 registros

Rodar (headless por padrão):
    .\.venv\Scripts\python.exe scripts\run_t19903_registros_f2_qa116_v2.py
Rodar com janela:
    TW_HEADED=1 .\.venv\Scripts\python.exe scripts\run_t19903_registros_f2_qa116_v2.py
"""

import json
import random
import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

# ─── configuração ────────────────────────────────────────────────────────────
BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"

ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"

LIDER_PURO_EMAIL    = "qaliderpuro@teste.com"
LIDER_PURO_PASSWORD = "123456"

LIDERADO_EMAIL = "liderado1@teste.com"
FORA_EMAIL     = "devtestes@teste.com"   # usuário fora da equipe

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)

resultados: dict = {}
entidades_criadas: list = []

log = lambda *a: print(*a, flush=True)


def snap(page, nome, full=False):
    fp = PASTA / f"{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    log(f"  [snap] {fp.name}")
    return fp


def tc_resultado(tc, veredito, resumo):
    resultados[tc] = {"veredito": veredito, "resumo": resumo}
    icone = "PASSOU" if veredito == "PASSOU" else "FALHOU"
    log(f"\n  [{icone}] {tc}: {resumo}\n")


def dispensar_overlays(page):
    tw.dispensar_nps(page)
    try:
        page.evaluate("""() => {
            document.querySelectorAll(
                '#hubspot-messages-iframe-container,[id*=sophia]'
            ).forEach(e => e.style.display='none');
        }""")
    except Exception:
        pass


def aguardar_tabela(page, timeout=25000):
    try:
        page.wait_for_function(
            "() => document.querySelectorAll('tbody tr').length > 0",
            timeout=timeout,
        )
        page.wait_for_timeout(800)
        return True
    except Exception:
        return False


def ir_records(page, as_admin=True):
    page.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    dispensar_overlays(page)


def ler_kpis(page) -> dict:
    """Lê os 4 contadores KPI da tela de Registros."""
    kpis = {}
    try:
        body = page.locator("body").inner_text()
        for label, key in [
            ("Emitidos", "emitidos"),
            ("Pendentes", "pendentes"),
            ("Recusados", "recusados"),
            ("Expirados", "expirados"),
        ]:
            m = re.search(rf"(\d[\d.]*)\s*\n?\s*{label}", body)
            if m:
                kpis[key] = int(m.group(1).replace(".", ""))
    except Exception as e:
        log(f"  [kpi] erro: {e}")
    return kpis


def api_get(page, path) -> tuple[int, dict]:
    resp = page.request.get(
        f"{BASE_URL}{path}",
        headers={"Accept": "application/json"},
    )
    try:
        data = resp.json()
    except Exception:
        data = {}
    return resp.status, data


def api_total_records(page) -> int:
    st, data = api_get(page, f"/api/v1/o/{ORG_ID}/records?order_type=desc&per_page=1&page=1")
    if st == 200:
        return data.get("data", {}).get("meta", {}).get("total_count", 0)
    return -1


def api_records_page(page, page_num=1, per_page=50) -> list:
    st, data = api_get(page, f"/api/v1/o/{ORG_ID}/records?order_type=desc&per_page={per_page}&page={page_num}")
    if st == 200:
        return data.get("data", {}).get("records", [])
    return []


def api_criar_registro_externo(page, pessoa_email: str, titulo: str) -> dict | None:
    """
    Cria registro externo via POST da API.
    Retorna dict com id ou None se falhou.
    ponytail: payload mínimo confirmado via inspeção de rede da QA 1.9
    """
    payload = {
        "record": {
            "origin": "external",
            "situation": "pending",
            "content": titulo,
            "workload_hours": 1,
            "workload_minutes": 0,
        },
        "person_email": pessoa_email,
    }
    resp = page.request.post(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        data=json.dumps(payload),
    )
    log(f"  [POST /records] status={resp.status} email={pessoa_email}")
    if resp.status in (200, 201):
        try:
            rec = resp.json().get("data", {}).get("record", {})
            return rec
        except Exception:
            pass
    # Tentar ler body de erro
    try:
        log(f"  [POST erro body] {resp.text()[:300]}")
    except Exception:
        pass
    return None


def api_inativar_usuario(page, user_id: int) -> bool:
    """PATCH /api/v1/o/{org}/professionals/{id} com active=false."""
    resp = page.request.patch(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/professionals/{user_id}",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        data=json.dumps({"professional": {"active": False}}),
    )
    log(f"  [PATCH inativar] user_id={user_id} status={resp.status}")
    return resp.status in (200, 204)


def buscar_professional_id(page, email: str) -> int | None:
    """Busca o ID do profissional pelo e-mail via API de usuários."""
    st, data = api_get(page, f"/api/v1/o/{ORG_ID}/professionals?search={email}&per_page=10")
    if st == 200:
        profs = data.get("data", {}).get("professionals", [])
        for p in profs:
            if p.get("email") == email:
                return p.get("id")
    # Fallback: página admin de usuários
    try:
        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/users?search={email}",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        page.wait_for_timeout(2000)
        href = page.locator(f"a[href*='/users/']").first.get_attribute("href")
        if href:
            m = re.search(r"/users/(\d+)", href)
            if m:
                return int(m.group(1))
    except Exception:
        pass
    return None


# ─── SETUP: criar líder puro ──────────────────────────────────────────────────

def criar_lider_puro(page_admin) -> bool:
    """Cria qaliderpuro@teste.com com SOMENTE perfil Gestor de Turma."""
    log("\n--- SETUP: criar líder puro ---")

    # Verificar se já existe
    page_admin.goto(
        f"{BASE_URL}/o/{ORG_ID}/users?search={LIDER_PURO_EMAIL}",
        wait_until="domcontentloaded",
        timeout=20000,
    )
    page_admin.wait_for_timeout(2000)
    if LIDER_PURO_EMAIL in page_admin.locator("body").inner_text():
        log(f"  [lider_puro] já existe — OK")
        snap(page_admin, "setup_lider_puro_existente")
        return True

    # Criar novo usuário
    page_admin.goto(
        f"{BASE_URL}/o/{ORG_ID}/users/new",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    dispensar_overlays(page_admin)
    page_admin.wait_for_timeout(2500)

    campos = {
        "professional[email]":      LIDER_PURO_EMAIL,
        "professional[first_name]": "QALider",
        "professional[last_name]":  "Puro116",
        "professional[phone1]":     "(47) 99111-1116",
    }
    for nm, val in campos.items():
        inp = page_admin.locator(f"input[name='{nm}']")
        if inp.count():
            try:
                inp.first.fill(val, timeout=3000)
            except Exception:
                pass

    # Marcar SOMENTE "Gestor de Turma" — desmarca Aluno se vier default
    def check_label(texto):
        box = page_admin.evaluate(
            r"""(t)=>{
              const labs=[...document.querySelectorAll('label,span,p,div')]
                .filter(e=>(e.innerText||'').replace(/\s+/g,' ').trim()===t
                         && e.getBoundingClientRect().left>200);
              if(!labs.length) return null;
              const l=labs[0]; l.scrollIntoView({block:'center'});
              const r=l.getBoundingClientRect();
              return {x:r.left-8, y:r.top+r.height/2};
            }""",
            texto,
        )
        if not box:
            return False
        page_admin.mouse.click(box["x"], box["y"])
        page_admin.wait_for_timeout(300)
        return True

    # Marcar Gestor de Turma (o único que queremos)
    ok_gestor = check_label("Gestor de Turma")
    log(f"  [lider_puro] Gestor de Turma marcado: {ok_gestor}")

    snap(page_admin, "setup_lider_puro_form", full=True)

    page_admin.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=5000)
    page_admin.wait_for_timeout(3500)

    snap(page_admin, "setup_lider_puro_salvo")
    body = page_admin.locator("body").inner_text()
    criou = "users/new" not in page_admin.url or LIDER_PURO_EMAIL in body
    log(f"  [lider_puro] criado={criou} url={page_admin.url[-50:]}")

    if criou:
        entidades_criadas.append({"tipo": "usuario", "email": LIDER_PURO_EMAIL, "acao": "criado"})

    # Definir senha via admin (editar perfil)
    page_admin.goto(
        f"{BASE_URL}/o/{ORG_ID}/users?search={LIDER_PURO_EMAIL}",
        wait_until="domcontentloaded",
        timeout=20000,
    )
    page_admin.wait_for_timeout(2000)

    # Clicar no nome do usuário para ir à edição
    try:
        link = page_admin.locator(f"a:has-text('QALider')").first
        if link.count():
            link.click()
            page_admin.wait_for_timeout(2000)
            # Preencher senha
            pwd_inp = page_admin.locator("input[name='professional[password]']")
            if pwd_inp.count():
                pwd_inp.first.fill(LIDER_PURO_PASSWORD)
                pwd_conf = page_admin.locator("input[name='professional[password_confirmation]']")
                if pwd_conf.count():
                    pwd_conf.first.fill(LIDER_PURO_PASSWORD)
                page_admin.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=5000)
                page_admin.wait_for_timeout(2000)
                log(f"  [lider_puro] senha definida")
    except Exception as e:
        log(f"  [lider_puro] aviso: definição de senha: {e}")

    return criou


# ─── SETUP: montar organograma ────────────────────────────────────────────────

def montar_organograma_api(page_admin) -> bool:
    """
    Tenta criar a relação líder->liderado via API de organograma.
    Org 37079 usa /api/v1/o/{org}/organization_chart_nodes.
    """
    log("\n--- SETUP: montar organograma ---")

    # Passo 1: buscar IDs
    lider_id = buscar_professional_id(page_admin, LIDER_PURO_EMAIL)
    liderado_id = buscar_professional_id(page_admin, LIDERADO_EMAIL)
    log(f"  [organograma] lider_id={lider_id} liderado_id={liderado_id}")

    if not lider_id or not liderado_id:
        log("  [organograma] IDs não encontrados — tentando via UI")
        return montar_organograma_ui(page_admin)

    # Passo 2: verificar URL correta do organograma
    candidatos = [
        f"/o/{ORG_ID}/organization_charts",
        f"/o/{ORG_ID}/users/{lider_id}/organization_chart",
        f"/o/{ORG_ID}/users/{lider_id}/edit",
    ]
    url_org = None
    for c in candidatos:
        page_admin.goto(BASE_URL + c, wait_until="domcontentloaded", timeout=15000)
        page_admin.wait_for_timeout(1500)
        if page_admin.url != f"{BASE_URL}/" and "404" not in page_admin.locator("body").inner_text()[:50]:
            url_org = c
            log(f"  [organograma] URL válida: {c}")
            snap(page_admin, "setup_organograma_url")
            break

    # Passo 3: tentar API de hierarquia
    # Tentar vincular liderado ao líder via professionals update
    payloads = [
        # Opção A: campo manager_id
        {"professional": {"manager_id": lider_id}},
        # Opção B: campo leader_id
        {"professional": {"leader_id": lider_id}},
    ]

    for payload in payloads:
        resp = page_admin.request.patch(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/professionals/{liderado_id}",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            data=json.dumps(payload),
        )
        log(f"  [organograma PATCH] payload={list(payload['professional'].keys())} status={resp.status}")
        if resp.status in (200, 201, 204):
            log(f"  [organograma] vinculo criado via {list(payload['professional'].keys())}")
            entidades_criadas.append({
                "tipo": "organograma",
                "lider": LIDER_PURO_EMAIL,
                "lider_id": lider_id,
                "liderado": LIDERADO_EMAIL,
                "liderado_id": liderado_id,
            })
            return True

    # Passo 4: tentar via edição do liderado na UI
    return montar_organograma_ui(page_admin, lider_id=lider_id, liderado_id=liderado_id)


def montar_organograma_ui(page_admin, lider_id=None, liderado_id=None) -> bool:
    """Fallback: montar organograma via UI de edição do liderado."""
    log("  [organograma] tentando via UI...")
    if not liderado_id:
        liderado_id = buscar_professional_id(page_admin, LIDERADO_EMAIL)
    if not lider_id:
        lider_id = buscar_professional_id(page_admin, LIDER_PURO_EMAIL)

    if not liderado_id:
        log("  [organograma] liderado_id não encontrado — BLOQUEADO")
        return False

    page_admin.goto(
        f"{BASE_URL}/o/{ORG_ID}/users/{liderado_id}/edit",
        wait_until="domcontentloaded",
        timeout=20000,
    )
    dispensar_overlays(page_admin)
    page_admin.wait_for_timeout(2500)
    snap(page_admin, "setup_organograma_edit_liderado", full=True)

    body = page_admin.locator("body").inner_text()
    log(f"  [organograma UI] url={page_admin.url} body[:100]={body[:100]}")

    # Procurar campo "Líder" / "Gestor" / "Responsável"
    for campo_nome in ["Líder direto", "Líder", "Gestor", "Responsável", "Manager"]:
        inp = page_admin.locator(f"input[placeholder*='{campo_nome}']")
        if inp.count():
            inp.first.fill("QALider")
            page_admin.wait_for_timeout(1000)
            opcao = page_admin.locator("[role='option']").filter(has_text="QALider")
            if opcao.count():
                opcao.first.click()
                page_admin.wait_for_timeout(500)
                log(f"  [organograma UI] campo '{campo_nome}' preenchido")
                page_admin.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=5000)
                page_admin.wait_for_timeout(2000)
                snap(page_admin, "setup_organograma_salvo")
                return True

    log("  [organograma UI] nenhum campo de líder encontrado — BLOQUEADO")
    snap(page_admin, "setup_organograma_bloqueado", full=True)
    return False


# ─── SETUP: criar registros ───────────────────────────────────────────────────

def criar_registros_setup(page_admin) -> dict:
    """Cria registros para liderado1 e para devtestes (fora da equipe)."""
    log("\n--- SETUP: criar registros ---")

    rec_liderado = api_criar_registro_externo(
        page_admin,
        LIDERADO_EMAIL,
        "QA116-Liderado-Externo",
    )
    if rec_liderado:
        log(f"  [setup] registro liderado1 id={rec_liderado.get('id')}")
        entidades_criadas.append({
            "tipo": "registro",
            "id": rec_liderado.get("id"),
            "pessoa": LIDERADO_EMAIL,
            "titulo": "QA116-Liderado-Externo",
        })

    rec_fora = api_criar_registro_externo(
        page_admin,
        FORA_EMAIL,
        "QA116-ForaEquipe-Externo",
    )
    if rec_fora:
        log(f"  [setup] registro devtestes id={rec_fora.get('id')}")
        entidades_criadas.append({
            "tipo": "registro",
            "id": rec_fora.get("id"),
            "pessoa": FORA_EMAIL,
            "titulo": "QA116-ForaEquipe-Externo",
        })

    return {
        "rec_liderado": rec_liderado,
        "rec_fora": rec_fora,
    }


# ─── TC1: Escopo do líder ─────────────────────────────────────────────────────

def executar_tc1(page_admin, page_lider, rec_liderado_id, rec_fora_id):
    log("\n=== TC1 — Escopo do Líder ===")

    # Admin: KPIs e total
    ir_records(page_admin)
    aguardar_tabela(page_admin)
    kpis_admin = ler_kpis(page_admin)
    total_admin = api_total_records(page_admin)
    admin_linhas = page_admin.locator("tbody tr").count()
    snap(page_admin, "tc1_01_admin_lista", full=True)
    log(f"  [admin] kpis={kpis_admin} total_api={total_admin} linhas_pagina={admin_linhas}")

    estrutura_admin = {
        "tem_adicionar": page_admin.locator("button:has-text('Adicionar')").count() > 0,
        "tem_kpis": bool(kpis_admin),
        "url": page_admin.url,
    }

    # Líder puro: navegar para /records
    page_lider.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try:
        page_lider.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page_lider.wait_for_timeout(3000)
    dispensar_overlays(page_lider)
    url_lider = page_lider.url
    log(f"  [lider] URL após navigate: {url_lider}")

    if "/records" not in url_lider:
        snap(page_lider, "tc1_02_lider_redirecionado")
        tc_resultado(
            "TC1",
            "FALHOU",
            f"Líder puro redirecionado para {url_lider} — não tem acesso à tela de Registros",
        )
        return

    aguardar_tabela(page_lider, timeout=15000)
    kpis_lider = ler_kpis(page_lider)
    total_lider_api = api_total_records(page_lider)
    lider_linhas = page_lider.locator("tbody tr").count()
    snap(page_lider, "tc1_02_lider_lista", full=True)
    log(f"  [lider] kpis={kpis_lider} total_api={total_lider_api} linhas={lider_linhas}")

    # Verificar Adicionar → Pessoa dropdown restrito
    btn_add = page_lider.locator("button:has-text('Adicionar')")
    dropdown_restrito = False
    if btn_add.count():
        btn_add.first.click()
        page_lider.wait_for_timeout(1500)
        snap(page_lider, "tc1_03_lider_adicionar_dropdown")
        # No modal/dropdown "Pessoa", apenas liderados devem aparecer
        body_add = page_lider.locator("body").inner_text()
        dropdown_restrito = (
            FORA_EMAIL not in body_add
            and "devtestes" not in body_add.lower()
        )
        log(f"  [lider] dropdown_restrito={dropdown_restrito}")
        page_lider.keyboard.press("Escape")
        page_lider.wait_for_timeout(500)

    # Verificar: líder vê MENOS registros que admin (restrição de escopo)
    soma_kpis_admin = sum(kpis_admin.values())
    soma_kpis_lider = sum(kpis_lider.values())

    # TC1 passa se:
    # a) O líder tem acesso à tela /records, E
    # b) Os KPIs do líder < KPIs do admin (escopo restrito), OU
    #    ambos os registros criados: se o de liderado aparece e o de fora NÃO aparece

    escopo_restrito = soma_kpis_lider < soma_kpis_admin
    lider_ve_rec_liderado = False
    lider_ve_rec_fora = False

    if rec_liderado_id:
        recs_lider = api_records_page(page_lider)
        lider_ve_rec_liderado = any(r.get("id") == rec_liderado_id for r in recs_lider)
        lider_ve_rec_fora = any(r.get("id") == rec_fora_id for r in recs_lider)
        log(f"  [lider via API] vê liderado={lider_ve_rec_liderado} vê fora={lider_ve_rec_fora}")

    snap(page_lider, "tc1_04_lider_kpis", full=True)

    # Determinar veredito
    if not escopo_restrito and rec_liderado_id is None:
        # Sem registros de teste criados (POST falhou), mas líder acessou /records
        # Verificar se organograma foi montado: se sim e KPIs iguais → FALHOU
        if total_lider_api == total_admin and total_admin > 0:
            tc_resultado(
                "TC1",
                "FALHOU",
                f"Líder puro vê mesmo total que admin ({total_lider_api}={total_admin}) — sem restrição de escopo",
            )
        else:
            tc_resultado(
                "TC1",
                "FALHOU",
                f"Sem registros de fixture criados para validar escopo; líder api_total={total_lider_api} admin={total_admin}",
            )
    elif rec_liderado_id and lider_ve_rec_liderado and not lider_ve_rec_fora:
        tc_resultado(
            "TC1",
            "PASSOU",
            f"Líder vê registro do liderado (id={rec_liderado_id}) mas NÃO vê registro fora da equipe (id={rec_fora_id}) — escopo correto",
        )
    elif rec_liderado_id and lider_ve_rec_fora:
        tc_resultado(
            "TC1",
            "FALHOU",
            f"Líder vê registro de usuário fora da equipe (id={rec_fora_id}) — escopo NÃO restrito",
        )
    elif escopo_restrito:
        tc_resultado(
            "TC1",
            "PASSOU",
            f"KPIs líder ({soma_kpis_lider}) < admin ({soma_kpis_admin}) — escopo restrito confirmado",
        )
    else:
        tc_resultado(
            "TC1",
            "FALHOU",
            f"Líder KPIs={soma_kpis_lider} == admin KPIs={soma_kpis_admin} e registros de fixture não discriminaram escopo",
        )


# ─── TC2: API 403 fora da equipe ─────────────────────────────────────────────

def executar_tc2(page_lider, rec_fora_id):
    log("\n=== TC2 — API 403 ao aprovar fora da equipe ===")

    if not rec_fora_id:
        tc_resultado("TC2", "FALHOU", "Registro de usuário fora da equipe não foi criado — sem fixture")
        return

    # Líder tenta aprovar registro de usuário fora da equipe
    resp = page_lider.request.patch(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records/{rec_fora_id}",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        data=json.dumps({"record": {"situation": "approved"}}),
    )
    st = resp.status
    log(f"  [TC2] PATCH records/{rec_fora_id} as lider → status={st}")

    try:
        body_resp = resp.json()
        log(f"  [TC2] body={str(body_resp)[:200]}")
    except Exception:
        body_resp = {}

    if st == 403:
        tc_resultado("TC2", "PASSOU", f"Líder recebeu 403 ao tentar aprovar registro fora da equipe (id={rec_fora_id})")
    elif st in (401, 404):
        tc_resultado(
            "TC2",
            "PASSOU",
            f"Líder recebeu {st} ao aprovar registro fora da equipe — acesso negado conforme esperado",
        )
    elif st == 200:
        tc_resultado(
            "TC2",
            "FALHOU",
            f"Líder conseguiu aprovar (200) registro fora da equipe (id={rec_fora_id}) — sem restrição de escopo",
        )
    else:
        tc_resultado("TC2", "FALHOU", f"Status inesperado {st} ao tentar aprovação fora do escopo")


# ─── TC3: Remove liderado → admin preserva, líder não vê ─────────────────────

def executar_tc3(page_admin, page_lider, rec_liderado_id, liderado_id):
    log("\n=== TC3 — Remover do organograma ===")

    if not rec_liderado_id or not liderado_id:
        tc_resultado("TC3", "FALHOU", "Fixtures de liderado não disponíveis para TC3")
        return

    # Passo 1: Aprovar registro do liderado como líder
    resp_aprovar = page_lider.request.patch(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records/{rec_liderado_id}",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        data=json.dumps({"record": {"situation": "approved"}}),
    )
    log(f"  [TC3] líder aprova registro liderado: status={resp_aprovar.status}")

    # Verificar que admin ainda vê o registro
    st_admin, data_admin = api_get(page_admin, f"/api/v1/o/{ORG_ID}/records/{rec_liderado_id}")
    admin_ve_antes = st_admin == 200
    sit_antes = data_admin.get("data", {}).get("record", {}).get("situation", "?")
    log(f"  [TC3] admin vê registro antes de remover: {admin_ve_antes} situation={sit_antes}")

    # Passo 2: Remover liderado do organograma via API
    resp_remove = page_admin.request.patch(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/professionals/{liderado_id}",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        data=json.dumps({"professional": {"manager_id": None}}),
    )
    log(f"  [TC3] remover liderado do organograma: status={resp_remove.status}")

    # Alternativa: setar leader_id=null
    if resp_remove.status not in (200, 204):
        resp_remove2 = page_admin.request.patch(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/professionals/{liderado_id}",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            data=json.dumps({"professional": {"leader_id": None}}),
        )
        log(f"  [TC3] remover via leader_id=null: status={resp_remove2.status}")

    page_admin.wait_for_timeout(1500)

    # Passo 3: Admin ainda vê o registro?
    st_admin2, data_admin2 = api_get(page_admin, f"/api/v1/o/{ORG_ID}/records/{rec_liderado_id}")
    admin_ve_depois = st_admin2 == 200
    sit_depois = data_admin2.get("data", {}).get("record", {}).get("situation", "?")
    log(f"  [TC3] admin vê registro depois de remover: {admin_ve_depois} situation={sit_depois}")

    snap(page_admin, "tc3_01_admin_apos_remover")

    # Passo 4: Líder ainda vê o registro?
    recs_lider_depois = api_records_page(page_lider)
    lider_ve_depois = any(r.get("id") == rec_liderado_id for r in recs_lider_depois)
    log(f"  [TC3] líder vê registro depois de remover: {lider_ve_depois}")

    ir_records(page_lider, as_admin=False)
    aguardar_tabela(page_lider, timeout=10000)
    snap(page_lider, "tc3_02_lider_apos_remover", full=True)

    if admin_ve_depois and not lider_ve_depois:
        tc_resultado(
            "TC3",
            "PASSOU",
            f"Registro aprovado (sit={sit_depois}) preservado para admin; removido da visão do líder após desvinculação do organograma",
        )
    elif not admin_ve_depois:
        tc_resultado(
            "TC3",
            "FALHOU",
            f"Admin perdeu acesso ao registro após remoção do organograma (sit={sit_depois}) — dados não preservados",
        )
    elif lider_ve_depois:
        tc_resultado(
            "TC3",
            "FALHOU",
            f"Líder ainda vê o registro após remoção do liderado do organograma — escopo não atualizado",
        )
    else:
        tc_resultado(
            "TC3",
            "FALHOU",
            f"admin_ve={admin_ve_depois} lider_ve={lider_ve_depois} sit={sit_depois}",
        )


# ─── TC4: Inativação ─────────────────────────────────────────────────────────

def executar_tc4(page_admin):
    log("\n=== TC4 — Inativação de usuário ===")

    # Passo 1: Capturar KPIs antes
    ir_records(page_admin)
    aguardar_tabela(page_admin)
    kpis_antes = ler_kpis(page_admin)
    total_antes = api_total_records(page_admin)
    snap(page_admin, "tc4_01_kpis_antes", full=True)
    log(f"  [TC4] KPIs antes: {kpis_antes} total={total_antes}")

    # Passo 2: Criar usuário descartável
    rand = random.randint(10000, 99999)
    inativo_email = f"qainativo_{rand}@twygotest.com"
    log(f"  [TC4] criando usuário descartável: {inativo_email}")

    page_admin.goto(
        f"{BASE_URL}/o/{ORG_ID}/users/new",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    dispensar_overlays(page_admin)
    page_admin.wait_for_timeout(2500)

    campos_inativo = {
        "professional[email]":      inativo_email,
        "professional[first_name]": "QAInativo",
        "professional[last_name]":  f"TC4-{rand}",
        "professional[phone1]":     "(47) 99555-5555",
    }
    for nm, val in campos_inativo.items():
        inp = page_admin.locator(f"input[name='{nm}']")
        if inp.count():
            try:
                inp.first.fill(val, timeout=3000)
            except Exception:
                pass

    page_admin.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=5000)
    page_admin.wait_for_timeout(3500)
    snap(page_admin, "tc4_02_inativo_criado")

    body_new = page_admin.locator("body").inner_text()
    criou_inativo = "users/new" not in page_admin.url or inativo_email in body_new
    log(f"  [TC4] criou_inativo={criou_inativo}")

    if not criou_inativo:
        tc_resultado("TC4", "FALHOU", f"Não foi possível criar usuário descartável {inativo_email}")
        return

    entidades_criadas.append({"tipo": "usuario", "email": inativo_email, "acao": "criado_descartavel"})

    # Passo 3: Criar 2 registros externos para o usuário descartável
    rec_a = api_criar_registro_externo(page_admin, inativo_email, f"QA116-TC4-RegA-{rand}")
    rec_b = api_criar_registro_externo(page_admin, inativo_email, f"QA116-TC4-RegB-{rand}")

    rec_a_id = rec_a.get("id") if rec_a else None
    rec_b_id = rec_b.get("id") if rec_b else None
    log(f"  [TC4] registros criados: A={rec_a_id} B={rec_b_id}")

    if not rec_a_id and not rec_b_id:
        tc_resultado("TC4", "FALHOU", f"Registros do usuário descartável não criados via API")
        return

    entidades_criadas.append({
        "tipo": "registros_inativo",
        "email": inativo_email,
        "ids": [rec_a_id, rec_b_id],
    })

    # Passo 4: Confirmar visibilidade na lista
    ir_records(page_admin)
    aguardar_tabela(page_admin)
    kpis_com_inativo = ler_kpis(page_admin)
    total_com_inativo = api_total_records(page_admin)
    snap(page_admin, "tc4_03_com_inativo", full=True)
    log(f"  [TC4] KPIs com inativo: {kpis_com_inativo} total={total_com_inativo}")

    # Verificar se os registros aparecem na API
    recs_all = api_records_page(page_admin, per_page=50)
    vis_a = any(r.get("id") == rec_a_id for r in recs_all) if rec_a_id else False
    vis_b = any(r.get("id") == rec_b_id for r in recs_all) if rec_b_id else False
    log(f"  [TC4] visível A={vis_a} B={vis_b}")

    # Passo 5: Buscar ID do usuário e inativar via UI
    inativo_id = buscar_professional_id(page_admin, inativo_email)
    log(f"  [TC4] inativo_id={inativo_id}")

    inativou = False
    if inativo_id:
        # Tentar via API primeiro
        inativou = api_inativar_usuario(page_admin, inativo_id)
        log(f"  [TC4] inativou via API: {inativou}")

    if not inativou:
        # Fallback via UI
        page_admin.goto(
            f"{BASE_URL}/o/{ORG_ID}/users?search={inativo_email}",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        page_admin.wait_for_timeout(2000)
        snap(page_admin, "tc4_04_busca_inativo")

        # Clicar kebab e Inativar
        try:
            row = page_admin.locator(f"tr:has-text('{inativo_email}')").first
            if row.count():
                kebab_btn = row.locator("button[aria-haspopup='menu'], button:has-text('more_vert')")
                if kebab_btn.count():
                    kebab_btn.first.click(force=True)
                    page_admin.wait_for_timeout(1200)
                    item_inativar = page_admin.locator("[role='menuitem']").filter(
                        has_text=re.compile(r"inativ", re.I)
                    )
                    if item_inativar.count():
                        item_inativar.first.click()
                        page_admin.wait_for_timeout(2000)
                        # Confirmar modal se houver
                        btn_conf = page_admin.locator("button").filter(has_text=re.compile(r"inativ|confirm|sim", re.I))
                        if btn_conf.count():
                            btn_conf.first.click()
                            page_admin.wait_for_timeout(2000)
                        inativou = True
                        log("  [TC4] inativou via UI kebab")
        except Exception as e:
            log(f"  [TC4] erro UI inativar: {e}")

    if not inativou:
        tc_resultado("TC4", "FALHOU", f"Não foi possível inativar usuário {inativo_email}")
        return

    entidades_criadas.append({"tipo": "inativacao", "email": inativo_email, "acao": "INATIVADO"})
    snap(page_admin, "tc4_05_pos_inativacao")

    # Passo 6: Verificar KPIs e lista
    page_admin.wait_for_timeout(2000)
    ir_records(page_admin)
    aguardar_tabela(page_admin)
    kpis_depois = ler_kpis(page_admin)
    total_depois = api_total_records(page_admin)
    snap(page_admin, "tc4_06_kpis_depois", full=True)
    log(f"  [TC4] KPIs depois: {kpis_depois} total={total_depois}")

    soma_antes = sum(kpis_com_inativo.values())
    soma_depois = sum(kpis_depois.values())
    delta = soma_antes - soma_depois
    log(f"  [TC4] delta KPI: {soma_antes} - {soma_depois} = {delta}")

    # Verificar se registros sumiram da lista
    recs_depois = api_records_page(page_admin, per_page=50)
    ainda_vis_a = any(r.get("id") == rec_a_id for r in recs_depois) if rec_a_id else False
    ainda_vis_b = any(r.get("id") == rec_b_id for r in recs_depois) if rec_b_id else False
    log(f"  [TC4] ainda visível A={ainda_vis_a} B={ainda_vis_b}")

    # Verificar se busca pelo nome retorna "nenhum"
    ir_records(page_admin)
    aguardar_tabela(page_admin)
    search_inp = page_admin.locator("input[placeholder*='Pesquise']").first
    nenhum_result = False
    if search_inp.count():
        search_inp.fill(f"QAInativo")
        page_admin.wait_for_timeout(2000)
        snap(page_admin, "tc4_07_busca_nome_inativo", full=True)
        body_busca = page_admin.locator("body").inner_text()
        nenhum_result = (
            "nenhum" in body_busca.lower()
            or "0 registro" in body_busca.lower()
            or page_admin.locator("tbody tr").count() == 0
        )
        log(f"  [TC4] busca nome inativo → nenhum_result={nenhum_result}")

    # Veredito
    qtd_registros_criados = (1 if rec_a_id else 0) + (1 if rec_b_id else 0)
    kpis_decrementaram = soma_depois < soma_antes
    registros_sumiram = not ainda_vis_a and not ainda_vis_b

    if kpis_decrementaram and registros_sumiram:
        tc_resultado(
            "TC4",
            "PASSOU",
            f"KPIs decrementaram ({soma_antes}→{soma_depois}, delta={delta}); "
            f"registros do inativo sumiram da lista; "
            f"busca por nome→nenhum={nenhum_result}",
        )
    elif kpis_decrementaram and not registros_sumiram:
        tc_resultado(
            "TC4",
            "FALHOU",
            f"KPIs decrementaram mas registros ainda visíveis (A={ainda_vis_a} B={ainda_vis_b})",
        )
    elif not kpis_decrementaram and registros_sumiram:
        tc_resultado(
            "TC4",
            "FALHOU",
            f"Registros sumiram mas KPIs não decrementaram ({soma_antes}→{soma_depois})",
        )
    else:
        tc_resultado(
            "TC4",
            "FALHOU",
            f"KPIs não decrementaram ({soma_antes}→{soma_depois}) E registros ainda visíveis (A={ainda_vis_a} B={ainda_vis_b})",
        )


# ─── TC5: KPI sum = total paginado ───────────────────────────────────────────

def executar_tc5(page_admin):
    log("\n=== TC5 — KPI sum = total paginado ===")

    ir_records(page_admin)
    aguardar_tabela(page_admin)
    kpis = ler_kpis(page_admin)
    snap(page_admin, "tc5_01_kpis", full=True)

    total_api = api_total_records(page_admin)
    soma_kpis = sum(kpis.values())

    log(f"  [TC5] kpis={kpis} soma={soma_kpis} total_api={total_api}")

    if total_api < 0:
        tc_resultado("TC5", "FALHOU", "API de registros retornou erro ao buscar total")
        return

    if soma_kpis == total_api:
        tc_resultado(
            "TC5",
            "PASSOU",
            f"KPI sum ({soma_kpis}) = total paginado ({total_api}) — coerência confirmada",
        )
    else:
        tc_resultado(
            "TC5",
            "FALHOU",
            f"KPI sum ({soma_kpis}) ≠ total paginado ({total_api}) — inconsistência",
        )


# ─── TC6-TC10: SharedEvent / multi-org ───────────────────────────────────────

def executar_tc6_a_tc10(page_admin):
    log("\n=== TC6-TC10 — SharedEvent / multi-org ===")

    # Verificar se existem registros com origin=shared
    recs = api_records_page(page_admin, per_page=50)
    shared = [r for r in recs if r.get("origin") == "shared"]
    log(f"  [TC6] registros compartilhados na primeira página: {len(shared)}")

    snap(page_admin, "tc6_check_shared")

    motivo = (
        "Registros Compartilhados (origin=shared) vêm de SharedEvent de org parceira. "
        "A org 37079 não tem parceiro configurado e não é possível criar origin=shared "
        "via API sem infraestrutura de outra org. "
        "TC6-TC10 requerem setup de org parceira — solicitar ao João Miguel."
    )

    for tc in ["TC6", "TC7", "TC8", "TC9", "TC10"]:
        tc_resultado(tc, "FALHOU", f"BLOQUEADO: {motivo}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    log("=== QA 1.16 v2 — Registros F2 — Escopo do Líder / Inativados ===\n")

    with tw.sync_playwright() as p:
        # Sessão admin
        ba, ca, page_admin = tw.nova_pagina(p)
        tw.login(
            page_admin,
            {
                "base_url": BASE_URL,
                "org_id": ORG_ID,
                "email": ADMIN_EMAIL,
                "senha": ADMIN_PASSWORD,
            },
            admin=True,
        )
        log("  [Admin] logado OK")
        dispensar_overlays(page_admin)

        # ── SETUP ─────────────────────────────────────────────
        criou_lider = criar_lider_puro(page_admin)
        org_ok = montar_organograma_api(page_admin)
        dados_rec = criar_registros_setup(page_admin)

        rec_liderado = dados_rec.get("rec_liderado") or {}
        rec_fora = dados_rec.get("rec_fora") or {}
        rec_liderado_id = rec_liderado.get("id") if rec_liderado else None
        rec_fora_id = rec_fora.get("id") if rec_fora else None

        liderado_id = buscar_professional_id(page_admin, LIDERADO_EMAIL)
        log(f"\n  [SETUP RESUMO] lider_criado={criou_lider} org_ok={org_ok} "
            f"rec_liderado={rec_liderado_id} rec_fora={rec_fora_id} liderado_id={liderado_id}")
        snap(page_admin, "setup_concluido")

        # ── Sessão líder puro ──────────────────────────────────
        bd, cd, page_lider = tw.nova_pagina(p)
        page_lider.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=20000)
        page_lider.fill("#user_email", LIDER_PURO_EMAIL)
        page_lider.fill("#user_password", LIDER_PURO_PASSWORD)
        page_lider.click("#user_submit")
        try:
            page_lider.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        page_lider.wait_for_timeout(2500)
        dispensar_overlays(page_lider)
        url_lider_inicial = page_lider.url
        lider_logou = "/login" not in url_lider_inicial
        log(f"  [Líder puro] logou={lider_logou} url={url_lider_inicial}")
        snap(page_lider, "setup_lider_login")

        # ── TCs principais ─────────────────────────────────────
        if lider_logou:
            executar_tc1(page_admin, page_lider, rec_liderado_id, rec_fora_id)
            executar_tc2(page_lider, rec_fora_id)
            executar_tc3(page_admin, page_lider, rec_liderado_id, liderado_id)
        else:
            for tc in ["TC1", "TC2", "TC3"]:
                tc_resultado(tc, "FALHOU", f"Líder puro não conseguiu logar (URL={url_lider_inicial})")

        executar_tc4(page_admin)
        executar_tc5(page_admin)
        executar_tc6_a_tc10(page_admin)

        try:
            ca.close(); ba.close()
            cd.close(); bd.close()
        except Exception:
            pass

    # ── SUMÁRIO ────────────────────────────────────────────────
    log("\n" + "=" * 60)
    log("SUMÁRIO QA 1.16 v2")
    log("=" * 60)

    tcs = ["TC1", "TC2", "TC3", "TC4", "TC5", "TC6", "TC7", "TC8", "TC9", "TC10"]
    passou = falhou = 0
    for tc in tcs:
        if tc in resultados:
            r = resultados[tc]
            v = r["veredito"]
            i = "v" if v == "PASSOU" else "x"
            log(f"  [{i}] {tc}: {v} — {r['resumo'][:120]}")
            if v == "PASSOU":
                passou += 1
            else:
                falhou += 1
        else:
            log(f"  [?] {tc}: NAO EXECUTADO")

    log(f"\n  PLACAR: {passou} PASSOU | {falhou} FALHOU")
    log(f"\n  ENTIDADES CRIADAS ({len(entidades_criadas)}):")
    for e in entidades_criadas:
        log(f"    {e}")

    # Salvar resultados
    saida = {
        "resultados": resultados,
        "entidades_criadas": entidades_criadas,
    }
    out_path = PASTA / "resultados_v2.json"
    out_path.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"\n  [saida] {out_path}")


if __name__ == "__main__":
    main()
