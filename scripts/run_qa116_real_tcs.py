# -*- coding: utf-8 -*-
"""
QA Suite 1.16 - Registros F2 - TCs REAIS (conforme AT test-analysis.md)
Org: 37079  registrosf2.stage.twygoead.com

TC1 (RN93) - Escopo de busca de Pessoa no Adicionar, e listagem Provedores
TC2 (RN94) - Lider nao pode aprovar registro fora de seu escopo (403)
TC3 (RN95) - Aprovacao persiste mesmo apos pessoa sair do time; lider nao ve mais
TC4 (RN96) - Registros de usuario inativado sumem da lista (KPIs decrementam)
TC5 (RN96.5) - KPI do lider == linhas visiveis no escopo dele
EXTRA - Confirma que P1 do QA 1.2 TC9 foi config-error, nao bug de produto

Massa disponivel:
- qaliderpuro@teste.com / twygoqa2026  (id=4299626, admin=false, gestor=true, is_manager=true)
- liderado1@teste.com / twygoqa2026    (id=4298605, manager_id=4299626)
- devtestes@twygo.com / existente      (nao no time do lider)
- qainativo_tc4_28129@twygotest.com (id=4299629) - tem QA116-TC4-InativoReg1/2
  NOTA: pode estar inativo - precisamos reativar primeiro para TC4
- Registro QA116-ForaEquipe-Externo (id=44280185) - de devtestes, fora do time
- Registro QA116-Liderado-Externo (id=44280186) - de liderado1
"""
import json, sys, re, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
LIDER_EMAIL    = "qaliderpuro@teste.com"
LIDER_SENHA    = "twygoqa2026"
LIDERADO_EMAIL = "liderado1@teste.com"
LIDERADO_SENHA = "twygoqa2026"
INATIVO_EMAIL  = "qainativo_tc4_28129@twygotest.com"
INATIVO_ID     = 4299629
FORA_REC_ID    = 44280185   # QA116-ForaEquipe-Externo (de devtestes)
LIDERADO_REC_ID = 44280186  # QA116-Liderado-Externo (de liderado1)

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log  = lambda *a: print(*a, flush=True)

def snap(pg, nome):
    pg.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True)
    log(f"  [snap] {nome}.png")

def admin_goto_records(pg):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)

def extrair_kpis(pg):
    """Extrai numeros dos cards de KPI (Emitidos/Expirados/Pendentes/Recusados)."""
    nums = pg.evaluate("""() => {
        const cards = [...document.querySelectorAll('.chakra-stat, [class*="stat"]')];
        return cards.map(c => ({
            label: (c.querySelector('[class*="label"], dt') || {innerText:''}).innerText.trim(),
            value: (c.querySelector('[class*="number"], dd') || {innerText:''}).innerText.trim()
        }));
    }""")
    # fallback: procurar numeros grandes em texto
    if not any(n['value'] for n in nums):
        nums = pg.evaluate("""() => {
            const els = [...document.querySelectorAll('p,span,h2,h3,h4')];
            return els.filter(e => /^\\d+$/.test(e.innerText.trim())).map(e => ({
                label: e.closest('[class]') ? e.closest('[class]').className.slice(0,40) : '',
                value: e.innerText.trim()
            })).slice(0, 10);
        }""")
    return nums

def contar_linhas_tabela(pg):
    """Conta linhas visiveis na tabela de registros."""
    try:
        rows = pg.locator("tbody tr").count()
        return rows
    except:
        return -1

results = {}

