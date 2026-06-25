# -*- coding: utf-8 -*-
"""Debug P — encontrar o overlay real de Vincular pessoas (não o popover de notificações)."""
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

def abrir_modal_pessoas(pg):
    pg.evaluate("""() => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim() === 'Adicionar pessoas') {
                let c = node.parentElement;
                for (let i=0; i<8; i++) {
                    if (!c) break;
                    if ((c.className||'').includes('css-zd45vb')) { c.click(); return 'clicked css-zd45vb'; }
                    c = c.parentElement;
                }
                node.parentElement?.parentElement?.click();
                return 'clicked fallback';
            }
        }
        return 'text not found';
    }""")
    pg.wait_for_timeout(2000)

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(3000)
    dispensar(pg)

    # Antes de clicar — listar todos os overlays existentes
    before = pg.evaluate("""() => {
        return [...document.querySelectorAll('[role="dialog"], [role="alertdialog"], .chakra-modal__content, .chakra-drawer__content, [data-testid*="modal"], [data-testid*="drawer"]')]
        .filter(el => el.offsetParent !== null || window.getComputedStyle(el).visibility !== 'hidden')
        .map(el => ({tag: el.tagName, role: el.getAttribute('role'), class: el.className.slice(0,60), visible: el.offsetParent !== null, text: (el.innerText||'').slice(0,50)}));
    }""")
    log(f"  Overlays antes: {json.dumps(before, ensure_ascii=False)}")

    abrir_modal_pessoas(pg)
    pg.wait_for_timeout(1500)
    snap(pg, "p_modal_aberto")

    # Listar todos os overlays depois de clicar
    after = pg.evaluate("""() => {
        return [...document.querySelectorAll('[role="dialog"], [role="alertdialog"], .chakra-modal__content, .chakra-drawer__content, [data-testid*="modal"], [data-testid*="drawer"], section[role="dialog"], [class*="modal"], [class*="drawer"], [class*="overlay"]')]
        .filter(el => el.offsetParent !== null)
        .map(el => ({
            tag: el.tagName,
            role: el.getAttribute('role'),
            class: el.className.slice(0,80),
            data_test: el.getAttribute('data-testid'),
            visible: el.offsetParent !== null,
            text: (el.innerText||'').slice(0,100)
        }));
    }""")
    log(f"  Overlays depois: {json.dumps(after, ensure_ascii=False)}")

    # Procurar por qualquer elemento que contenha "Vincular pessoas"
    vincular = pg.evaluate("""() => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.includes('Vincular pessoas') || node.textContent.includes('Vincular')) {
                const el = node.parentElement;
                const r = el.getBoundingClientRect();
                return {
                    found: true,
                    tag: el.tagName,
                    class: (el.className||'').slice(0,60),
                    text: node.textContent.slice(0,50),
                    parent_chain: (() => {
                        let chain = [], node2 = el;
                        for (let i=0; i<10 && node2; i++) {
                            chain.push({tag: node2.tagName, class: (node2.className||'').slice(0,40), role: node2.getAttribute('role')});
                            node2 = node2.parentElement;
                        }
                        return chain;
                    })(),
                };
            }
        }
        return {found: false};
    }""")
    log(f"  'Vincular pessoas' no DOM: {json.dumps(vincular, ensure_ascii=False)}")

    # Tentar localizar o drawer pelo texto do header "Vincular pessoas"
    drawer_header = pg.locator("text=Vincular pessoas").first
    log(f"  locator 'Vincular pessoas': {drawer_header.count()} visivel={drawer_header.count() > 0}")
    if drawer_header.count():
        # Pegar o container pai que é o drawer
        drawer_el = drawer_header.evaluate("""el => {
            let node = el;
            for (let i=0; i<10; i++) {
                if (!node) break;
                if (node.getAttribute('role') === 'dialog' || (node.className||'').includes('drawer') || (node.className||'').includes('modal')) {
                    return {role: node.getAttribute('role'), class: node.className.slice(0,80)};
                }
                node = node.parentElement;
            }
            return null;
        }""")
        log(f"  Drawer container: {drawer_el}")
        snap(pg, "p_vincular_pessoas_header")

        # Inspecionar a lista de usuários dentro do drawer
        lista_info = pg.evaluate("""() => {
            const header = [...document.querySelectorAll('*')].find(el => (el.innerText||'').trim() === 'Vincular pessoas');
            if (!header) return 'header not found';
            // Subir para o container do drawer
            let container = header;
            for (let i=0; i<10; i++) {
                if (!container) break;
                if (container.offsetHeight > 400) {
                    // Listar filhos que parecem itens de usuário
                    const items = [...container.querySelectorAll('*')].filter(el => {
                        const r = el.getBoundingClientRect();
                        return r.height >= 40 && r.height <= 100 && r.width > 150 && el.offsetParent !== null;
                    });
                    return {
                        container_class: container.className.slice(0,80),
                        items_count: items.length,
                        sample_items: items.slice(0,5).map(el => ({
                            tag: el.tagName,
                            class: (el.className||'').slice(0,60),
                            text: (el.innerText||'').slice(0,80),
                            y: el.getBoundingClientRect().y,
                        })),
                    };
                }
                container = container.parentElement;
            }
            return 'container not found';
        }""")
        log(f"  Lista dentro do drawer: {json.dumps(lista_info, ensure_ascii=False)[:2000]}")

    ca.close(); ba.close()
