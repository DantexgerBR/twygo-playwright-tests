# -*- coding: utf-8 -*-
"""Debug R — correções finais: Conteúdo e Data de término."""
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

def abrir_drawer_pessoas(pg):
    pg.evaluate("""() => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim() === 'Adicionar pessoas') {
                let c = node.parentElement;
                for (let i=0; i<8; i++) {
                    if (!c) break;
                    if ((c.className||'').includes('css-zd45vb')) { c.click(); return; }
                    c = c.parentElement;
                }
                node.parentElement?.parentElement?.click();
            }
        }
    }""")
    pg.wait_for_timeout(2000)

def selecionar_usuario_drawer_e_vincular(pg, pessoa_email):
    """Seleciona usuário no drawer correto e clica Vincular."""
    drawer = pg.locator("div.chakra-modal__content:has(header:has-text('Vincular pessoas'))").first
    if not drawer.count():
        log("  [drawer] não aberto!")
        return False

    # Campo de busca — INPUT.chakra-input.css-653wwz dentro do drawer
    buscar_inp = drawer.locator("input.css-653wwz, input[type='text']").first
    if buscar_inp.count() == 0:
        buscar_inp = drawer.locator("input").filter(visible=True).first
    if buscar_inp.count():
        buscar_inp.fill(pessoa_email)
        pg.wait_for_timeout(1500)
        log(f"  [busca] digitou {pessoa_email}")

    snap(pg, f"r_drawer_busca_{pessoa_email.split('@')[0][:8]}")

    # Clicar no card do usuário (div.css-1d07itj é o card, div.css-15z1zis é o container)
    clicou = pg.evaluate(f"""() => {{
        const drawer = document.querySelector('div.chakra-modal__content');
        if (!drawer) return 'no drawer';
        const walker = document.createTreeWalker(drawer, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {{
            if (node.textContent.includes('{pessoa_email}') || node.textContent.includes('{pessoa_email.split('@')[0]}')) {{
                let el = node.parentElement;
                for (let i=0; i<8; i++) {{
                    if (!el || el === drawer) break;
                    const r = el.getBoundingClientRect();
                    if (r.height >= 50 && r.width > 150) {{
                        el.click();
                        return 'clicked ' + el.tagName + ' ' + el.className.slice(0,30);
                    }}
                    el = el.parentElement;
                }}
            }}
        }}
        return 'not found';
    }}""")
    log(f"  [selecionar] {clicou}")
    pg.wait_for_timeout(800)

    vincular = pg.locator("[data-test-id='resource-selector-drawer-confirm-button']").first
    if vincular.count():
        habilitado = vincular.evaluate("el => !el.disabled")
        if habilitado:
            vincular.click(force=True)
            pg.wait_for_timeout(2000)
            log("  [vincular] OK!")
            return True
    log("  [vincular] FALHOU (desabilitado ou não encontrado)")
    return False