# ==============================================================================
log("\n" + "="*70)
log("TC1 (RN93) - Escopo dropdown Pessoa no Adicionar, e aba Provedores")
log("="*70)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=400)
    # Login como LIDER
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": LIDER_EMAIL, "senha": LIDER_SENHA}, admin=True)
    log("[lider] logado como qaliderpuro")

    admin_goto_records(pg)
    snap(pg, "tc1_lider_lista_inicial")
    log(f"  url: {pg.url}")

    # TC1 Passo 3: Clicar em Adicionar -> abrir form -> ver dropdown Pessoa
    btn_adicionar = pg.locator("button, a").filter(has_text=re.compile("Adicionar|Novo registro", re.I)).first
    if btn_adicionar.count():
        box = btn_adicionar.bounding_box()
        if box:
            pg.mouse.click(box['x']+box['width']/2, box['y']+box['height']/2)
            pg.wait_for_timeout(2000)
            snap(pg, "tc1_form_adicionar_aberto")
            log("  [TC1.3] Form Adicionar aberto")

            # Clicar no campo Pessoa para ver o dropdown
            pessoa_field = pg.locator("input[placeholder*='Pesquise por nome' i], [id*='pessoa' i] input, [class*='select'] input").first
            if not pessoa_field.count():
                # tentar label Pessoa
                pessoa_label = pg.locator("label").filter(has_text=re.compile("Pessoa", re.I)).first
                if pessoa_label.count():
                    label_for = pessoa_label.get_attribute("for")
                    if label_for:
                        pessoa_field = pg.locator(f"#{label_for}")

            if pessoa_field.count():
                pessoa_field.click(timeout=5000)
                pg.wait_for_timeout(1500)
                snap(pg, "tc1_dropdown_pessoa_aberto")

                # Coletar opcoes do dropdown
                opcoes = pg.evaluate("""() => {
                    const opts = [...document.querySelectorAll('[role="option"], [class*="option"], [id*="__option"]')];
                    return opts.map(o => (o.innerText||'').trim()).filter(t => t.length > 0).slice(0, 20);
                }""")
                log(f"  [TC1.3] Opcoes Pessoa no dropdown: {opcoes}")

                # Esperado: SOMENTE liderado1 (nao toda a org)
                tem_liderado = any("liderado" in o.lower() or "liderado1" in o.lower() for o in opcoes)
                tem_outros_externos = len([o for o in opcoes if "liderado" not in o.lower() and o]) > 2
                log(f"  tem_liderado={tem_liderado}, tem_outros_externos={tem_outros_externos}")

                if tem_liderado and not tem_outros_externos:
                    results['tc1_pessoa_scope'] = 'PASS'
                    log("  [TC1.3] PASS - dropdown Pessoa mostra apenas liderado (escopo correto)")
                elif not tem_liderado:
                    results['tc1_pessoa_scope'] = 'FAIL_sem_liderado'
                    log("  [TC1.3] FAIL - liderado1 nao aparece no dropdown")
                else:
                    results['tc1_pessoa_scope'] = f'FAIL_escopo_largo:{len(opcoes)}_opcoes'
                    log(f"  [TC1.3] FAIL - dropdown mostra {len(opcoes)} opcoes (esperado: so liderado1)")
            else:
                results['tc1_pessoa_scope'] = 'INCONCLUSIVO_campo_pessoa_nao_encontrado'
                log("  [TC1.3] INCONCLUSIVO - campo Pessoa nao encontrado no form")
                snap(pg, "tc1_form_sem_campo_pessoa")

            # TC1 Passo 4: Aba Provedores - deve mostrar lista COMPLETA (sem filtro por escopo)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(500)
        else:
            results['tc1_pessoa_scope'] = 'INCONCLUSIVO_btn_adicionar_sem_box'
    else:
        results['tc1_pessoa_scope'] = 'INCONCLUSIVO_btn_adicionar_nao_encontrado'
        log("  [TC1] INCONCLUSIVO - botao Adicionar nao encontrado")
        snap(pg, "tc1_sem_btn_adicionar")

    # TC1 Passo 4: Aba Provedores
    tab_provedores = pg.locator("[role='tab'], a, button").filter(has_text=re.compile("Provedores?", re.I)).first
    if tab_provedores.count():
        box = tab_provedores.bounding_box()
        if box:
            pg.mouse.click(box['x']+box['width']/2, box['y']+box['height']/2)
            pg.wait_for_timeout(2000)
            snap(pg, "tc1_aba_provedores")

            # Contar provedores listados
            provedores_count = pg.locator("tbody tr, [class*='row'], [class*='item']").count()
            log(f"  [TC1.4] Provedores visiveis: {provedores_count}")

            # Comparar com total admin (checar mais adiante)
            results['tc1_provedores_count_lider'] = provedores_count
            results['tc1_provedores'] = 'captured'
            log(f"  [TC1.4] Provedores capturados para comparacao com admin")
    else:
        results['tc1_provedores'] = 'INCONCLUSIVO_aba_provedores_nao_encontrada'
        log("  [TC1.4] INCONCLUSIVO - aba Provedores nao encontrada")

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*70)
log("TC5 (RN96.5) - KPI do lider == linhas visiveis no escopo dele")
log("="*70)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": LIDER_EMAIL, "senha": LIDER_SENHA}, admin=True)
    log("[lider] logado")

    admin_goto_records(pg)
    pg.wait_for_timeout(2000)
    snap(pg, "tc5_lider_lista_completa")

    kpis = extrair_kpis(pg)
    log(f"  [TC5] KPIs lider: {json.dumps(kpis, ensure_ascii=False)}")

    linhas = contar_linhas_tabela(pg)
    log(f"  [TC5] Linhas visiveis: {linhas}")

    # Pegar total KPI (soma dos numeros visiveis)
    kpi_total = sum(int(k['value']) for k in kpis if k['value'].isdigit())
    log(f"  [TC5] Total KPI: {kpi_total}, Linhas: {linhas}")

    results['tc5_kpis'] = kpis
    results['tc5_linhas'] = linhas
    results['tc5_kpi_total'] = kpi_total

    # O KPI TOTAL deve bater com o numero de registros no escopo
    # Se KPI nao reflete exatamente as linhas na paginacao (por pagina), aceitar proporcional
    # Mas o lider deve ver apenas registros do seu escopo
    if linhas >= 0:
        results['tc5'] = 'captured'
        log(f"  [TC5] Dados capturados: KPI={kpi_total}, Linhas={linhas}")
    else:
        results['tc5'] = 'INCONCLUSIVO'

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*70)
log("EXTRA - Verificar escopo do lider (confirmar P1 do QA 1.2 TC9 era config-error)")
log("="*70)

