# -*- coding: utf-8 -*-
"""Debug C — criar registros via UI, buscar IDs, corrigir senha do líder."""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)

log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

def dispensar(pg):
    tw.dispensar_nps(pg)
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

def abrir_dropdown_label(pg, label_txt):
    """Abre dropdown Chakra pelo texto do label."""
    try:
        lbl = pg.locator(f"label:has-text('{label_txt}')").first
        if lbl.count():
            container = lbl.locator("xpath=following-sibling::div[1]")
            if container.count():
                container.click(timeout=4000)
                pg.wait_for_timeout(1000)
                return True
    except Exception as e:
        log(f"  [dropdown] erro: {e}")
    return False

def criar_registro_ui(pg, pessoa_email, conteudo):
    """Cria registro externo via form da UI como admin."""
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)
    snap(pg, f"criar_rec_{conteudo[:20].replace(' ','_')}_01_form")
    log(f"  [form] url={pg.url}")

    # Campo Pessoas — dropdown para selecionar o usuário
    # Primeiro encontrar o campo
    pessoas_aberto = False
    for sel in [
        "[data-test-id='people-selector-hidden-input']",
        "label:has-text('Pessoas')",
        "label:has-text('Person')",
    ]:
        el = pg.locator(sel).first
        if el.count():
            try:
                container = el.locator("xpath=..") if "hidden-input" in sel else el.locator("xpath=following-sibling::div[1]")
                container.click(timeout=4000)
                pg.wait_for_timeout(1500)
                pessoas_aberto = True
                break
            except: pass

    if pessoas_aberto:
        # Digitar o email para buscar
        pg.keyboard.type(pessoa_email, delay=40)
        pg.wait_for_timeout(2000)
        opcao = pg.locator("[role='option']").first
        if opcao.count():
            opcao.click()
            pg.wait_for_timeout(500)
            log(f"  [pessoas] selecionou {pessoa_email}")
        else:
            log(f"  [pessoas] nenhuma opcao para {pessoa_email}")

    snap(pg, f"criar_rec_{conteudo[:20].replace(' ','_')}_02_pessoas")

    # Conteúdo
    try:
        cont_inp = pg.get_by_label("Conteúdo").first
        if cont_inp.count() == 0:
            cont_inp = pg.locator("input[name*='content'], input[placeholder*='onteúdo'], input[placeholder*='onteudo']").first
        if cont_inp.count() == 0:
            cont_inp = pg.locator("label:has-text('Conteúdo')").locator("xpath=following-sibling::input[1]").first
        if cont_inp.count():
            cont_inp.first.fill(conteudo, timeout=4000)
            log(f"  [conteudo] preenchido: {conteudo}")
    except Exception as e:
        log(f"  [conteudo] erro: {e}")

    # Provedor — selecionar primeira opção
    if abrir_dropdown_label(pg, "Provedor"):
        opcoes = pg.locator("[role='option']").all()
        if opcoes:
            opcoes[0].click()
            pg.wait_for_timeout(500)
            log("  [provedor] selecionado")

    # Tipo de experiência
    if abrir_dropdown_label(pg, "Tipo de experiência"):
        opcoes = pg.locator("[role='option']").all()
        if opcoes:
            opcoes[0].click()
            pg.wait_for_timeout(500)
            log("  [tipo] selecionado")

    # Categorias
    if abrir_dropdown_label(pg, "Categorias"):
        opcoes = pg.locator("[role='option']").all()
        if opcoes:
            opcoes[0].click()
            pg.wait_for_timeout(500)
            pg.keyboard.press("Escape")
            log("  [categorias] selecionado")

    # Carga horária — tentar preencher
    try:
        carga_inp = pg.locator("input[placeholder*='horária'], input[placeholder*='horaria'], input[name*='workload']").first
        if carga_inp.count() == 0:
            carga_inp = pg.get_by_label("Carga horária").first
        if carga_inp.count():
            carga_inp.fill("01:00:00", timeout=4000)
            log("  [carga] preenchida")
    except Exception as e:
        log(f"  [carga] erro: {e}")

    # Data de término
    try:
        date_inp = pg.locator("input[type='date']").first
        if date_inp.count():
            date_inp.fill("2026-06-01", timeout=4000)
            log("  [data] preenchida")
    except Exception as e:
        log(f"  [data] erro: {e}")

    snap(pg, f"criar_rec_{conteudo[:20].replace(' ','_')}_03_preenchido")

    # Salvar
    btn_salvar = pg.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first
    btn_salvar.click(timeout=5000)
    pg.wait_for_timeout(4000)
    snap(pg, f"criar_rec_{conteudo[:20].replace(' ','_')}_04_salvo")

    url_depois = pg.url
    log(f"  [salvar] url={url_depois}")

    # Buscar ID do registro criado (URL ou via API)
    criou = "records/new" not in url_depois
    rec_id = None
    if criou:
        m = re.search(r"/records/(\d+)", url_depois)
        if m:
            rec_id = int(m.group(1))
        else:
            # Buscar na lista por conteúdo
            resp = pg.request.get(
                f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=25&page=1&order_by=created_at&order_type=desc",
                headers={"Accept":"application/json"},
            )
            if resp.status == 200:
                recs = resp.json().get("data",{}).get("records",[])
                match = next((r for r in recs if conteudo in str(r.get("content",""))), None)
                if match:
                    rec_id = match.get("id")

    log(f"  [criar_registro] criou={criou} rec_id={rec_id} conteudo={conteudo}")
    return rec_id

