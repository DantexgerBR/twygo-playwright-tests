"""retrabalho_provedor_aluno_401.py -- Valida retrabalho Artia #20298
P2 [Registros F2] API de provedores retorna 401 para o perfil Aluno (TC7)

Bug original: GET /api/v1/o/37079/event_sources/get_provider_names retornava
401 para o Aluno -> combobox "Provedor" aparecia vazio no form
/records/new?in_use_mode_layout=true. Admin via lista completa.

PR https://github.com/Twygo/twyg-app/pull/10835 corrigiu a autorizacao do
endpoint para permitir o perfil Aluno.

Este script porta a logica ja validada em scripts/run_qa16_round2b.py
(funcao tc7_provedor_aluno_real), cobrindo:
  - Aluno principal (REGISTROSF2_ALUNO_EMAIL)
  - Aluno TC3 (REGISTROSF2_TC3_EMAIL) -- segundo usuario p/ evitar falso negativo
  - Admin como controle (sem regressao esperada)

Rodar: .\.venv\Scripts\python.exe scripts/retrabalho_provedor_aluno_401.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID = os.environ.get("REGISTROSF2_ORG_ID", "37079")

ADMIN_EMAIL = os.environ["REGISTROSF2_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["REGISTROSF2_ADMIN_PASSWORD"]
ALUNO_EMAIL = os.environ["REGISTROSF2_ALUNO_EMAIL"]
ALUNO_PASSWORD = os.environ["REGISTROSF2_ALUNO_PASSWORD"]
TC3_EMAIL = os.environ.get("REGISTROSF2_TC3_EMAIL")
TC3_PASSWORD = os.environ.get("REGISTROSF2_TC3_PASSWORD")

SLUG = "registros-f2-qa16-retrabalho"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)

NEW_FORM_ADMIN = f"{BASE_URL}/o/{ORG_ID}/records/new"
NEW_FORM_ALUNO = f"{BASE_URL}/o/{ORG_ID}/records/new?in_use_mode_layout=true"

PROVEDORES_ESPERADOS = ["alura", "coursera", "fgv", "linkedin", "nocode", "udemy", "usp"]

results = {}


def log(msg):
    print(msg)


def r(perfil, passou, nota=""):
    results[perfil] = {"pass": passou, "note": nota}
    status = "PASSOU" if passou else "FALHOU"
    print(f"  [{status}] {perfil}: {nota}")


def dispensar_overlays(page):
    tw.dispensar_nps(page)
    try:
        page.evaluate("""() => {
            document.querySelectorAll('#hubspot-messages-iframe-container,[id*="sophia"],[id*="hubspot"]')
                .forEach(e => e.style.display='none');
        }""")
    except Exception:
        pass
    try:
        btn = page.locator("button:has-text('Continuar mesmo assim')").first
        if btn.count() > 0 and btn.is_visible():
            btn.click()
            page.wait_for_timeout(500)
    except Exception:
        pass


def aguardar_sem_spinner(page, timeout=15000):
    try:
        page.wait_for_selector(".chakra-spinner", state="hidden", timeout=timeout)
    except Exception:
        pass


def login_como(page, email, senha, admin=False):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", email)
    page.fill("#user_password", senha)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    dispensar_overlays(page)
    if admin:
        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
            wait_until="domcontentloaded", timeout=30000,
        )
        page.wait_for_timeout(2000)
        dispensar_overlays(page)
    ok = "/login" not in page.url
    log(f"  [login] {email} -> ok={ok}")
    return ok


def ir_para_form(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    page.wait_for_timeout(1000)


def checar_provedor(browser, perfil_nome, email, senha, admin, snap_prefix):
    """Loga, escuta a API get_provider_names, abre o form e le o combobox Provedor.
    Retorna (opcoes: list[str], status_api: int|None, url_api: str|None)."""
    log("\n" + "=" * 60)
    log(f"Perfil: {perfil_nome} ({email})")
    log("=" * 60)

    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
    page = ctx.new_page()

    respostas_prov = []

    def capturar(resp):
        url_l = resp.url.lower()
        if "get_provider_names" in url_l or "event_source" in url_l or "provider" in url_l:
            info = {"url": resp.url, "status": resp.status}
            respostas_prov.append(info)
            log(f"  [{resp.status}] API Provedor: {resp.url[:110]}")

    page.on("response", capturar)

    ok = login_como(page, email, senha, admin=admin)
    if not ok:
        r(perfil_nome, False, "Login falhou")
        ctx.close()
        return [], None, None

    form_url = NEW_FORM_ADMIN if admin else NEW_FORM_ALUNO
    ir_para_form(page, form_url)
    page.wait_for_timeout(2000)  # aguardar requests iniciais de get_provider_names

    opcoes = []
    try:
        combos = page.locator("[role='combobox']").all()
        log(f"  Total comboboxes: {len(combos)}")
        if combos:
            combos[0].click(timeout=5000)
            page.wait_for_timeout(1500)
            opcoes = page.locator("[role='option']").all_text_contents()
            log(f"  Opcoes combobox[0] (Provedor): {opcoes}")
    except Exception as e:
        log(f"  Erro ao abrir combobox Provedor: {e}")

    if opcoes:
        tw.snap(page, EVID, f"{snap_prefix}_provedor_com_opcoes")
    else:
        tw.snap(page, EVID, f"{snap_prefix}_provedor_vazio")

    try:
        page.keyboard.press("Escape")
    except Exception:
        pass

    # Foco no endpoint especifico de nomes de provedor
    chamadas_get_names = [x for x in respostas_prov if "get_provider_names" in x["url"].lower()]
    status_api = chamadas_get_names[-1]["status"] if chamadas_get_names else None
    url_api = chamadas_get_names[-1]["url"] if chamadas_get_names else None

    if not chamadas_get_names:
        log("  [AVISO] endpoint get_provider_names nao foi observado na rede.")

    ctx.close()
    return opcoes, status_api, url_api


def eh_lista_provedor_valida(opcoes):
    return bool(opcoes) and any(any(p in op.lower() for p in PROVEDORES_ESPERADOS) for op in opcoes)


def avaliar(perfil_nome, opcoes, status_api):
    tem_lista = eh_lista_provedor_valida(opcoes)
    sem_401 = status_api is not None and status_api < 400
    if tem_lista and sem_401:
        r(perfil_nome, True, f"Combobox com provedores {opcoes} | API status={status_api}")
    elif tem_lista and status_api is None:
        r(perfil_nome, None, f"Combobox com provedores {opcoes} | API get_provider_names NAO observada na rede (possivel cache) -- INCONCLUSIVO parcial")
    elif not opcoes and status_api == 401:
        r(perfil_nome, False, f"Combobox vazio | API retornou 401 -- bug ainda presente")
    else:
        r(perfil_nome, None, f"Combobox={opcoes} | API status={status_api} -- padrao inesperado, revisar manualmente")


def main():
    log("=" * 60)
    log("Retrabalho Artia #20298 -- Provedor 401 para Aluno")
    log(f"URL: {BASE_URL} | Org: {ORG_ID}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser = p.chromium.launch(headless=os.environ.get("TW_HEADED") != "1", slow_mo=300)

        # 1. Aluno principal (o mesmo da evidencia original do bug)
        opcoes_aluno, status_aluno, url_aluno = checar_provedor(
            browser, "Aluno_principal", ALUNO_EMAIL, ALUNO_PASSWORD, admin=False,
            snap_prefix="01_aluno_principal",
        )
        avaliar("Aluno_principal", opcoes_aluno, status_aluno)

        # 2. Segundo aluno (TC3) -- evita falso negativo por usuario isolado
        if TC3_EMAIL and TC3_PASSWORD:
            opcoes_tc3, status_tc3, url_tc3 = checar_provedor(
                browser, "Aluno_TC3", TC3_EMAIL, TC3_PASSWORD, admin=False,
                snap_prefix="02_aluno_tc3",
            )
            avaliar("Aluno_TC3", opcoes_tc3, status_tc3)
        else:
            log("\n[AVISO] REGISTROSF2_TC3_EMAIL/PASSWORD nao definidos -- pulando segundo aluno")

        # 3. Admin como controle (nao deve regredir)
        opcoes_admin, status_admin, url_admin = checar_provedor(
            browser, "Admin_controle", ADMIN_EMAIL, ADMIN_PASSWORD, admin=True,
            snap_prefix="03_admin_controle",
        )
        avaliar("Admin_controle", opcoes_admin, status_admin)

        browser.close()

    log("\n" + "=" * 60)
    log("SUMARIO")
    log("=" * 60)
    for perfil, dados in results.items():
        status = {True: "PASSOU", False: "FALHOU", None: "INCONCLUSIVO"}[dados["pass"]]
        log(f"  {perfil}: {status} -- {dados['note']}")
    log("=" * 60)


if __name__ == "__main__":
    main()