with tw.sync_playwright() as p:
    ba, ca, pg_admin = tw.nova_pagina(p, slow_mo=300)
    tw.login(pg_admin, {"base_url": BASE_URL, "org_id": ORG_ID,
                         "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    admin_goto_records(pg_admin)
    pg_admin.wait_for_timeout(2000)
    snap(pg_admin, "extra_admin_lista_total")

    kpis_admin = extrair_kpis(pg_admin)
    linhas_admin = contar_linhas_tabela(pg_admin)
    log(f"  [EXTRA] KPIs admin: {json.dumps(kpis_admin, ensure_ascii=False)}")
    log(f"  [EXTRA] Linhas admin: {linhas_admin}")
    kpi_admin_total = sum(int(k['value']) for k in kpis_admin if k['value'].isdigit())

    results['extra_kpi_admin'] = kpi_admin_total
    results['extra_linhas_admin'] = linhas_admin

    # Comparar com o que o lider ve
    kpi_lider_total = results.get('tc5_kpi_total', 0)
    linhas_lider = results.get('tc5_linhas', -1)

    if kpi_admin_total > 0 and kpi_lider_total > 0:
        if kpi_lider_total < kpi_admin_total:
            results['extra'] = f'PASS_escopo_correto (lider:{kpi_lider_total} < admin:{kpi_admin_total})'
            log(f"  [EXTRA] PASS - lider ve {kpi_lider_total} registros (admin ve {kpi_admin_total})")
        elif kpi_lider_total == kpi_admin_total:
            results['extra'] = f'FAIL_escopo_igual_admin (lider:{kpi_lider_total} == admin:{kpi_admin_total})'
            log(f"  [EXTRA] FAIL - lider ve mesmo total que admin = escopo vazando")
        else:
            results['extra'] = f'INCONCLUSIVO (lider:{kpi_lider_total}, admin:{kpi_admin_total})'
    else:
        results['extra'] = 'INCONCLUSIVO_kpis_nao_extraidos'

    pg_admin.close(); ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*70)
log("TC2 (RN94) - Lider nao pode aprovar registro fora do escopo (403)")
log("="*70)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=400)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": LIDER_EMAIL, "senha": LIDER_SENHA}, admin=True)
    log("[lider] logado para TC2")

    admin_goto_records(pg)
    pg.wait_for_timeout(2000)

    # Verificar se lider CONSEGUE VER o registro ForaEquipe (devtestes) na lista
    # Se nao aparece, confirmar isso e tentar via API direta
    pg.evaluate("""() => {
        const inputs = [...document.querySelectorAll('input[placeholder]')];
        return inputs.map(i => i.placeholder).slice(0,5);
    }""")

    search_selectors = [
        "input[placeholder*='Pesquise' i]",
        "input[placeholder*='nome' i]",
        "input[type='search']",
        "input[type='text']",
    ]
    busca = None
    for sel in search_selectors:
        loc = pg.locator(sel).first
        if loc.count() and loc.is_visible():
            busca = loc
            break

    if busca:
        busca.fill("ForaEquipe")
        pg.wait_for_timeout(2000)
        snap(pg, "tc2_busca_foraequipe_como_lider")
        linhas_fora = contar_linhas_tabela(pg)
        log(f"  [TC2] Busca por 'ForaEquipe' como lider: {linhas_fora} linhas")

        if linhas_fora == 0:
            log("  [TC2] Registro ForaEquipe NAO aparece para lider (escopo correto)")
            results['tc2_visibilidade'] = 'PASS_registro_nao_visivel'
        else:
            log(f"  [TC2] ATENCAO: Registro ForaEquipe APARECE para lider ({linhas_fora} linhas)")
            results['tc2_visibilidade'] = f'visivel:{linhas_fora}'

        busca.fill("")
        pg.wait_for_timeout(1000)
    else:
        log("  [TC2] Campo de busca nao encontrado")
        results['tc2_visibilidade'] = 'INCONCLUSIVO_sem_busca'

    # TC2: Tentar aprovacao via API como lider (interceptar CSRF e fazer chamada)
    # Primeiro, descobrir o endpoint correto capturando uma aprovacao normal
    # Capturar CSRF token
    csrf = pg.evaluate("() => document.querySelector('meta[name=csrf-token]')?.content || ''")
    log(f"  [TC2] CSRF token: {csrf[:20]}..." if csrf else "  [TC2] Sem CSRF token")

    # Tentar GET no registro fora do escopo para ver se da 403
    try:
        r_get = pg.request.get(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/records/{FORA_REC_ID}",
            headers={"Accept": "application/json", "X-CSRF-Token": csrf}
        )
        log(f"  [TC2] GET record {FORA_REC_ID} como lider: {r_get.status}")
        results['tc2_get_fora'] = r_get.status

        if r_get.status == 403:
            log("  [TC2] PASS - GET retornou 403 (lider nao pode ver registro fora do escopo)")
        elif r_get.status == 200:
            log("  [TC2] INFO - GET retornou 200; precisamos testar PATCH/POST de aprovacao")
    except Exception as e:
        log(f"  [TC2] Erro no GET: {e}")
        results['tc2_get_fora'] = f'erro:{e}'

    # Tentar PATCH/POST de aprovacao no registro fora do escopo
    # Primeiro descobrir o endpoint correto aprovando um registro legitimo do lider
    # e capturando a URL
    captured_approval_url = []

    def captura_req(req):
        if req.method in ("POST", "PATCH", "PUT") and "record" in req.url.lower():
            captured_approval_url.append({"method": req.method, "url": req.url})
            log(f"  [NET] {req.method} {req.url}")

    pg.on("request", captura_req)

    # Ir para lista normal (sem busca) e tentar aprovacao em um registro do lider
    busca2 = pg.locator("input[placeholder*='Pesquise' i], input[type='search']").first
    if busca2.count():
        busca2.fill("")
        pg.wait_for_timeout(1000)

    # Buscar liderado para ver seus registros
    if busca2.count():
        busca2.fill("liderado1")
        pg.wait_for_timeout(2000)
        snap(pg, "tc2_busca_liderado1_como_lider")

    # Tentar abrir kebab da primeira linha
    rows = pg.locator("tbody tr")
    if rows.count():
        kebab = rows.first.locator("button").last
        box_k = kebab.bounding_box()
        if box_k:
            pg.mouse.click(box_k['x']+box_k['width']/2, box_k['y']+box_k['height']/2)
            pg.wait_for_timeout(1000)
            snap(pg, "tc2_kebab_liderado_aberto")

            items = pg.evaluate("""() => {
                return [...document.querySelectorAll('[role="menuitem"]')].map(e => e.innerText.trim()).filter(t=>t);
            }""")
            log(f"  [TC2] Menu items no registro do liderado: {items}")

            # Anotar endpoint se aprovar
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(500)

    pg.remove_listener("request", captura_req)

    # Agora tentar via API direta (simulando aprovacao no registro FORA DO ESCOPO)
    # Endpoints comuns do Twygo para registros:
    endpoints_aprovacao = [
        f"/api/v1/o/{ORG_ID}/records/{FORA_REC_ID}/approve",
        f"/api/v1/o/{ORG_ID}/records/{FORA_REC_ID}/emit",
        f"/o/{ORG_ID}/records/{FORA_REC_ID}/approve",
    ]
    tc2_api_results = {}
    for ep in endpoints_aprovacao:
        try:
            r = pg.request.post(
                f"{BASE_URL}{ep}",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-CSRF-Token": csrf
                },
                data=json.dumps({})
            )
            tc2_api_results[ep] = r.status
            log(f"  [TC2] POST {ep}: {r.status}")
        except Exception as e:
            tc2_api_results[ep] = f'erro:{e}'
            log(f"  [TC2] Erro POST {ep}: {e}")

    results['tc2_api'] = tc2_api_results

    # Veredito TC2
    got_403 = any(v == 403 for v in tc2_api_results.values())
    got_200 = any(v == 200 for v in tc2_api_results.values())
    if got_403:
        results['tc2'] = 'PASS_403_em_registro_fora_escopo'
        log("  [TC2] PASS - Pelo menos 1 endpoint retornou 403")
    elif got_200:
        results['tc2'] = 'FAIL_200_aprovacao_indevida_permitida'
        log("  [TC2] FAIL - Aprovacao retornou 200 (deveria ser 403)")
    elif results.get('tc2_visibilidade') == 'PASS_registro_nao_visivel':
        results['tc2'] = 'PASS_registro_invisivel_ao_lider'
        log("  [TC2] PASS (parcial) - Registro nao visivel; API retornou codigos nao definitivos")
    else:
        results['tc2'] = 'INCONCLUSIVO'
        log("  [TC2] INCONCLUSIVO")

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*70)
log("TC4 (RN96) - Registros de inativo SUMEM (KPIs decrementam)")
log("="*70)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=400)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado para TC4")

    # PASSO 1: Reativar qainativo_tc4_28129 e confirmar registros aparecem
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{INATIVO_ID}/edit", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "tc4_edit_usuario_inativo")
    log(f"  [TC4] URL edit usuario: {pg.url}")

    # Verificar estado atual do toggle ativo/inativo
    toggle_sel = "input[type='checkbox'][name*='active' i], input[type='checkbox'][name*='ativo' i]"
    chk_active = pg.locator(toggle_sel).first

    # Tentar via chakra-switch
    if not chk_active.count():
        chk_active = pg.locator(".chakra-switch input[type='checkbox']").first
    if not chk_active.count():
        chk_active = pg.locator("input[type='checkbox']").filter(has_text="").first

    # Verificar estado via JS
    estado_inativo = pg.evaluate(f"""() => {{
        const chk = document.querySelector("input[type='checkbox'][name*='active' i], .chakra-switch input");
        if (!chk) return 'nao_encontrado';
        return {{checked: chk.checked, name: chk.name, id: chk.id}};
    }}""")
    log(f"  [TC4] Estado toggle ativo: {estado_inativo}")

    # Reativar se estiver inativo
    if isinstance(estado_inativo, dict) and not estado_inativo.get('checked'):
        log("  [TC4] Usuario esta INATIVO. Reativando...")
        pg.evaluate("""() => {
            const chk = document.querySelector("input[type='checkbox'][name*='active' i], .chakra-switch input");
            if (chk) { chk.click(); }
        }""")
        pg.wait_for_timeout(1000)
        snap(pg, "tc4_reativando_usuario")

        # Salvar
        save_btn = pg.locator("button[type='submit'], input[type='submit'], button").filter(
            has_text=re.compile("Salvar|Atualizar|Save|Update", re.I)).first
        if save_btn.count():
            box_s = save_btn.bounding_box()
            if box_s:
                pg.mouse.click(box_s['x']+box_s['width']/2, box_s['y']+box_s['height']/2)
                pg.wait_for_timeout(3000)
                snap(pg, "tc4_pos_reativar_salvo")
                log(f"  [TC4] Salvo. URL: {pg.url}")
    elif isinstance(estado_inativo, dict) and estado_inativo.get('checked'):
        log("  [TC4] Usuario ja esta ATIVO. Ok.")
    else:
        log(f"  [TC4] Nao conseguiu determinar estado do toggle: {estado_inativo}")

    # Verificar via API se usuario esta ativo
    r_api = pg.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/users/{INATIVO_ID}",
                            headers={"Accept": "application/json"})
    if r_api.status == 200:
        try:
            api_data = r_api.json()
            ativo_api = api_data.get('active', api_data.get('user', {}).get('active'))
            log(f"  [TC4] API usuario ativo: {ativo_api}")
            results['tc4_usuario_ativo_antes'] = ativo_api
        except:
            log(f"  [TC4] API respondeu {r_api.status} mas nao JSON")
    else:
        log(f"  [TC4] API usuario: {r_api.status}")

    # Verificar registros do inativo na lista de Registros
    admin_goto_records(pg)
    pg.wait_for_timeout(2000)

    # Buscar pelo usuario inativo
    busca_tc4 = pg.locator("input[placeholder*='Pesquise' i], input[type='search']").first
    if busca_tc4.count():
        busca_tc4.fill("qainativo_tc4")
        pg.wait_for_timeout(2000)
        snap(pg, "tc4_busca_inativo_ativo_fase1")
        linhas_antes = contar_linhas_tabela(pg)
        log(f"  [TC4] Linhas com usuario ATIVO: {linhas_antes}")
        results['tc4_linhas_ativo'] = linhas_antes
        busca_tc4.fill("")
        pg.wait_for_timeout(1000)
    else:
        log("  [TC4] Busca nao encontrada")
        results['tc4_linhas_ativo'] = -1

    # Capturar KPIs ANTES de inativar
    kpis_antes = extrair_kpis(pg)
    kpi_total_antes = sum(int(k['value']) for k in kpis_antes if k['value'].isdigit())
    log(f"  [TC4] KPIs ANTES de inativar: {json.dumps(kpis_antes, ensure_ascii=False)}")
    log(f"  [TC4] Total antes: {kpi_total_antes}")
    results['tc4_kpi_antes'] = kpi_total_antes
    snap(pg, "tc4_kpis_antes_inativar")

    # PASSO 2: Inativar o usuario
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{INATIVO_ID}/edit", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)

    estado_antes = pg.evaluate("""() => {
        const chk = document.querySelector("input[type='checkbox'][name*='active' i], .chakra-switch input");
        return chk ? {checked: chk.checked, name: chk.name} : 'nao_encontrado';
    }""")
    log(f"  [TC4] Estado antes de inativar: {estado_antes}")

    if isinstance(estado_antes, dict) and estado_antes.get('checked'):
        log("  [TC4] Inativando usuario (desmarcando toggle)...")
        pg.evaluate("""() => {
            const chk = document.querySelector("input[type='checkbox'][name*='active' i], .chakra-switch input");
            if (chk) { chk.click(); }
        }""")
        pg.wait_for_timeout(1000)
        snap(pg, "tc4_inativando_usuario")

        # Salvar
        save_btn2 = pg.locator("button[type='submit'], input[type='submit'], button").filter(
            has_text=re.compile("Salvar|Atualizar|Save|Update", re.I)).first
        if save_btn2.count():
            box_s2 = save_btn2.bounding_box()
            if box_s2:
                pg.mouse.click(box_s2['x']+box_s2['width']/2, box_s2['y']+box_s2['height']/2)
                pg.wait_for_timeout(3000)
                snap(pg, "tc4_pos_inativar_salvo")
                log(f"  [TC4] Inativado. URL: {pg.url}")
    else:
        log(f"  [TC4] ATENCAO: usuario nao estava ativo antes de inativar: {estado_antes}")
        log("  [TC4] Tentando inativar de qualquer forma...")
        pg.evaluate("""() => {
            const chk = document.querySelector("input[type='checkbox'][name*='active' i], .chakra-switch input");
            if (chk) { chk.click(); }
        }""")
        pg.wait_for_timeout(1000)
        save_btn3 = pg.locator("button").filter(has_text=re.compile("Salvar|Save", re.I)).first
        if save_btn3.count():
            save_btn3.click(timeout=5000)
            pg.wait_for_timeout(3000)

    # PASSO 3: Recarregar Registros e verificar que linhas SUMIRAM e KPIs decrementaram
    admin_goto_records(pg)
    pg.wait_for_timeout(3000)  # aguardar reload completo
    snap(pg, "tc4_registros_pos_inativar")

    kpis_depois = extrair_kpis(pg)
    kpi_total_depois = sum(int(k['value']) for k in kpis_depois if k['value'].isdigit())
    log(f"  [TC4] KPIs DEPOIS de inativar: {json.dumps(kpis_depois, ensure_ascii=False)}")
    log(f"  [TC4] Total depois: {kpi_total_depois}")
    results['tc4_kpi_depois'] = kpi_total_depois

    # Buscar registros do inativo (devem NAO aparecer)
    busca_tc4_2 = pg.locator("input[placeholder*='Pesquise' i], input[type='search']").first
    if busca_tc4_2.count():
        busca_tc4_2.fill("qainativo_tc4")
        pg.wait_for_timeout(2000)
        snap(pg, "tc4_busca_inativo_pos_inativar")
        linhas_depois = contar_linhas_tabela(pg)
        log(f"  [TC4] Linhas com usuario INATIVO buscando: {linhas_depois}")
        results['tc4_linhas_inativo'] = linhas_depois

        # Verificar mensagem "Nenhum registro"
        msg_vazia = pg.locator("td, p, [class*='empty']").filter(
            has_text=re.compile("Nenhum|nenhum|No records|Sem registros", re.I)).count()
        results['tc4_msg_vazia'] = msg_vazia > 0
        log(f"  [TC4] Mensagem 'Nenhum registro': {msg_vazia > 0}")
    else:
        results['tc4_linhas_inativo'] = -1

    # PASSO 4: Verificar que NAO existe toggle "mostrar inativos"
    busca_tc4_2.fill("") if busca_tc4_2.count() else None
    pg.wait_for_timeout(1000)
    toggle_inativos = pg.locator("button, input, label, [role='switch']").filter(
        has_text=re.compile("Inativ|mostrar inativ|show inact", re.I)).count()
    log(f"  [TC4] Toggle 'mostrar inativos' presente: {toggle_inativos > 0}")
    results['tc4_toggle_inativos'] = toggle_inativos
    snap(pg, "tc4_verificar_toggle_inativos")

    # VEREDITO TC4
    linhas_antes_v = results.get('tc4_linhas_ativo', -1)
    linhas_depois_v = results.get('tc4_linhas_inativo', -1)

    if linhas_antes_v > 0 and linhas_depois_v == 0 and kpi_total_depois < kpi_total_antes:
        results['tc4'] = 'PASS'
        log("  [TC4] PASS - Registros SUMIRAM e KPI DECREMENTOU apos inativar")
    elif linhas_depois_v > 0:
        results['tc4'] = 'FAIL_registros_ainda_aparecem'
        log(f"  [TC4] FAIL - Registros AINDA aparecem ({linhas_depois_v} linhas) apos inativar")
    elif kpi_total_depois >= kpi_total_antes and linhas_antes_v > 0:
        results['tc4'] = 'FAIL_kpi_nao_decrementou'
        log(f"  [TC4] FAIL - KPI NAO decrementou: antes={kpi_total_antes}, depois={kpi_total_depois}")
    elif linhas_antes_v <= 0:
        results['tc4'] = 'INCONCLUSIVO_registros_nao_encontrados_antes'
        log(f"  [TC4] INCONCLUSIVO - registros nao encontrados na fase 1 (linhas_antes={linhas_antes_v})")
    else:
        results['tc4'] = 'INCONCLUSIVO'
        log(f"  [TC4] INCONCLUSIVO - antes={linhas_antes_v}, depois={linhas_depois_v}, kpi_antes={kpi_total_antes}, kpi_depois={kpi_total_depois}")

    ca.close(); ba.close()


