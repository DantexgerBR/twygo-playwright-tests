# -*- coding: utf-8 -*-
"""Debug S — (1) checar registros existentes, (2) verificar kebab reset senha qaliderpuro."""
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

with tw.sync_playwright() as p:
    ba, ca, pg = tw.nova_pagina(p)
    tw.login(pg, {"base_url":BASE_URL,"org_id":ORG_ID,"email":ADMIN_EMAIL,"senha":ADMIN_PASSWORD}, admin=True)
    log("[admin] logado")

    # --- 1. GET registros existentes ---
    log("\n=== CHECK 1: Registros existentes ===")
    r = pg.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records?per_page=50&page=1&order_by=created_at&order_type=desc",
        headers={"Accept":"application/json"}
    )
    log(f"  status={r.status}")
    if r.status == 200:
        body = r.json()
        recs = body.get("data",{}).get("records",[])
        total = body.get("data",{}).get("pagination",{}).get("total_entries", 0)
        log(f"  total_entries={total}, recs na pagina={len(recs)}")
        for rec in recs[:20]:
            log(f"    id={rec.get('id')} conteudo={rec.get('content')} pessoa_ids={rec.get('professional_ids')} aprovado={rec.get('approved')}")

    # Filtrar por usuário específico (liderado1 = 4298605, devtestes = 4298501, qaliderpuro = 4299626)
    LIDERADO_ID = 4298605
    FORA_ID = 4298501
    QALIDERPURO_ID = 4299626
    QAINSTATIVO_ID = None  # TC4 — a definir

    if r.status == 200:
        recs_liderado = [x for x in recs if LIDERADO_ID in (x.get("professional_ids") or [])]
        recs_fora = [x for x in recs if FORA_ID in (x.get("professional_ids") or [])]
        log(f"\n  Registros liderado1 ({LIDERADO_ID}): {len(recs_liderado)}")
        for x in recs_liderado: log(f"    id={x.get('id')} conteudo={x.get('content')}")
        log(f"  Registros devtestes ({FORA_ID}): {len(recs_fora)}")
        for x in recs_fora: log(f"    id={x.get('id')} conteudo={x.get('content')}")

    # --- 2. Kebab / acoes na lista de usuários para qaliderpuro ---
    log("\n=== CHECK 2: Ações disponíveis na lista de usuários ===")
    pg.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
    try: pg.wait_for_load_state("networkidle", timeout=8000)
    except: pass
    pg.wait_for_timeout(2000)
    snap(pg, "s_users_list")

    # Procurar linha de qaliderpuro e clicar no kebab
    # A lista está em tabela — procurar pelo texto "qaliderpuro"
    qarow = pg.locator("tr").filter(has_text="qaliderpuro")
    if not qarow.count():
        qarow = pg.locator("[class*='row'], [class*='item'], tr").filter(has_text="qaliderpuro")
    log(f"  qaliderpuro rows: {qarow.count()}")

    if qarow.count():
        # Tentar clicar no kebab (botão de 3 pontos / ... / ações)
        kebab = qarow.first.locator("button[aria-label*='ações'], button[aria-label*='menu'], button[title*='ações'], button[data-test*='kebab'], [class*='kebab'], button:has-text('...'), button:has-text('⋮')").first
        if not kebab.count():
            # Qualquer botão na linha
            kebab = qarow.first.locator("button").last
        log(f"  kebab count={kebab.count()}")
        if kebab.count():
            kebab.click()
            pg.wait_for_timeout(1500)
            snap(pg, "s_kebab_qaliderpuro")
            # Listar opções do menu
            opcoes_menu = pg.locator("[role='menuitem'], [role='option'], [data-test*='menu-item'], .chakra-menu__menuitem").all_text_contents()
            log(f"  Opcoes kebab: {opcoes_menu}")
            # Procurar "Redefinir senha" / "Resetar senha" / "Alterar senha"
            for txt in opcoes_menu:
                if any(p in txt.lower() for p in ["senha", "password", "reset"]):
                    log(f"  *** ENCONTROU RESET SENHA: '{txt}'")
    else:
        log("  qaliderpuro não encontrado na lista")
        # Listar nomes na tabela
        nomes = pg.locator("td:first-child, [class*='name']").all_text_contents()[:20]
        log(f"  Nomes visíveis: {nomes}")

    # --- 3. Buscar pelo campo de busca ---
    log("\n=== CHECK 3: Busca na lista de usuários ===")
    busca = pg.locator("input[type='search'], input[placeholder*='usuário'], input[placeholder*='Pesquisa']").first
    if not busca.count():
        busca = pg.locator("input[type='text']").first
    if busca.count():
        busca.fill("qaliderpuro")
        pg.wait_for_timeout(2000)
        snap(pg, "s_busca_qaliderpuro")
        rows = pg.locator("tr").filter(has_text="qaliderpuro")
        log(f"  Após busca, linhas com qaliderpuro: {rows.count()}")
        if rows.count():
            # Tentar abrir kebab
            kebab = tw.abrir_kebab(rows.first)
            if kebab:
                snap(pg, "s_kebab_apos_busca")
                opcoes_menu = pg.locator("[role='menuitem'], .chakra-menu__menuitem").all_text_contents()
                log(f"  Opcoes kebab (pós busca): {opcoes_menu}")

    ca.close(); ba.close()
