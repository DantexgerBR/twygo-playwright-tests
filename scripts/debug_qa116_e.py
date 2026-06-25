# -*- coding: utf-8 -*-
"""Debug E — definir perfis do lider puro, montar organograma, senha via reset, criar registros."""
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

LIDER_PURO_ID = 4299626
LIDERADO_ID   = 4298605
FORA_ID       = 4298501

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

    # 1. Editar qaliderpuro: marcar SOMENTE "Gestor de turma" e definir senha via admin
    log("\n--- 1. Editar qaliderpuro: perfil + senha ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDER_PURO_ID}/edit", wait_until="domcontentloaded", timeout=20000)
    dispensar(pg)
    pg.wait_for_timeout(3000)

    # Marcar "Gestor de turma" via label/checkbox
    # Do screenshot vemos que os perfis são checkboxes
    for perfil_txt in ["Administrador", "Instrutor", "Gestor de turma"]:
        chk = pg.locator(f"input[type='checkbox']").filter(has_text=perfil_txt)
        if chk.count() == 0:
            # Tentar pelo label
            lbl = pg.locator(f"label:has-text('{perfil_txt}')").first
            if lbl.count():
                chk = lbl.locator("input[type='checkbox']").first
                if chk.count() == 0:
                    chk = lbl.locator("xpath=preceding-sibling::input").first
        # Verificar estado atual
        label_el = pg.locator(f"label:has-text('{perfil_txt}')").first
        if label_el.count():
            # Verificar se checkbox ao lado está marcado
            chk2 = pg.locator(f"input[type='checkbox']").nth(0)
            # Simplificar: usar JS para encontrar o checkbox pelo label text
            is_checked = pg.evaluate(f"""() => {{
                const labels = [...document.querySelectorAll('label')];
                const lbl = labels.find(l => l.innerText.trim() === '{perfil_txt}');
                if (!lbl) return null;
                const chk = lbl.querySelector('input[type="checkbox"]') || lbl.previousElementSibling;
                return chk ? chk.checked : null;
            }}""")
            log(f"  {perfil_txt}: checked={is_checked}")

    # Usar JS para marcar SOMENTE Gestor de turma
    result = pg.evaluate("""() => {
        const result = {};
        const labels = [...document.querySelectorAll('label')];
        for (const lbl of labels) {
            const txt = lbl.innerText.trim();
            if (['Administrador', 'Instrutor', 'Gestor de turma'].includes(txt)) {
                const chk = lbl.querySelector('input[type="checkbox"]');
                if (chk) {
                    result[txt] = {before: chk.checked, id: chk.id, name: chk.name};
                }
            }
        }
        return result;
    }""")
    log(f"  Perfis encontrados via JS: {result}")

    # Verificar se Gestor de turma está marcado; se não, marcar
    for perfil, info in result.items():
        if info:
            chk_name = info.get("name") or info.get("id")
            is_checked = info.get("before", False)
            if perfil == "Gestor de turma" and not is_checked:
                # Clicar no label para marcar
                pg.evaluate(f"""() => {{
                    const labels = [...document.querySelectorAll('label')];
                    const lbl = labels.find(l => l.innerText.trim() === '{perfil}');
                    if (lbl) lbl.click();
                }}""")
                pg.wait_for_timeout(300)
                log(f"  Marcou: {perfil}")
            elif perfil in ["Administrador", "Instrutor"] and is_checked:
                # Desmarcar
                pg.evaluate(f"""() => {{
                    const labels = [...document.querySelectorAll('label')];
                    const lbl = labels.find(l => l.innerText.trim() === '{perfil}');
                    if (lbl) lbl.click();
                }}""")
                pg.wait_for_timeout(300)
                log(f"  Desmarcou: {perfil}")

    snap(pg, "e_lider_edit_perfis")

    # Salvar
    btn_sal = pg.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first
    btn_sal.click(timeout=5000)
    pg.wait_for_timeout(3000)
    log(f"  url apos salvar: {pg.url}")
    snap(pg, "e_lider_edit_salvo")

    # 2. Tentar reset de senha via admin (API)
    log("\n--- 2. Reset de senha via API ---")
    resp_pwd = pg.request.post(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/professionals/{LIDER_PURO_ID}/reset_password",
        headers={"Accept":"application/json","Content-Type":"application/json"},
        data=json.dumps({"new_password": "123456", "password_confirmation": "123456"}),
    )
    log(f"  reset_password status={resp_pwd.status} body={resp_pwd.text()[:200]}")

    # Tentar outros endpoints
    for path, payload in [
        (f"/api/v1/o/{ORG_ID}/professionals/{LIDER_PURO_ID}", json.dumps({"professional": {"password": "123456", "password_confirmation": "123456"}})),
        (f"/o/{ORG_ID}/users/{LIDER_PURO_ID}/reset_password", json.dumps({"password": "123456"})),
    ]:
        resp2 = pg.request.patch(
            BASE_URL + path,
            headers={"Accept":"application/json","Content-Type":"application/json"},
            data=payload,
        )
        log(f"  PATCH {path[:50]}: status={resp2.status} body={resp2.text()[:100]}")

    # Tentar via UI: admin pode "simular" senha do usuário? Buscar na tela
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDER_PURO_ID}/edit", wait_until="domcontentloaded", timeout=15000)
    dispensar(pg)
    pg.wait_for_timeout(2000)
    # Procurar link "Alterar senha" ou input de senha (pode estar em outra aba)
    abas = pg.locator("a[role='tab'], button[role='tab'], .chakra-tabs__tab").all_text_contents()
    log(f"  Abas disponíveis: {abas}")
    senhas_inp = pg.locator("input[type='password']").all()
    log(f"  Inputs de senha encontrados: {len(senhas_inp)}")
    snap(pg, "e_lider_edit_senha_busca")

    # 3. Montar organograma via campo "Responsável" do liderado1
    log("\n--- 3. Montar organograma (liderado1 -> qaliderpuro) ---")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users/{LIDERADO_ID}/edit", wait_until="domcontentloaded", timeout=15000)
    dispensar(pg)
    pg.wait_for_timeout(3000)
    snap(pg, "e_liderado_edit")

    # Campo "Responsável" com busca
    resp_input = pg.locator("input[placeholder*='Responsável'], input[placeholder*='esponsavel'], input[placeholder*='esponsável']").first
    if resp_input.count() == 0:
        # Buscar pelo label
        resp_label = pg.locator("label:has-text('Responsável')").first
        if resp_label.count():
            resp_input = resp_label.locator("xpath=following-sibling::input").first
            if resp_input.count() == 0:
                resp_input = resp_label.locator("xpath=../input").first
    log(f"  campo Responsavel: {resp_input.count()}")
    snap(pg, "e_liderado_responsavel_campo")

    # Também verificar campo "Liderança" / "Líder de equipe"
    lidereq_input = pg.locator("input[placeholder*='Líder'], input[placeholder*='Lider']").first
    log(f"  campo Liderança/Líder: {lidereq_input.count()}")

    # Tentar via ícone de busca ao lado do campo Responsável
    # No screenshot vemos um ícone de lupa ao lado do campo "Responsável"
    lupa_btn = pg.locator("[title*='Responsável'] + button, button[aria-label*='Responsável'], label:has-text('Responsável') ~ button").first
    log(f"  lupa_btn count: {lupa_btn.count()}")

    # Procurar o input próximo ao label "Responsável" de forma mais agressiva
    resp_box = pg.evaluate("""() => {
        const labels = [...document.querySelectorAll('label, .chakra-text, span, p')];
        const lbl = labels.find(l => (l.innerText||'').trim() === 'Responsável');
        if (!lbl) return 'label not found';
        const parent = lbl.parentElement;
        const inputs = parent.querySelectorAll('input');
        return {
            lbl_text: lbl.innerText,
            parent_class: parent.className.slice(0,60),
            inputs: [...inputs].map(i => ({type: i.type, placeholder: i.placeholder, name: i.name, id: i.id})),
        };
    }""")
    log(f"  Responsável DOM: {resp_box}")

    ca.close(); ba.close()
