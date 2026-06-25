# -*- coding: utf-8 -*-
"""Debug D — criar registros via UI com fluxo correto do modal Vincular pessoas."""
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

# IDs já conhecidos
LIDERADO_ID = 4298605
LIDER_PURO_ID = 4299626
FORA_ID = 4298501

def dispensar(pg):
    tw.dispensar_nps(pg)
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

def fechar_modal_se_aberto(pg):
    """Fecha qualquer modal aberto via X ou Escape."""
    modal = pg.locator("[role='dialog'], [role='alertdialog']").filter(visible=True).first
    if modal.count():
        try:
            close_btn = modal.locator("button[aria-label*='close'], button[aria-label*='fechar'], button:has-text('×'), button:has-text('✕')").first
            if close_btn.count():
                close_btn.click()
                pg.wait_for_timeout(800)
                return True
        except: pass
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(800)
        return True
    return False

def criar_registro_ui(pg, pessoa_email, conteudo):
    """Cria registro externo via form da UI como admin, com fluxo correto do modal."""
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    log(f"  [form] url={pg.url}")

    # 1. Campo "Pessoas" — clicar no input para abrir modal
    pessoas_inp = pg.locator("input[placeholder*='Adicionar pessoas']").first
    if pessoas_inp.count() == 0:
        pessoas_inp = pg.locator("[placeholder*='pessoas']").first
    if pessoas_inp.count():
        pessoas_inp.click(timeout=4000)
        pg.wait_for_timeout(2000)
        snap(pg, f"d_modal_pessoas_{conteudo[:10]}")
    else:
        # Tentar clicar no ícone de pessoa
        icon_btn = pg.locator("button[aria-label*='pes'], [data-test-id*='people']").first
        if icon_btn.count():
            icon_btn.click(timeout=4000)
            pg.wait_for_timeout(2000)

    # 2. No modal "Vincular pessoas" — digitar email e selecionar
    modal = pg.locator("[role='dialog']").filter(visible=True).first
    if modal.count():
        log("  [modal] Vincular pessoas aberto")
        # Campo "Pesquise por seu email"
        search = modal.locator("input[placeholder*='email'], input[placeholder*='Pesquise']").first
        if search.count():
            search.fill(pessoa_email)
            pg.wait_for_timeout(1500)
            snap(pg, f"d_modal_pesquisa_{conteudo[:10]}")

        # Selecionar o usuário na lista
        # O email deve estar visível como card/item
        opcao = modal.locator(f"text={pessoa_email}").first
        if opcao.count() == 0:
            # Tentar pelo nome ou pelo email parcial
            nome_parte = pessoa_email.split("@")[0]
            opcao = modal.locator(f"text={nome_parte}").first
        if opcao.count():
            # Clicar no checkbox ou no card inteiro
            checkbox = opcao.locator("xpath=ancestor::div[contains(@class,'card') or @role='option']//input[@type='checkbox']").first
            if checkbox.count():
                checkbox.click()
            else:
                opcao.click()
            pg.wait_for_timeout(800)
            snap(pg, f"d_modal_selecionado_{conteudo[:10]}")
        else:
            log(f"  [modal] email {pessoa_email} não encontrado. Tentando clicar no primeiro resultado")
            # Clicar no primeiro item da lista
            primeiro = modal.locator("[role='option'], .chakra-checkbox, input[type='checkbox']").first
            if primeiro.count():
                primeiro.click()
                pg.wait_for_timeout(500)

        # Clicar botão "Associar" ou "Vincular"
        btn_assoc = modal.locator("button").filter(has_text=re.compile(r"Associar|Vincular|Salvar", re.I)).first
        if btn_assoc.count():
            btn_assoc.click()
            pg.wait_for_timeout(2000)
            log("  [modal] clicou Associar")
        else:
            # Fechar modal pelo botão X
            fechar_modal_se_aberto(pg)
    else:
        log("  [modal] não abriu — tentando continuar")

    # Garantir que o modal fechou
    pg.wait_for_timeout(1000)
    if pg.locator("[role='dialog']").filter(visible=True).count():
        fechar_modal_se_aberto(pg)
    pg.wait_for_timeout(500)

    snap(pg, f"d_form_apos_pessoas_{conteudo[:10]}")

    # 3. Conteúdo
    # O campo Conteúdo é um react-select (creatable) — não um input simples
    cont_container = pg.locator("#content").first
    if cont_container.count() == 0:
        cont_container = pg.locator("[id*='content']").first
    if cont_container.count() == 0:
        # Buscar pelo placeholder "Digite o nome do conteúdo"
        cont_container = pg.locator("[placeholder*='onteúdo'], [placeholder*='onteudo']").first

    if cont_container.count():
        cont_container.click(timeout=4000)
        pg.wait_for_timeout(500)
        pg.keyboard.type(conteudo, delay=30)
        pg.wait_for_timeout(800)
        # Pode precisar selecionar opção de "criar novo"
        criar_opt = pg.locator("[role='option']").first
        if criar_opt.count():
            criar_opt.click()
        else:
            # Se não há opção, pressionar Enter para criar inline
            pg.keyboard.press("Enter")
        pg.wait_for_timeout(500)
        log(f"  [conteudo] {conteudo}")
    else:
        log("  [conteudo] campo não encontrado")

    # 4. Provedor — react-select creatable
    prov_container = pg.locator("#provider").first
    if prov_container.count() == 0:
        prov_container = pg.locator("[id*='provider']").first
    if prov_container.count():
        prov_container.click(timeout=4000)
        pg.wait_for_timeout(800)
        opcoes = pg.locator("[role='option']").all()
        if opcoes:
            opcoes[0].click()
            pg.wait_for_timeout(500)
            log("  [provedor] selecionado")
        else:
            pg.keyboard.type("Alura", delay=30)
            pg.wait_for_timeout(500)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            pg.wait_for_timeout(500)

    # 5. Tipo de experiência
    tipo_container = pg.locator("#learningExperience").first
    if tipo_container.count():
        tipo_container.click(timeout=4000)
        pg.wait_for_timeout(800)
        opcoes = pg.locator("[role='option']").all()
        if opcoes:
            opcoes[0].click()
            pg.wait_for_timeout(500)
            log("  [tipo] selecionado")

    # 6. Categorias
    cat_container = pg.locator("#categories").first
    if cat_container.count():
        cat_container.click(timeout=4000)
        pg.wait_for_timeout(800)
        opcoes = pg.locator("[role='option']").all()
        if opcoes:
            opcoes[0].click()
            pg.wait_for_timeout(500)
            pg.keyboard.press("Escape")
            log("  [categorias] selecionado")

    # 7. Carga horária
    carga_inp = pg.locator("input[placeholder='HH:MM:SS']").first
    if carga_inp.count():
        carga_inp.fill("01:00:00")
        log("  [carga] preenchida")

    # 8. Data de término (obrigatório)
    data_inp = pg.locator("input[type='date']").first
    if data_inp.count():
        data_inp.fill("2026-06-01")
        log("  [data] preenchida")

    snap(pg, f"d_form_preenchido_{conteudo[:10]}")

    # 9. Salvar usando JS click para evitar bloqueio de overlay
    btn_salvar = pg.locator("button").filter(has_text=re.compile(r"^Salvar$", re.I)).first
    if btn_salvar.count():
        btn_salvar.evaluate("el => el.click()")
        pg.wait_for_timeout(5000)
        log(f"  [salvar] url={pg.url}")
    else:
        log("  [salvar] botão não encontrado!")

    snap(pg, f"d_pos_salvar_{conteudo[:10]}")

    # 10. Capturar ID
    url_depois = pg.url
    criou = "records/new" not in url_depois
    rec_id = None
    if criou:
        m = re.search(r"/records/(\d+)", url_depois)
        if m:
            rec_id = int(m.group(1))
        else:
            # Buscar na API pelo conteúdo
            resp = pg.request.get(
                f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=25&page=1&order_by=created_at&order_type=desc",
                headers={"Accept":"application/json"},
            )
            if resp.status == 200:
                recs = resp.json().get("data",{}).get("records",[])
                match = next((r for r in recs if conteudo in str(r.get("content",""))), None)
                if match:
                    rec_id = match.get("id")

    log(f"  [criar_registro] criou={criou} rec_id={rec_id}")
    return rec_id

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # Definir senha do líder puro primeiro
    log("\n--- Corrigir senha qaliderpuro ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDER_PURO_ID}/edit", wait_until="domcontentloaded", timeout=15000)
    dispensar(pg)
    pg.wait_for_timeout(2000)
    snap(pg, "d_lider_edit")
    body_edit = pg.locator("body").inner_text()
    log(f"  body[:100]: {body_edit[:100]}")

    pwd = pg.locator("input[name='professional[password]']").first
    log(f"  campo senha encontrado: {pwd.count() > 0}")
    if pwd.count():
        pwd.fill("123456")
        conf = pg.locator("input[name='professional[password_confirmation]']").first
        if conf.count(): conf.fill("123456")
        pg.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=5000)
        pg.wait_for_timeout(2500)
        snap(pg, "d_lider_senha_salva")
        log(f"  url apos salvar: {pg.url}")

    # Criar registro para liderado1
    log("\n--- Criar registro para liderado1 ---")
    rec_lid = criar_registro_ui(pg, "liderado1@teste.com", "QA116-Liderado-Externo")
    log(f"  rec_liderado_id = {rec_lid}")

    # Criar registro para devtestes (fora da equipe)
    log("\n--- Criar registro para devtestes ---")
    rec_fora = criar_registro_ui(pg, "devtestes@teste.com", "QA116-ForaEquipe-Externo")
    log(f"  rec_fora_id = {rec_fora}")

    # Salvar resultado
    resultado = {
        "lider_puro_id": LIDER_PURO_ID,
        "liderado_id": LIDERADO_ID,
        "fora_id": FORA_ID,
        "rec_liderado_id": rec_lid,
        "rec_fora_id": rec_fora,
    }
    (PASTA/"debug_d_resultado.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"\nResultado: {resultado}")

    ca.close(); ba.close()
