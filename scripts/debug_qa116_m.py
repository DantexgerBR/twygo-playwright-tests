# -*- coding: utf-8 -*-
"""Debug M — criar registros com fluxo correto do modal Vincular pessoas."""
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
    """Clica na div .css-zd45vb para abrir o modal Vincular pessoas."""
    # Encontrar o elemento "Adicionar pessoas" e clicar no container
    clicked = pg.evaluate("""() => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim() === 'Adicionar pessoas') {
                const el = node.parentElement;
                let container = el;
                for (let i=0; i<8; i++) {
                    if (!container) break;
                    if ((container.className||'').includes('css-zd45vb') ||
                        (container.className||'').includes('chakra-input__group') ||
                        container.getAttribute('tabindex') === '0') {
                        container.click();
                        return {clicked: true, class: container.className.slice(0,60)};
                    }
                    container = container.parentElement;
                }
                // Clicar no próprio elemento pai
                el.parentElement.click();
                return {clicked: true, class: 'parent', note: 'fallback'};
            }
        }
        return {clicked: false, reason: 'text not found'};
    }""")
    pg.wait_for_timeout(2000)
    return clicked

def selecionar_usuario_modal(pg, pessoa_email):
    """Seleciona usuário no modal Vincular pessoas."""
    modal = pg.locator("[role='dialog']").filter(visible=True).first
    if not modal.count():
        return False

    # Buscar pelo email
    search = modal.locator("input").filter(visible=True).first
    if search.count():
        search.fill(pessoa_email)
        pg.wait_for_timeout(1500)

    # Clicar no card do usuário
    # No modal, cada usuário é um card clicável com avatar + nome + email
    result = pg.evaluate(f"""() => {{
        const dialog = document.querySelector('[role="dialog"]');
        if (!dialog) return 'no dialog';

        // Encontrar o item com o email
        const walker = document.createTreeWalker(dialog, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {{
            if (node.textContent.includes('{pessoa_email.split('@')[0]}') ||
                node.textContent.includes('{pessoa_email}')) {{
                const el = node.parentElement;
                // Subir até o card clicável
                let card = el;
                for (let i=0; i<6; i++) {{
                    if (!card || card === dialog) break;
                    if (card.offsetHeight > 30 && card.offsetWidth > 100) {{
                        card.click();
                        return 'clicked card: ' + card.tagName + ' ' + card.className.slice(0,40);
                    }}
                    card = card.parentElement;
                }}
            }}
        }}
        return 'user not found in dialog';
    }}""")
    log(f"  [selecionar] {result}")
    pg.wait_for_timeout(800)
    snap(pg, f"m_modal_selecionado_{pessoa_email.split('@')[0][:8]}")
    return True

def confirmar_modal(pg):
    """Clica no botão Associar do modal."""
    modal = pg.locator("[role='dialog']").filter(visible=True).first
    if not modal.count():
        return False
    btns = [b.inner_text().strip() for b in modal.locator("button").all()]
    log(f"  [confirmar] botões: {btns}")
    btn_assoc = modal.locator("button").filter(has_text=re.compile(r"Associar|Vincular|Adicionar|Confirmar", re.I)).first
    if btn_assoc.count():
        btn_assoc.click(); pg.wait_for_timeout(2000)
        return True
    # Clicar no último botão (não-cancelar)
    all_btns = modal.locator("button").all()
    for btn in reversed(all_btns):
        txt = btn.inner_text().strip().lower()
        if txt and "cancelar" not in txt and "fechar" not in txt and "×" not in txt:
            btn.click(); pg.wait_for_timeout(2000)
            log(f"  [confirmar] clicou '{txt}'")
            return True
    return False

def criar_registro_completo(pg, pessoa_email, conteudo):
    """Fluxo completo de criação de registro externo."""
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # Pessoas
    click_result = abrir_modal_pessoas(pg)
    log(f"  [pessoas] modal click: {click_result}")
    modal_aberto = pg.locator("[role='dialog']").filter(visible=True).count() > 0
    log(f"  [pessoas] modal aberto: {modal_aberto}")

    if modal_aberto:
        snap(pg, f"m_modal_{conteudo[:8]}")
        selecionar_usuario_modal(pg, pessoa_email)
        confirmar_modal(pg)
    else:
        log("  [pessoas] modal não abriu — forçando via JS direto no hidden input")
        pg.evaluate(f"""() => {{
            const inp = document.querySelector('input[name="people"]');
            if (inp) {{
                inp.value = '{LIDERADO_ID if "liderado" in pessoa_email else FORA_ID}';
                inp.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
        }}""")

    snap(pg, f"m_form_apos_pessoas_{conteudo[:8]}")

    # Conteúdo
    for sel in ["#content input", "[id='content'] input", "div[id='content'] input"]:
        c = pg.locator(sel).first
        if c.count():
            c.click(force=True); pg.keyboard.type(conteudo, delay=30); pg.wait_for_timeout(700)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            else: pg.keyboard.press("Enter")
            log("  [conteudo] OK"); break

    # Provedor
    for sel in ["#provider input"]:
        c = pg.locator(sel).first
        if c.count():
            c.click(force=True); pg.keyboard.type("Alura", delay=30); pg.wait_for_timeout(700)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            log("  [provedor] OK"); break

    # Tipo experiência
    for sel in ["#learningExperience input"]:
        c = pg.locator(sel).first
        if c.count():
            c.click(force=True); pg.keyboard.type("Curso", delay=30); pg.wait_for_timeout(700)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click()
            log("  [tipo] OK"); break

    # Categorias
    for sel in ["#categories input"]:
        c = pg.locator(sel).first
        if c.count():
            c.click(force=True); pg.wait_for_timeout(500)
            opt = pg.locator("[role='option']").first
            if opt.count(): opt.click(); pg.keyboard.press("Escape")
            log("  [cat] OK"); break

    # Carga horária e data
    pg.locator("input[placeholder='HH:MM:SS']").first.fill("01:00:00") if pg.locator("input[placeholder='HH:MM:SS']").count() else None
    pg.locator("input[type='date']").first.fill("2026-06-01") if pg.locator("input[type='date']").count() else None

    snap(pg, f"m_preenchido_{conteudo[:8]}")

    # Salvar
    pg.evaluate("() => { const btn = [...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='Salvar'); if(btn) btn.click(); }")
    pg.wait_for_timeout(5000)
    snap(pg, f"m_salvo_{conteudo[:8]}")

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
    log(f"  → criou={criou} rec_id={rec_id} url={url_d}")
    return rec_id

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    log("\n--- Criar registro para liderado1 ---")
    rec_lid = criar_registro_completo(pg, "liderado1@teste.com", "QA116-Liderado-Externo")
    log(f"  rec_liderado_id={rec_lid}")

    log("\n--- Criar registro para devtestes ---")
    rec_fora = criar_registro_completo(pg, "devtestes@teste.com", "QA116-ForaEquipe-Externo")
    log(f"  rec_fora_id={rec_fora}")

    log(f"\n=== Resultado ===")
    log(f"  rec_liderado_id={rec_lid}")
    log(f"  rec_fora_id={rec_fora}")

    # Salvar
    resultado = {"rec_liderado_id": rec_lid, "rec_fora_id": rec_fora}
    (PASTA/"debug_m_resultado.json").write_text(json.dumps(resultado, indent=2), encoding="utf-8")

    ca.close(); ba.close()