def buscar_user_id_via_pagina(pg, search_term):
    """Busca ID de usuário navegando pela lista e capturando a URL de edição."""
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=15000)
    pg.wait_for_timeout(2000)

    # Tentar campo de busca
    search_inp = pg.locator("input[placeholder*='Pesquise'], input[placeholder*='Busca'], input[type='search']").first
    if search_inp.count():
        search_inp.fill(search_term)
        pg.wait_for_timeout(2000)

    snap(pg, f"busca_user_{search_term[:10]}")

    # Procurar botão kebab na linha do usuário e abrir edição
    # Tentar capturar da href de algum link na row
    body_text = pg.locator("body").inner_text()
    log(f"  [users page] search={search_term} body snippet: {body_text[:200]}")

    # Tentar clicar no kebab da linha que contém o email
    rows = pg.locator("tr, [role='row']").all()
    for row in rows:
        try:
            rt = row.inner_text()
            if search_term.lower() in rt.lower() or search_term.split("@")[0].lower() in rt.lower():
                # Tentar abrir kebab desta linha
                kebab = row.locator("button[aria-haspopup='menu'], button:has-text('more_vert')").first
                if kebab.count():
                    kebab.click(force=True)
                    pg.wait_for_timeout(1000)
                    # Procurar item "Editar"
                    editar = pg.locator("[role='menuitem']").filter(has_text="Editar").first
                    if editar.count():
                        editar.click()
                        pg.wait_for_timeout(2000)
                        url_edit = pg.url
                        m = re.search(r"/users/(\d+)/edit", url_edit)
                        if m:
                            uid = int(m.group(1))
                            log(f"  [user_id] {search_term} → id={uid} url={url_edit}")
                            pg.go_back()
                            pg.wait_for_timeout(1500)
                            return uid
        except Exception as e:
            pass

    return None

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # 1. Buscar IDs de usuários via página
    log("\n--- 1. Buscar IDs de usuários ---")
    ids_encontrados = {}
    for email in ["liderado1@teste.com", "qaliderpuro@teste.com", "devtestes@teste.com"]:
        uid = buscar_user_id_via_pagina(pg, email)
        ids_encontrados[email] = uid
        log(f"  {email} → id={uid}")

    log(f"\n  IDs: {ids_encontrados}")

    # 2. Se qaliderpuro existe, corrigir senha
    log("\n--- 2. Corrigir senha qaliderpuro ---")
    uid_lider = ids_encontrados.get("qaliderpuro@teste.com")
    if uid_lider:
        pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{uid_lider}/edit", wait_until="domcontentloaded", timeout=15000)
        pg.wait_for_timeout(2000)
        snap(pg, "lider_edit")
        # Definir senha
        pwd = pg.locator("input[name='professional[password]']").first
        if pwd.count():
            pwd.fill("123456")
            conf = pg.locator("input[name='professional[password_confirmation]']").first
            if conf.count(): conf.fill("123456")
            pg.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=5000)
            pg.wait_for_timeout(2000)
            log(f"  senha definida. url={pg.url}")
            snap(pg, "lider_senha_salva")
    else:
        log("  qaliderpuro não encontrado via kebab — criação pode ter falhado")
        # Verificar se a criação funcionou de outra forma
        pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=15000)
        pg.wait_for_timeout(2000)
        snap(pg, "users_list_busca_lider", )

    # 3. Tentar criar registro via UI para liderado1
    log("\n--- 3. Criar registro via UI para liderado1 ---")
    rec_liderado_id = criar_registro_ui(pg, "liderado1@teste.com", "QA116-Liderado-Externo")
    log(f"  rec_liderado_id = {rec_liderado_id}")

    # 4. Tentar criar registro via UI para devtestes
    log("\n--- 4. Criar registro via UI para devtestes ---")
    rec_fora_id = criar_registro_ui(pg, "devtestes@teste.com", "QA116-ForaEquipe-Externo")
    log(f"  rec_fora_id = {rec_fora_id}")

    # 5. Verificar paginação correta
    log("\n--- 5. Verificar paginação total ---")
    resp = pg.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=1&page=1", headers={"Accept":"application/json"})
    if resp.status == 200:
        data = resp.json().get("data",{})
        pag = data.get("pagination",{})
        log(f"  pagination: {pag}")
        log(f"  total_entries: {pag.get('total_entries','?')}")

    # 6. Verificar se login do líder funciona agora
    log("\n--- 6. Testar login do líder ---")
    if uid_lider:
        bd, cd, pg_l = tw.nova_pagina(p)
        pg_l.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
        pg_l.fill("#user_email", "qaliderpuro@teste.com")
        pg_l.fill("#user_password", "123456")
        pg_l.click("#user_submit")
        try: pg_l.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        pg_l.wait_for_timeout(2000)
        log(f"  login qaliderpuro: url={pg_l.url}")
        snap(pg_l, "lider_login_teste")
        cd.close(); bd.close()

    # Salvar resultado
    resultado = {
        "ids_usuarios": ids_encontrados,
        "rec_liderado_id": rec_liderado_id,
        "rec_fora_id": rec_fora_id,
    }
    (PASTA/"debug_c_resultado.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"\n  Resultado salvo em debug_c_resultado.json")

    ca.close(); ba.close()
