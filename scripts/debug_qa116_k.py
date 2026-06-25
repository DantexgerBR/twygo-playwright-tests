# -*- coding: utf-8 -*-
"""Debug K — criar registro corretamente usando o chakra-input de Pessoas."""
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

LIDER_PURO_ID  = 4299626
LIDERADO_ID    = 4298605
FORA_ID        = 4298501

log = lambda *a: print(*a, flush=True)
def snap(pg, nome): pg.screenshot(path=str(PASTA/f"{nome}.png"), full_page=True); log(f"  [snap] {nome}.png")

def dispensar(pg):
    tw.dispensar_nps(pg)
    try: pg.evaluate("()=>{document.querySelectorAll('#hubspot-messages-iframe-container,[id*=sophia]').forEach(e=>e.style.display='none')}")
    except: pass

def criar_registro_ui_final(pg, pessoa_email, conteudo):
    """Criar registro externo pela UI com seletores corretos."""
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # Campo Pessoas — é um chakra-input css-1k4krg8 VISÍVEL
    # Clicar nele vai abrir um modal/drawer de seleção
    pessoas_inp = pg.locator("input.chakra-input.css-1k4krg8, input[class*='css-1k4krg8']").first
    if pessoas_inp.count() == 0:
        # Fallback: procurar o input visível na área de Pessoas
        # Baseado no DOM: é o INPUT dentro do .chakra-input__group
        pessoas_inp = pg.locator(".chakra-input__group input").first
    if pessoas_inp.count() == 0:
        # Último fallback
        pessoas_inp = pg.locator("input:not([type='hidden']):not([type='date'])").first

    log(f"  [pessoas] locator count: {pessoas_inp.count()}")
    if pessoas_inp.count():
        pessoas_inp.click(force=True, timeout=5000)
        pg.wait_for_timeout(2000)
    else:
        log("  [pessoas] NENHUM INPUT ENCONTRADO")
        return None

    snap(pg, f"k_apos_click_pessoas_{conteudo[:8]}")
    modal = pg.locator("[role='dialog']").filter(visible=True).first
    log(f"  Modal aberto: {modal.count() > 0}")

    if modal.count():
        snap(pg, f"k_modal_{conteudo[:8]}")
        modal_text = modal.inner_text()
        log(f"  Modal text: {modal_text[:300]}")

        # Buscar pelo email
        search = modal.locator("input").filter(visible=True).first
        if search.count():
            search.fill(pessoa_email)
            pg.wait_for_timeout(1500)

        snap(pg, f"k_modal_buscado_{conteudo[:8]}")

        # Clicar no item encontrado — estrutura baseada no screenshot do debug C
        # No screenshot: cada usuário aparece com avatar + nome + email
        # Há um "Selecionar tudo" e um botão "Cancelar" + "Associar"
        user_row = modal.locator(f"text={pessoa_email}").first
        if user_row.count() == 0:
            # Tentar pelo nome parcial
            nome_parte = pessoa_email.split("@")[0].replace("1","").replace("2","")
            user_row = modal.locator(f"text={nome_parte}").first
        if user_row.count():
            user_row.scroll_into_view_if_needed()
            pg.wait_for_timeout(300)
            # JS: encontrar e clicar no checkbox deste item
            clicou = pg.evaluate(f"""() => {{
                const allText = [...document.querySelectorAll('[role="dialog"] *')];
                const el = allText.find(e => e.innerText && e.innerText.includes('{pessoa_email.split("@")[0]}'));
                if (el) {{
                    // Ir subindo até encontrar um checkbox ou input
                    let node = el;
                    for (let i=0; i<8; i++) {{
                        if (!node) break;
                        const chk = node.querySelector('input[type="checkbox"], .chakra-checkbox__control');
                        if (chk) {{ chk.click(); return 'clicked ' + chk.tagName + ' via ancestor'; }}
                        node = node.parentElement;
                    }}
                    el.click();
                    return 'clicked el: ' + el.tagName + ' ' + el.className.slice(0,30);
                }}
                return 'not found';
            }}""")
            log(f"  [modal] clicou item: {clicou}")
            pg.wait_for_timeout(500)
            snap(pg, f"k_modal_selecionado_{conteudo[:8]}")
        else:
            log(f"  [modal] usuário não encontrado, clicando no primeiro resultado")
            # Clicar no primeiro item
            primeiro = modal.locator("[role='row'], .chakra-checkbox, [class*='person-item']").first
            if primeiro.count():
                primeiro.click(force=True)
                pg.wait_for_timeout(500)

        # Botões do modal
        btns = [b.strip() for b in modal.locator("button").all_text_contents() if b.strip()]
        log(f"  Botões modal: {btns}")
        btn_assoc = modal.locator("button").filter(has_text=re.compile(r"Associar|Adicionar|Vincular|Confirmar", re.I)).first
        if btn_assoc.count():
            btn_assoc.click()
            pg.wait_for_timeout(2000)
            log("  [modal] clicou Associar")
        elif len(btns) >= 2:
            # Clicar no botão que não é Cancelar
            for btn in modal.locator("button").all():
                txt = btn.inner_text().strip()
                if txt and "cancelar" not in txt.lower() and "fechar" not in txt.lower() and "×" not in txt:
                    btn.click(); pg.wait_for_timeout(2000)
                    log(f"  [modal] clicou '{txt}'")
                    break
    else:
        log("  [pessoas] modal não abriu — criando sem vincular pessoa")

    snap(pg, f"k_form_apos_pessoas_{conteudo[:8]}")

    # Conteúdo (react-select)
    for sel in ["#content input", "[placeholder*='onteúdo']", "[placeholder*='onteudo']"]:
        cont = pg.locator(sel).first
        if cont.count():
            cont.click(force=True)
            pg.keyboard.type(conteudo, delay=30)
            pg.wait_for_timeout(800)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            else: pg.keyboard.press("Enter")
            pg.wait_for_timeout(300)
            log(f"  [conteudo] OK")
            break

    # Provedor
    for sel in ["#provider input"]:
        prov = pg.locator(sel).first
        if prov.count():
            prov.click(force=True)
            pg.keyboard.type("Alura", delay=30)
            pg.wait_for_timeout(800)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            log("  [provedor] OK"); break

    # Tipo de experiência
    for sel in ["#learningExperience input"]:
        tipo = pg.locator(sel).first
        if tipo.count():
            tipo.click(force=True)
            pg.keyboard.type("Curso", delay=30)
            pg.wait_for_timeout(800)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            log("  [tipo] OK"); break

    # Categorias
    for sel in ["#categories input"]:
        cat = pg.locator(sel).first
        if cat.count():
            cat.click(force=True)
            pg.wait_for_timeout(500)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            pg.keyboard.press("Escape")
            log("  [cat] OK"); break

    # Carga horária
    pg.locator("input[placeholder='HH:MM:SS']").first.fill("01:00:00", timeout=3000) if pg.locator("input[placeholder='HH:MM:SS']").count() else None
    # Data de término
    pg.locator("input[type='date']").first.fill("2026-06-01", timeout=3000) if pg.locator("input[type='date']").count() else None

    snap(pg, f"k_preenchido_{conteudo[:8]}")

    # Salvar
    pg.evaluate("() => { const btn = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Salvar'); if(btn) btn.click(); }")
    pg.wait_for_timeout(5000)
    snap(pg, f"k_salvo_{conteudo[:8]}")

    url_d = pg.url
    criou = "records/new" not in url_d
    rec_id = None
    if criou:
        m = re.search(r"/records/(\d+)", url_d)
        if m: rec_id = int(m.group(1))
        else:
            r = pg.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=5&page=1&order_by=created_at&order_type=desc", headers={"Accept":"application/json"})
            if r.status == 200:
                recs = r.json().get("data",{}).get("records",[])
                found = next((x for x in recs if conteudo in str(x.get("content",""))), None)
                if found: rec_id = found.get("id")
    log(f"  → rec_id={rec_id} url={url_d}")
    return rec_id

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    log("\n--- Criar registro para liderado1 ---")
    rec_lid = criar_registro_ui_final(pg, "liderado1@teste.com", "QA116-Liderado-Externo")
    log(f"  rec_liderado_id={rec_lid}")

    log("\n--- Criar registro para devtestes ---")
    rec_fora = criar_registro_ui_final(pg, "devtestes@teste.com", "QA116-ForaEquipe-Externo")
    log(f"  rec_fora_id={rec_fora}")

    log(f"\nResultado: rec_lid={rec_lid} rec_fora={rec_fora}")
    ca.close(); ba.close()
