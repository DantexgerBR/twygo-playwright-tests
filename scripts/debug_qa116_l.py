# -*- coding: utf-8 -*-
"""Debug L — mapear exatamente o DOM do campo Pessoas e clicar corretamente."""
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

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # Mapear TODOS os elementos com "Adicionar pessoas" ou na área de Pessoas
    dom = pg.evaluate("""() => {
        // Buscar por texto "Adicionar pessoas"
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        const results = [];
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.includes('Adicionar pessoas') || node.textContent.includes('Adicionar pessoa')) {
                const el = node.parentElement;
                let ancestor = el;
                for (let i=0; i<6; i++) {
                    if (!ancestor) break;
                    results.push({
                        level: i,
                        tag: ancestor.tagName,
                        class: (ancestor.className||'').slice(0,80),
                        role: ancestor.getAttribute('role'),
                        onclick: ancestor.onclick ? 'has onclick' : null,
                        tabindex: ancestor.getAttribute('tabindex'),
                        visible: ancestor.offsetParent !== null,
                        rect: ancestor.getBoundingClientRect(),
                        text: (ancestor.innerText||'').slice(0,50),
                    });
                    ancestor = ancestor.parentElement;
                }
                break;
            }
        }
        return results;
    }""")
    log(f"  'Adicionar pessoas' DOM path:")
    for el in dom:
        log(f"    L{el['level']}: {el['tag']} class={el['class'][:50]} role={el['role']} tabindex={el['tabindex']} visible={el['visible']} rect_y={el.get('rect',{}).get('y','?')}")

    # Encontrar o elemento clicável mais próximo de "Adicionar pessoas"
    target = pg.evaluate("""() => {
        // Encontrar o elemento visível mais próximo de "Adicionar pessoas"
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim() === 'Adicionar pessoas') {
                const el = node.parentElement;
                // Subir até encontrar elemento com onclick ou tabindex ou button/div clicável
                let container = el;
                for (let i=0; i<8; i++) {
                    if (!container) break;
                    if (container.tagName === 'BUTTON' ||
                        container.getAttribute('role') === 'button' ||
                        container.onclick ||
                        container.getAttribute('tabindex') === '0') {
                        const r = container.getBoundingClientRect();
                        return {tag: container.tagName, class: container.className.slice(0,80), x: r.x + r.width/2, y: r.y + r.height/2, w: r.width, h: r.height};
                    }
                    container = container.parentElement;
                }
                // Se não encontrou, retornar o próprio elemento text
                const r = el.getBoundingClientRect();
                return {tag: el.tagName, class: el.className.slice(0,80), x: r.x + r.width/2, y: r.y + r.height/2, w: r.width, h: r.height, note: 'fallback to text parent'};
            }
        }
        return null;
    }""")
    log(f"  Target clicável: {target}")

    if target:
        pg.mouse.click(target["x"], target["y"])
        pg.wait_for_timeout(2000)
        snap(pg, "l_click_target")
        modal = pg.locator("[role='dialog']").filter(visible=True).first
        log(f"  Modal após click target: {modal.count() > 0}")
        if modal.count():
            log(f"  Modal text: {modal.inner_text()[:300]}")
            snap(pg, "l_modal_pessoas")

    # Se ainda não abriu, tentar o ícone de pessoa (SVG ou span com ícone)
    if not pg.locator("[role='dialog']").filter(visible=True).count():
        log("\n  Tentando clicar no ícone de pessoa...")
        pessoa_icon = pg.evaluate("""() => {
            // Encontrar o ícone de pessoa (material icon 'person' ou similar)
            const icons = [...document.querySelectorAll('span.material-icons, span.material-symbols-outlined, button svg')];
            for (const icon of icons) {
                const txt = icon.innerText || icon.textContent || '';
                if (txt.includes('person') || txt.includes('people') || txt.includes('group_add')) {
                    const r = icon.getBoundingClientRect();
                    return {x: r.x + r.width/2, y: r.y + r.height/2, text: txt.slice(0,20)};
                }
            }
            // Buscar botão próximo ao label Pessoas
            const form_controls = [...document.querySelectorAll('.chakra-form-control')];
            for (const fc of form_controls) {
                if ((fc.innerText||'').includes('Pessoas')) {
                    const btns = fc.querySelectorAll('button');
                    if (btns.length) {
                        const r = btns[0].getBoundingClientRect();
                        return {x: r.x + r.width/2, y: r.y + r.height/2, text: btns[0].innerText.slice(0,20), tag: 'button'};
                    }
                }
            }
            return null;
        }""")
        log(f"  Ícone pessoa: {pessoa_icon}")
        if pessoa_icon:
            pg.mouse.click(pessoa_icon["x"], pessoa_icon["y"])
            pg.wait_for_timeout(2000)
            snap(pg, "l_click_icone")
            modal2 = pg.locator("[role='dialog']").filter(visible=True).first
            log(f"  Modal após ícone: {modal2.count() > 0}")

    ca.close(); ba.close()