def criar_registro_v4(pg, pessoa_email, conteudo, label_slug):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # 1. Pessoas
    abrir_drawer_pessoas(pg)
    drawer_ok = pg.locator("div.chakra-modal__content:has(header:has-text('Vincular pessoas'))").count() > 0
    log(f"  [drawer] aberto={drawer_ok}")
    if drawer_ok:
        ok = selecionar_usuario_drawer_e_vincular(pg, pessoa_email)
        log(f"  [vincular] ok={ok}")

    snap(pg, f"r_form_pessoas_{label_slug}")

    # 2. Conteúdo — react-select creatable
    # O campo é um creatable react-select com id "content"
    # Precisamos: clicar no input, digitar, esperar "Criar..." e clicar
    cont_input = pg.locator("#content input").first
    if cont_input.count():
        cont_input.click(force=True)
        pg.wait_for_timeout(300)
        # Limpar e digitar
        cont_input.fill(conteudo)  # fill limpa e digita
        pg.wait_for_timeout(1000)
        # Verificar opções disponíveis
        opcoes = pg.locator("[class*='option'], [role='option']").all_text_contents()
        log(f"  [conteudo] opções: {opcoes[:5]}")
        # Selecionar a primeira opção (pode ser "Criar...")
        opt = pg.locator("[class*='option'], [role='option']").first
        if opt.count():
            opt.click(force=True)
            pg.wait_for_timeout(400)
            log(f"  [conteudo] selecionou opção")
        else:
            # Enter para criar inline
            pg.keyboard.press("Enter")
            pg.wait_for_timeout(400)
            log(f"  [conteudo] criou via Enter")
    else:
        log("  [conteudo] input não encontrado!")

    # 3. Provedor
    prov_input = pg.locator("#provider input").first
    if prov_input.count():
        prov_input.click(force=True); prov_input.fill("Alura"); pg.wait_for_timeout(700)
        opt = pg.locator("[role='option']").first
        if opt.count(): opt.click(force=True)
        log("  [provedor] OK")

    # 4. Tipo experiência
    tipo_input = pg.locator("#learningExperience input").first
    if tipo_input.count():
        tipo_input.click(force=True); tipo_input.fill("Curso"); pg.wait_for_timeout(700)
        opt = pg.locator("[role='option']").first
        if opt.count(): opt.click(force=True)
        log("  [tipo] OK")

    # 5. Categorias
    cat_input = pg.locator("#categories input").first
    if cat_input.count():
        cat_input.click(force=True); pg.wait_for_timeout(500)
        opt = pg.locator("[role='option']").first
        if opt.count(): opt.click(force=True)
        pg.keyboard.press("Escape")
        log("  [cat] OK")

    # 6. Carga horária — input com placeholder HH:MM:SS
    carga = pg.locator("input[placeholder='HH:MM:SS']").first
    if carga.count():
        carga.click()
        carga.fill("")  # limpar
        pg.keyboard.type("010000", delay=50)  # digitar 01:00:00 sem separadores
        pg.wait_for_timeout(300)
        log("  [carga] OK")

    # 7. Data de término — é o SEGUNDO input[type='date']
    # Baseado no screenshot: Data de início (1º) e Data de término (2º)
    datas = pg.locator("input[type='date']").all()
    log(f"  [datas] {len(datas)} inputs encontrados")
    # Data de término é o segundo (índice 1)
    if len(datas) >= 2:
        datas[1].fill("2026-06-01")
        log("  [data termino] OK (2º input)")
    elif len(datas) == 1:
        datas[0].fill("2026-06-01")
        log("  [data termino] OK (1º input)")

    snap(pg, f"r_form_preenchido_{label_slug}")

    # 8. Salvar
    pg.evaluate("() => { const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='Salvar'); if(b) b.click(); }")
    pg.wait_for_timeout(6000)
    snap(pg, f"r_salvo_{label_slug}")

    url_d = pg.url; criou = "records/new" not in url_d; rec_id = None
    if criou:
        m = re.search(r"/records/(\d+)", url_d)
        if m: rec_id = int(m.group(1))
        else:
            r = pg.request.get(f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=5&page=1&order_by=created_at&order_type=desc", headers={"Accept":"application/json"})
            if r.status == 200:
                recs = r.json().get("data",{}).get("records",[])
                found = next((x for x in recs if conteudo in str(x.get("content",""))), None)
                if found: rec_id = found.get("id")
    log(f"  → criou={criou} rec_id={rec_id} url={url_d}")
    return rec_id

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    log("\n--- Criar registro para liderado1 ---")
    rec_lid = criar_registro_v4(pg, "liderado1@teste.com", "QA116-Liderado-Externo", "liderado")
    log(f"  rec_lid={rec_lid}")

    log("\n--- Criar registro para devtestes ---")
    rec_fora = criar_registro_v4(pg, "devtestes@teste.com", "QA116-ForaEquipe-Externo", "fora")
    log(f"  rec_fora={rec_fora}")

    log(f"\nRESULTADO FINAL: rec_lid={rec_lid} rec_fora={rec_fora}")
    ca.close(); ba.close()
