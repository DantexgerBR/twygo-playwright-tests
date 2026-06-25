# -*- coding: utf-8 -*-
"""Debug O — clicar diretamente nos cards da lista no modal, sem busca."""
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
                    if ((c.className||'').includes('css-zd45vb')) { c.click(); return; }
                    c = c.parentElement;
                }
                node.parentElement?.parentElement?.click();
                return;
            }
        }
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

    abrir_modal_pessoas(pg)
    pg.wait_for_timeout(1000)
    snap(pg, "o_modal_aberto")

    # Inspecionar TODOS os inputs no modal
    inputs_modal = pg.evaluate("""() => {
        const d = document.querySelector('[role="dialog"]');
        if (!d) return [];
        return [...d.querySelectorAll('input, textarea, [contenteditable]')].map(el => ({
            tag: el.tagName,
            type: el.type,
            placeholder: el.placeholder,
            name: el.name,
            id: el.id,
            visible: el.offsetParent !== null,
            rect: el.getBoundingClientRect(),
        }));
    }""")
    log(f"  Inputs no modal: {json.dumps(inputs_modal, ensure_ascii=False)}")

    # Inspecionar os primeiros elementos de lista/scroll
    lista = pg.evaluate("""() => {
        const d = document.querySelector('[role="dialog"]');
        if (!d) return null;
        // Encontrar a área de scroll com a lista de usuários
        const scrollable = [...d.querySelectorAll('*')].find(el => {
            return el.scrollHeight > el.clientHeight + 5 && el.clientHeight > 100;
        });
        if (!scrollable) {
            // Listar todos os elementos visíveis com altura entre 40-120px
            const els = [...d.querySelectorAll('*')].filter(el => {
                const r = el.getBoundingClientRect();
                return r.height >= 40 && r.height <= 120 && r.width > 200 && el.offsetParent !== null;
            });
            return {type: 'filtered', count: els.length, items: els.slice(0,8).map(el=>({
                tag: el.tagName,
                class: (el.className||'').slice(0,60),
                text: (el.innerText||'').slice(0,80),
                y: el.getBoundingClientRect().y,
            }))};
        }
        const children = [...scrollable.children].slice(0,5);
        return {type: 'scrollable', scrollable_class: (scrollable.className||'').slice(0,60), children: children.map(c=>({
            tag: c.tagName, class: (c.className||'').slice(0,60), text: (c.innerText||'').slice(0,60), y: c.getBoundingClientRect().y
        }))};
    }""")
    log(f"  Lista: {json.dumps(lista, ensure_ascii=False)[:2000]}")

    # Usar Playwright para encontrar os textos no modal diretamente
    modal = pg.locator("[role='dialog']").first
    modal_html = modal.evaluate("el => el.outerHTML.slice(0, 3000)")
    log(f"  Modal HTML (primeiros 3000): {modal_html}")

    ca.close(); ba.close()