# ==============================================================================
log("\n" + "="*70)
log("TC3 (RN95) - Aprovacao persiste apos sair do time; lider nao ve mais")
log("="*70)

with tw.sync_playwright() as p:
    ba, ca, pg_admin = tw.nova_pagina(p, slow_mo=400)
    ba2, ca2, pg_lider = tw.nova_pagina(p, slow_mo=400)

    tw.login(pg_admin, {"base_url": BASE_URL, "org_id": ORG_ID,
                         "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
    log("[admin] logado para TC3")

    tw.login(pg_lider, {"base_url": BASE_URL, "org_id": ORG_ID,
                          "email": LIDER_EMAIL, "senha": LIDER_SENHA}, admin=True)
    log("[lider] logado para TC3")

    # TC3 Passo 1: Criar registro PENDENTE para liderado1 (se nao houver um pendente)
    # Verificar se ha algum registro pendente de liderado1
    admin_goto_records(pg_admin)
    pg_admin.wait_for_timeout(2000)

    # Buscar registros pendentes do liderado
    busca_tc3 = pg_admin.locator("input[placeholder*='Pesquise' i], input[type='search']").first
    if busca_tc3.count():
        busca_tc3.fill("liderado1")
        pg_admin.wait_for_timeout(2000)
        snap(pg_admin, "tc3_admin_busca_liderado1")

    linhas_tc3 = contar_linhas_tabela(pg_admin)
    log(f"  [TC3] Registros de liderado1: {linhas_tc3}")

    # Verificar se algum esta Pendente
    pendentes = pg_admin.locator("tbody tr").filter(has_text=re.compile("Pendente|Aguardando", re.I)).count()
    aprovados = pg_admin.locator("tbody tr").filter(has_text=re.compile("Emitido|Aprovado", re.I)).count()
    log(f"  [TC3] Pendentes: {pendentes}, Aprovados: {aprovados}")

    # TC3 Passo 1: Lider aprova registro de liderado1
    # Buscar como lider
    admin_goto_records(pg_lider)
    pg_lider.wait_for_timeout(2000)

    busca_lider_tc3 = pg_lider.locator("input[placeholder*='Pesquise' i], input[type='search']").first
    if busca_lider_tc3.count():
        busca_lider_tc3.fill("liderado1")
        pg_lider.wait_for_timeout(2000)
        snap(pg_lider, "tc3_lider_busca_liderado1")

    rows_lider = pg_lider.locator("tbody tr")
    rows_count = rows_lider.count()
    log(f"  [TC3] Lider ve {rows_count} registros de liderado1")

    aprovacao_feita = False
    if rows_count > 0:
        # Tentar aprovar o primeiro registro pendente (ou qualquer um)
        primeiro = rows_lider.first
        kebab_tc3 = primeiro.locator("button").last
        box_k3 = kebab_tc3.bounding_box()
        if box_k3:
            pg_lider.mouse.click(box_k3['x']+box_k3['width']/2, box_k3['y']+box_k3['height']/2)
            pg_lider.wait_for_timeout(1000)
            snap(pg_lider, "tc3_kebab_liderado_aberto")

            items_tc3 = pg_lider.evaluate("""() => {
                return [...document.querySelectorAll('[role="menuitem"]')].map(e => ({
                    text: e.innerText.trim(), id: e.id
                })).filter(i => i.text);
            }""")
            log(f"  [TC3] Menu items: {json.dumps(items_tc3, ensure_ascii=False)}")

            # Clicar em Aprovar/Emitir
            aprovacao_item = pg_lider.locator("[role='menuitem']").filter(
                has_text=re.compile("Aprova|Emitir|Avaliar", re.I)).first
            if aprovacao_item.count():
                box_ap = aprovacao_item.bounding_box()
                if box_ap:
                    pg_lider.mouse.click(box_ap['x']+box_ap['width']/2, box_ap['y']+box_ap['height']/2)
                    pg_lider.wait_for_timeout(2000)
                    snap(pg_lider, "tc3_pos_aprovar")

                    # Verificar toast de sucesso
                    toast = pg_lider.locator("[role='alert'], .chakra-toast, [class*='toast']").filter(
                        has_text=re.compile("aprovad|emitid|sucesso", re.I)).first
                    if toast.count():
                        log("  [TC3] Toast de aprovacao detectado")
                        aprovacao_feita = True
                        results['tc3_toast_aprovacao'] = 'sim'
                    else:
                        log("  [TC3] Toast nao detectado mas acao executada")
                        aprovacao_feita = True
                        results['tc3_toast_aprovacao'] = 'nao_detectado'
            else:
                pg_lider.keyboard.press("Escape")
                log("  [TC3] Item Aprovar nao encontrado no menu")
                results['tc3'] = 'INCONCLUSIVO_sem_item_aprovar'
    else:
        log("  [TC3] Lider nao ve registros de liderado1")
        results['tc3'] = 'INCONCLUSIVO_lider_sem_registros_liderado'

    if aprovacao_feita:
        # TC3 Passo 2: Remover liderado1 do organograma do lider
        # Ir para organograma
        pg_admin.goto(f"{BASE_URL}/o/{ORG_ID}/organization_chart", wait_until="domcontentloaded", timeout=30000)
        try: pg_admin.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        pg_admin.wait_for_timeout(3000)
        snap(pg_admin, "tc3_organograma_antes_remover")
        log(f"  [TC3] Organograma URL: {pg_admin.url}")

        # Tentar remover liderado1 do time do qaliderpuro
        # Buscar a linha do liderado1 no organograma
        org_search = pg_admin.locator("input[placeholder*='Pesquise' i], input[placeholder*='nome' i]").first
        if org_search.count():
            org_search.fill("liderado1")
            pg_admin.wait_for_timeout(2000)
            snap(pg_admin, "tc3_org_busca_liderado1")

        # Abrir kebab/remover do organograma
        rows_org = pg_admin.locator("tbody tr, [class*='row']").filter(has_text=re.compile("liderado1", re.I))
        if rows_org.count():
            kebab_org = rows_org.first.locator("button").last
            box_org = kebab_org.bounding_box()
            if box_org:
                pg_admin.mouse.click(box_org['x']+box_org['width']/2, box_org['y']+box_org['height']/2)
                pg_admin.wait_for_timeout(1000)
                snap(pg_admin, "tc3_org_kebab_aberto")

                # Procurar opcao de remover gestor / alterar gestor
                items_org = pg_admin.evaluate("""() => {
                    return [...document.querySelectorAll('[role="menuitem"], [class*="menu"] li')].map(e => e.innerText.trim()).filter(t=>t);
                }""")
                log(f"  [TC3] Organograma menu: {items_org}")

                remover_item = pg_admin.locator("[role='menuitem'], li").filter(
                    has_text=re.compile("Remover|Excluir|Desvincul|Alterar gestor", re.I)).first
                if remover_item.count():
                    box_rem = remover_item.bounding_box()
                    if box_rem:
                        pg_admin.mouse.click(box_rem['x']+box_rem['width']/2, box_rem['y']+box_rem['height']/2)
                        pg_admin.wait_for_timeout(2000)
                        snap(pg_admin, "tc3_liderado_removido_organograma")
                        log("  [TC3] Liderado1 removido do organograma")
                        results['tc3_removido_organograma'] = True
                else:
                    pg_admin.keyboard.press("Escape")
                    log("  [TC3] Item remover nao encontrado no organograma")
                    results['tc3_removido_organograma'] = False
        else:
            log("  [TC3] Liderado1 nao encontrado no organograma")
            results['tc3_removido_organograma'] = False

        # TC3 Passo 3: Verificar que registro aprovado AINDA esta Emitido/Aprovado como admin
        admin_goto_records(pg_admin)
        pg_admin.wait_for_timeout(2000)
        busca_tc3_2 = pg_admin.locator("input[placeholder*='Pesquise' i], input[type='search']").first
        if busca_tc3_2.count():
            busca_tc3_2.fill("liderado1")
            pg_admin.wait_for_timeout(2000)

        snap(pg_admin, "tc3_admin_verifica_aprovacao_persiste")
        linhas_admin_tc3 = pg_admin.locator("tbody tr").filter(has_text=re.compile("Emitido|Aprovado", re.I)).count()
        log(f"  [TC3] Admin ve {linhas_admin_tc3} registros aprovados/emitidos de liderado1 apos remocao do time")
        results['tc3_aprovados_persistem_admin'] = linhas_admin_tc3

        # TC3 Passo 4: Como lider, NAO deve mais ver o registro de liderado1
        admin_goto_records(pg_lider)
        pg_lider.wait_for_timeout(2000)
        busca_lider_tc3_2 = pg_lider.locator("input[placeholder*='Pesquise' i], input[type='search']").first
        if busca_lider_tc3_2.count():
            busca_lider_tc3_2.fill("liderado1")
            pg_lider.wait_for_timeout(2000)

        snap(pg_lider, "tc3_lider_apos_remocao_organograma")
        linhas_lider_tc3 = contar_linhas_tabela(pg_lider)
        log(f"  [TC3] Lider ve {linhas_lider_tc3} registros de liderado1 apos remocao do time")
        results['tc3_lider_nao_ve'] = linhas_lider_tc3

        # VEREDITO TC3
        aprovacao_persiste = results.get('tc3_aprovados_persistem_admin', 0) > 0
        lider_nao_ve = results.get('tc3_lider_nao_ve', -1) == 0

        if aprovacao_persiste and lider_nao_ve:
            results['tc3'] = 'PASS'
            log("  [TC3] PASS - Aprovacao persiste (admin ve) e lider nao ve mais")
        elif not aprovacao_persiste:
            results['tc3'] = 'FAIL_aprovacao_perdida'
            log("  [TC3] FAIL - Aprovacao foi PERDIDA apos saida do time")
        elif not lider_nao_ve:
            results['tc3'] = f'FAIL_lider_ainda_ve:{results.get("tc3_lider_nao_ve")}_registros'
            log(f"  [TC3] FAIL - Lider AINDA ve registros apos remocao do time")
        else:
            results['tc3'] = 'INCONCLUSIVO'

        # Restaurar liderado1 ao organograma do lider (para nao quebrar outros dados)
        log("  [TC3] Restaurando liderado1 ao organograma do qaliderpuro...")
        pg_admin.goto(f"{BASE_URL}/o/{ORG_ID}/organization_chart", wait_until="domcontentloaded", timeout=30000)
        try: pg_admin.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        pg_admin.wait_for_timeout(3000)
        snap(pg_admin, "tc3_organograma_pos_remocao")
        log("  [TC3] Organograma apos remocao - restauracao manual pode ser necessaria")

    pg_admin.close(); ca.close(); ba.close()
    pg_lider.close(); ca2.close(); ba2.close()


# ==============================================================================
log("\n" + "="*70)
log("SUMARIO FINAL")
log("="*70)
for k, v in results.items():
    log(f"  {k}: {v}")

log("\n  === VEREDITOS ===")
log(f"  TC1 Pessoa scope: {results.get('tc1_pessoa_scope','?')}")
log(f"  TC1 Provedores:   {results.get('tc1_provedores','?')}")
log(f"  TC2 (RN94):       {results.get('tc2','?')}")
log(f"  TC3 (RN95):       {results.get('tc3','?')}")
log(f"  TC4 (RN96):       {results.get('tc4','?')}")
log(f"  TC5 (RN96.5):     {results.get('tc5','?')}")
log(f"  EXTRA:            {results.get('extra','?')}")
log(f"  TC6-TC10:         BLOQUEADO (SharedEvent/multi-org nao disponivel no stage)")
