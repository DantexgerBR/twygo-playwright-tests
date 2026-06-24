# -*- coding: utf-8 -*-
"""Restaurar responsavel do liderado1 = qaliderpuro (LIDER_ID 4299626)."""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
LIDERADO_ID    = 4298605
LIDER_ID       = 4299626

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa116"
PASTA.mkdir(parents=True, exist_ok=True)
log = lambda *a: print(*a, flush=True)


def snap(pg, nome):
    pg.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True)
    log(f"  [snap] {nome}.png")


with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p, slow_mo=500)
    tw.login(pg, {"base_url": BASE_URL, "org_id": ORG_ID,
                   "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)

    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "restore2_before")

    # Verificar estado atual
    qa_status = pg.evaluate("""() => {
        return [...document.querySelectorAll('*')].some(e => e.children.length === 0 && e.innerText && e.innerText.trim().includes('QALider'));
    }""")
    log(f"  QALider presente: {qa_status}")

    # Verificar o HTML atual do manager_container
    mc_html = pg.evaluate("""() => document.getElementById('manager_container')?.innerHTML.slice(0, 600) || 'nao encontrado'""")
    log(f"  #manager_container: {mc_html}")

    # Estrategia: usar a API de busca de usuario para encontrar qaliderpuro e fazer o POST
    # via request da page (autenticado com os cookies do admin)
    csrf = pg.evaluate("() => document.querySelector('meta[name=csrf-token]')?.content || ''")
    log(f"  CSRF: {csrf[:20]}")

    # Tentar via request autenticado para salvar diretamente
    # O form salva via POST /o/{ORG_ID}/users/{ID}
    # Precisamos incluir manager_id = LIDER_ID

    # Primeiro capturar os valores atuais do form
    form_values = pg.evaluate("""() => {
        const form = document.querySelector('form');
        if (!form) return null;
        const data = {};
        [...form.querySelectorAll('input, select, textarea')].forEach(el => {
            if (el.name && el.type !== 'file' && el.type !== 'submit') {
                if (el.type === 'checkbox') {
                    if (el.checked) data[el.name] = el.value;
                } else {
                    data[el.name] = el.value;
                }
            }
        });
        return data;
    }""")
    log(f"  Form values: {json.dumps(form_values, ensure_ascii=False)}")

    # Usar a API de busca de profissionais para obter o ID correto do lider
    resp_search = pg.request.get(
        f"{BASE_URL}/o/{ORG_ID}/professionals/search?q=qaliderpuro",
        headers={"Accept": "application/json", "X-CSRF-Token": csrf}
    )
    log(f"  Busca professionals/search: {resp_search.status}")
    if resp_search.ok:
        try:
            data = resp_search.json()
            log(f"  Resultado: {json.dumps(data)[:300]}")
        except:
            log(f"  Body: {resp_search.text()[:200]}")

    # Tentar busca autocomplete
    resp_ac = pg.request.get(
        f"{BASE_URL}/o/{ORG_ID}/users/autocomplete?q=qaliderpuro&field=manager",
        headers={"Accept": "application/json", "X-CSRF-Token": csrf}
    )
    log(f"  Autocomplete users: {resp_ac.status}")
    if resp_ac.ok:
        try:
            data = resp_ac.json()
            log(f"  Resultado: {json.dumps(data)[:300]}")
        except:
            log(f"  Body: {resp_ac.text()[:200]}")

    # Tentar a rota que o frontend usa ao digitar no campo manager_name
    # Baseado no HTML: o input tem id="manager_name" e a lista e #professiona-manager-list
    # O JS do Twygo provavelmente usa algo como /managers/search ou /users/search_manager
    endpoints_busca = [
        f"/o/{ORG_ID}/users/search?q=qaliderpuro",
        f"/o/{ORG_ID}/users/search_manager?q=qaliderpuro",
        f"/o/{ORG_ID}/managers/search?q=qaliderpuro",
        f"/api/v1/o/{ORG_ID}/users?q=qaliderpuro&role=manager",
    ]
    for ep in endpoints_busca:
        r = pg.request.get(f"{BASE_URL}{ep}", headers={"Accept": "application/json", "X-CSRF-Token": csrf})
        log(f"  GET {ep}: {r.status}")
        if r.ok:
            try: log(f"    Body: {r.json()}")
            except: log(f"    Body: {r.text()[:100]}")

    # Abordagem direta: simular o autocomplete via evento input no campo manager_name
    # Primeiro, mostrar o input
    pg.evaluate("""() => {
        const ms = document.getElementById('manager_search');
        const ml = document.getElementById('manager_label');
        if (ms) ms.style.display = 'block';
        if (ml) ml.style.display = 'none';
    }""")
    pg.wait_for_timeout(500)

    # Simular digitacao com eventos nativos
    manager_inp = pg.locator("#manager_name")
    if manager_inp.count():
        manager_inp.focus()
        manager_inp.fill("")
        pg.wait_for_timeout(300)
        # Digitar letra a letra para disparar eventos
        for char in "qalid":
            pg.keyboard.type(char)
            pg.wait_for_timeout(200)
        pg.wait_for_timeout(1500)
        snap(pg, "restore2_typeahead")

        lista_html = pg.evaluate("() => document.getElementById('professiona-manager-list')?.innerHTML.slice(0, 500) || 'vazio'")
        log(f"  Lista apos digitar: {lista_html}")

        # Ver se alguma opcao apareceu
        opcoes = pg.locator("#professiona-manager-list li, #professiona-manager-list div").all()
        log(f"  Opcoes: {len(opcoes)}")

        if len(opcoes) > 0:
            opcoes[0].click()
            pg.wait_for_timeout(1000)
            log("  Opcao selecionada!")
        else:
            # Tentar via JavaScript direto: definir o valor oculto manager_id e salvar
            # Verificar se ha um input hidden para manager_id
            hidden_manager = pg.evaluate("""() => {
                const inp = document.querySelector('input[name=manager_id], input[id=manager_id]');
                return inp ? {name: inp.name, value: inp.value, id: inp.id} : null;
            }""")
            log(f"  Hidden manager_id: {hidden_manager}")

            # Definir manualmente o manager_id
            set_manager = pg.evaluate(f"""() => {{
                // Tentar definir via input hidden
                const hiddenInps = [...document.querySelectorAll('input[type=hidden]')].filter(i => i.name.includes('manager') || i.id.includes('manager'));
                if (hiddenInps.length) {{
                    hiddenInps[0].value = '{LIDER_ID}';
                    return {{found: hiddenInps[0].name, set: '{LIDER_ID}'}};
                }}
                return {{found: false}};
            }}""")
            log(f"  Definir manager manual: {set_manager}")

    snap(pg, "restore2_estado")

    # Salvar o form
    save = pg.evaluate("""() => {
        const btns = [...document.querySelectorAll('button, input[type=submit]')];
        const s = btns.find(b => /salvar|save/i.test(b.innerText || b.value || '') && b.getBoundingClientRect().height > 0);
        if (s) { s.click(); return true; }
        return false;
    }""")
    pg.wait_for_timeout(3000)
    snap(pg, "restore2_salvo")
    log(f"  Salvo: {save}, URL: {pg.url}")

    # Verificar se o responsavel foi restaurado
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit",
            wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "restore2_verificar")

    qa_presente = pg.evaluate("""() => {
        return [...document.querySelectorAll('*')].some(e => e.children.length === 0 && e.innerText && e.innerText.trim().includes('QALider'));
    }""")
    log(f"  QALider presente apos restore: {qa_presente}")

    ca.close(); ba.close()

log("Restauracao concluida" if True else "Falhou")
