# -*- coding: utf-8 -*-
"""Debug N — criar registro selecionando usuário no modal corretamente."""
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

def abrir_modal_pessoas(pg):
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
                return;
            }
        }
    }""")
    pg.wait_for_timeout(2000)

def selecionar_e_vincular(pg, pessoa_email):
    """Seleciona usuário no modal e clica Vincular."""
    modal = pg.locator("[role='dialog']").filter(visible=True).first
    if not modal.count():
        log("  [modal] não aberto!")
        return False

    # Inspecionar estrutura do modal
    dom = pg.evaluate("""() => {
        const d = document.querySelector('[role="dialog"]');
        if (!d) return null;
        // Todos os filhos diretos até 4 níveis
        const mapEl = (el, depth=0) => {
            if (depth > 3) return;
            return {
                tag: el.tagName,
                class: (el.className||'').slice(0,60),
                text: (el.innerText||'').slice(0,80),
                children: depth<3 ? [...el.children].slice(0,5).map(c=>mapEl(c, depth+1)) : []
            };
        };
        // Listar primeiros itens da lista de usuários
        const items = [...d.querySelectorAll('[class*="card"], [class*="user"], [class*="person"], [class*="row"], [class*="item"]')].slice(0,5);
        return {
            modal_text_slice: (d.innerText||'').slice(0,500),
            items: items.map(el => ({
                tag: el.tagName,
                class: el.className.slice(0,60),
                text: (el.innerText||'').slice(0,60),
                rect: el.getBoundingClientRect(),
            })),
        };
    }""")
    log(f"  [modal DOM] items: {json.dumps(dom.get('items',[]), ensure_ascii=False)}")

    # Tentar buscar com o input de busca correto
    # Do modal_text: "Buscar pessoa" seguido de placeholder
    search = modal.locator("input[type='text'], input[type='search'], input[placeholder*='mail']").first
    if search.count():
        pessoa_para_buscar = pessoa_email.split("@")[0]
        search.fill(pessoa_para_buscar)
        pg.wait_for_timeout(1500)
        log(f"  [busca] digitou '{pessoa_para_buscar}'")
        snap(pg, f"n_modal_busca_{pessoa_para_buscar[:8]}")

    # Inspecionar lista após busca
    items_apos = pg.evaluate("""() => {
        const d = document.querySelector('[role="dialog"]');
        if (!d) return [];
        // Pegar todos os elementos com altura > 30 dentro do scrollable da lista
        const allEls = [...d.querySelectorAll('*')].filter(el => {
            const r = el.getBoundingClientRect();
            return r.height > 30 && r.height < 200 && r.width > 100 && el.offsetParent !== null;
        });
        return allEls.slice(0,15).map(el => ({
            tag: el.tagName,
            class: (el.className||'').slice(0,50),
            text: (el.innerText||'').slice(0,60),
            rect: {x: el.getBoundingClientRect().x, y: el.getBoundingClientRect().y, h: el.getBoundingClientRect().height},
        }));
    }""")
    log(f"  [modal items pós-busca]: {json.dumps(items_apos, ensure_ascii=False)[:1000]}")

    # Tentar clicar nos primeiros itens para ver qual está relacionado ao usuário
    # Encontrar item que contém o email ou nome
    clicou = pg.evaluate(f"""() => {{
        const d = document.querySelector('[role="dialog"]');
        if (!d) return 'no dialog';
        const allEls = [...d.querySelectorAll('*')].filter(el => {{
            const txt = (el.innerText||'').toLowerCase();
            return (txt.includes('{pessoa_email.split('@')[0].lower()}') || txt.includes('{pessoa_email}')) &&
                   el.getBoundingClientRect().height > 15;
        }});
        if (allEls.length > 0) {{
            // Pegar o mais específico (menor container)
            const el = allEls.reduce((a,b) => a.getBoundingClientRect().height < b.getBoundingClientRect().height ? a : b);
            el.click();
            return 'clicked: ' + el.tagName + ' ' + (el.innerText||'').slice(0,40);
        }}
        // Se não encontrou, clicar no primeiro item da lista
        const lista = d.querySelector('[class*="list"], [class*="scroll"], [role="listbox"]');
        if (lista) {{
            const primeiro = lista.firstElementChild;
            if (primeiro) {{ primeiro.click(); return 'clicked first: ' + primeiro.tagName; }}
        }}
        return 'not found';
    }}""")
    log(f"  [selecionar] {clicou}")
    pg.wait_for_timeout(800)
    snap(pg, f"n_modal_pos_click_{pessoa_email.split('@')[0][:8]}")

    # Verificar se Vincular ficou habilitado
    vincular = pg.locator("[data-test-id='resource-selector-drawer-confirm-button']").first
    habilitado = False
    if vincular.count():
        habilitado = vincular.evaluate("el => !el.disabled")
        log(f"  [vincular] habilitado={habilitado}")

    if habilitado:
        vincular.click(force=True)
        pg.wait_for_timeout(2000)
        log("  [vincular] clicou!")
        return True
    else:
        log("  [vincular] ainda desabilitado — usuário não selecionado")
        return False

def criar_registro_v3(pg, pessoa_email, conteudo):
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    abrir_modal_pessoas(pg)
    modal_aberto = pg.locator("[role='dialog']").filter(visible=True).count() > 0
    log(f"  [modal] aberto={modal_aberto}")

    if modal_aberto:
        snap(pg, f"n_modal_{conteudo[:8]}")
        ok = selecionar_e_vincular(pg, pessoa_email)
        log(f"  [selecionar_e_vincular] ok={ok}")
    else:
        log("  [modal] não abriu")

    snap(pg, f"n_form_apos_modal_{conteudo[:8]}")

    # Conteúdo
    c = pg.locator("#content input").first
    if c.count(): c.click(force=True); pg.keyboard.type(conteudo, delay=30); pg.wait_for_timeout(600); opt = pg.locator("[role='option']").first; opt.click() if opt.count() else pg.keyboard.press("Enter"); log("  [conteudo] OK")
    # Provedor
    c = pg.locator("#provider input").first
    if c.count(): c.click(force=True); pg.keyboard.type("Alura", delay=30); pg.wait_for_timeout(600); opt = pg.locator("[role='option']").first; opt.click() if opt.count() else None; log("  [provedor] OK")
    # Tipo
    c = pg.locator("#learningExperience input").first
    if c.count(): c.click(force=True); pg.keyboard.type("Curso", delay=30); pg.wait_for_timeout(600); opt = pg.locator("[role='option']").first; opt.click() if opt.count() else None; log("  [tipo] OK")
    # Categorias
    c = pg.locator("#categories input").first
    if c.count(): c.click(force=True); pg.wait_for_timeout(500); opt = pg.locator("[role='option']").first; opt.click() if opt.count() else None; pg.keyboard.press("Escape"); log("  [cat] OK")
    # Carga e data
    pg.locator("input[placeholder='HH:MM:SS']").first.fill("01:00:00") if pg.locator("input[placeholder='HH:MM:SS']").count() else None
    pg.locator("input[type='date']").first.fill("2026-06-01") if pg.locator("input[type='date']").count() else None

    snap(pg, f"n_preenchido_{conteudo[:8]}")
    pg.evaluate("() => { const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='Salvar'); if(b) b.click(); }")
    pg.wait_for_timeout(5000)
    snap(pg, f"n_salvo_{conteudo[:8]}")

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
    rec_lid = criar_registro_v3(pg, "liderado1@teste.com", "QA116-Liderado-Externo")
    log(f"  rec_lid={rec_lid}")

    log("\n--- Criar registro para devtestes ---")
    rec_fora = criar_registro_v3(pg, "devtestes@teste.com", "QA116-ForaEquipe-Externo")
    log(f"  rec_fora={rec_fora}")

    log(f"\n=== RESULTADO ===\n  rec_lid={rec_lid}\n  rec_fora={rec_fora}")
    ca.close(); ba.close()
