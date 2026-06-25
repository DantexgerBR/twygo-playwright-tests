# -*- coding: utf-8 -*-
"""Debug Q — usar seletor correto do drawer Vincular pessoas e selecionar usuário."""
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

LIDERADO_ID    = 4298605
FORA_ID        = 4298501

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

def obter_drawer(pg):
    """Retorna o locator do drawer 'Vincular pessoas' (não o popover de notificações)."""
    # O drawer é div.chakra-slide.chakra-modal__content (não section.chakra-popover__content)
    return pg.locator("div.chakra-modal__content:has(header:has-text('Vincular pessoas'))").first

def selecionar_usuario_drawer(pg, pessoa_email):
    """Seleciona um usuário no drawer."""
    drawer = obter_drawer(pg)
    if not drawer.count():
        log("  [drawer] não encontrado!")
        return False

    drawer_text = drawer.inner_text()
    log(f"  [drawer] texto (primeiros 400): {drawer_text[:400]}")

    # Campo "Buscar pessoa" — input dentro do form-control com label "Buscar pessoa"
    buscar_inp = drawer.locator("input[placeholder*='mail'], input[type='search'], input[type='text']").first
    if buscar_inp.count():
        buscar_inp.fill(pessoa_email)
        pg.wait_for_timeout(1500)
        log(f"  [busca] digitou {pessoa_email}")
        snap(pg, f"q_drawer_busca_{pessoa_email.split('@')[0][:8]}")

    # Listar itens de usuário na lista (após busca)
    itens = pg.evaluate(f"""() => {{
        const drawer = document.querySelector('div.chakra-modal__content:has(header)') ||
                      document.querySelector('.chakra-slide.chakra-modal__content');
        if (!drawer) return [];
        // Procurar por elementos que parecem cards de usuário
        const all = [...drawer.querySelectorAll('*')].filter(el => {{
            const r = el.getBoundingClientRect();
            return r.height >= 40 && r.height <= 120 && r.width > 200 && el.offsetParent !== null;
        }});
        return all.slice(0, 20).map(el => ({{
            tag: el.tagName,
            class: (el.className||'').slice(0,60),
            text: (el.innerText||'').slice(0,80),
            y: el.getBoundingClientRect().y,
            h: el.getBoundingClientRect().height,
        }}));
    }}""")
    log(f"  [itens pós-busca]: {json.dumps(itens, ensure_ascii=False)[:2000]}")

    # Procurar o item com o email na lista
    clicou = pg.evaluate(f"""() => {{
        const drawer = document.querySelector('div.chakra-modal__content') ||
                      document.querySelector('.chakra-slide.chakra-modal__content');
        if (!drawer) return 'no drawer';
        const walker = document.createTreeWalker(drawer, NodeFilter.SHOW_TEXT);
        let node;
        let found = null;
        while (node = walker.nextNode()) {{
            if (node.textContent.includes('{pessoa_email}') || node.textContent.includes('{pessoa_email.split('@')[0]}')) {{
                found = node.parentElement;
                break;
            }}
        }}
        if (!found) return 'text not found in drawer';
        // Encontrar o container clicável — subir até um div com altura >= 50
        let el = found;
        for (let i=0; i<8; i++) {{
            if (!el || el === drawer) break;
            const r = el.getBoundingClientRect();
            if (r.height >= 50 && r.width > 150) {{
                el.click();
                return 'clicked: ' + el.tagName + ' ' + el.className.slice(0,40) + ' text=' + (el.innerText||'').slice(0,30);
            }}
            el = el.parentElement;
        }}
        found.click();
        return 'clicked text parent: ' + found.tagName;
    }}""")
    log(f"  [selecionar] {clicou}")
    pg.wait_for_timeout(800)
    snap(pg, f"q_drawer_selecionado_{pessoa_email.split('@')[0][:8]}")

    # Verificar botão Vincular
    vincular = pg.locator("[data-test-id='resource-selector-drawer-confirm-button']").first
    if vincular.count():
        habilitado = vincular.evaluate("el => !el.disabled")
        log(f"  [vincular] habilitado={habilitado}")
        if habilitado:
            vincular.click(force=True)
            pg.wait_for_timeout(2000)
            log("  [vincular] clicou!")
            return True
    return False

def criar_registro_final(pg, pessoa_email, conteudo):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    abrir_drawer_pessoas(pg)
    drawer_aberto = obter_drawer(pg).count() > 0
    log(f"  [drawer] aberto={drawer_aberto}")

    if drawer_aberto:
        snap(pg, f"q_drawer_{conteudo[:8]}")
        ok = selecionar_usuario_drawer(pg, pessoa_email)
        log(f"  [selecionar] ok={ok}")
    else:
        log("  [drawer] não abriu!")

    snap(pg, f"q_form_apos_pessoas_{conteudo[:8]}")

    # Preencher campos
    c = pg.locator("#content input").first
    if c.count(): c.click(force=True); pg.keyboard.type(conteudo, delay=30); pg.wait_for_timeout(600); opt = pg.locator("[role='option']").first; opt.click() if opt.count() else pg.keyboard.press("Enter"); log("  [conteudo] OK")
    c = pg.locator("#provider input").first
    if c.count(): c.click(force=True); pg.keyboard.type("Alura", delay=30); pg.wait_for_timeout(600); opt = pg.locator("[role='option']").first; opt.click() if opt.count() else None; log("  [provedor] OK")
    c = pg.locator("#learningExperience input").first
    if c.count(): c.click(force=True); pg.keyboard.type("Curso", delay=30); pg.wait_for_timeout(600); opt = pg.locator("[role='option']").first; opt.click() if opt.count() else None; log("  [tipo] OK")
    c = pg.locator("#categories input").first
    if c.count(): c.click(force=True); pg.wait_for_timeout(500); opt = pg.locator("[role='option']").first; opt.click() if opt.count() else None; pg.keyboard.press("Escape"); log("  [cat] OK")
    pg.locator("input[placeholder='HH:MM:SS']").first.fill("01:00:00") if pg.locator("input[placeholder='HH:MM:SS']").count() else None
    pg.locator("input[type='date']").first.fill("2026-06-01") if pg.locator("input[type='date']").count() else None

    snap(pg, f"q_preenchido_{conteudo[:8]}")
    pg.evaluate("() => { const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='Salvar'); if(b) b.click(); }")
    pg.wait_for_timeout(5000)
    snap(pg, f"q_salvo_{conteudo[:8]}")

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
    log(f"  → rec_id={rec_id}")
    return rec_id

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    log("\n--- Criar registro para liderado1 ---")
    rec_lid = criar_registro_final(pg, "liderado1@teste.com", "QA116-Liderado-Externo")
    log(f"  rec_lid={rec_lid}")

    log("\n--- Criar registro para devtestes ---")
    rec_fora = criar_registro_final(pg, "devtestes@teste.com", "QA116-ForaEquipe-Externo")
    log(f"  rec_fora={rec_fora}")

    log(f"\nRESULTADO: rec_lid={rec_lid} rec_fora={rec_fora}")
    ca.close(); ba.close()
