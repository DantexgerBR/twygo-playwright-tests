"""Retrabalho 19602 — [Recertificação] Desempenho na trilha não corresponde corretamente.

Bug: na aba Aprendizagem (visão admin) de uma trilha, o Desempenho da inscrição
atual do usuario nao corresponde — as varias inscricoes do MESMO usuario mostram
desempenho/pontuacao identicos apesar de progresso diferente, e o % muda conforme
avanca cursos (67% -> 69%) sem fazer questionarios.

Env: RECERTIFICACAO (NAO o env fixo do .env). org 37048.
Validacao: abrir a trilha "Trilha para CASCADE" > Aprendizagem e extrair a tabela
(participante, progresso, desempenho, pontuacao) pra comparar inscricoes do mesmo user.
"""
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

# --- Env da RECERTIFICACAO (hardcoded; NAO usar .env que aponta pra 36675) ---
BASE_URL = "https://recertificacao-testeqa.stage.twygoead.com"
ORG_ID = "37048"
# Credenciais: tenta a do retrabalho primeiro, fallback pra da memoria
CREDS = [
    ("agents.claude@claude.com", "123456"),
    ("agents.qa@claude.com", "123456"),
]

PASTA = ROOT / "evidencias" / "19602_desempenho_trilha"
PASTA.mkdir(parents=True, exist_ok=True)


def snap(page, nome):
    p = PASTA / f"{nome}.png"
    page.screenshot(path=str(p), full_page=False)
    print(f"   [snap] {p.name}")
    return p


def tentar_login(page, email, senha):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", email)
    page.fill("#user_password", senha)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    return page.url


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=400)
    context = browser.new_context(viewport={"width": 1500, "height": 900}, locale="pt-BR")
    page = context.new_page()

    # --- Login (tenta credenciais em ordem) ---
    logado_email = None
    for email, senha in CREDS:
        print(f"[login] tentando {email} ...")
        url = tentar_login(page, email, senha)
        print(f"   pos-login url: {url}")
        if "/login" not in url and "/users/login" not in url:
            logado_email = email
            print(f"   OK logado como {email}")
            break
        else:
            print("   falhou, proxima credencial")

    if not logado_email:
        print("FALHA: nenhuma credencial logou. Abortando.")
        snap(page, "00-falha-login")
        context.close()
        browser.close()
        raise SystemExit(1)

    # --- Switch pra admin ---
    page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    print(f"[admin] url: {page.url}")
    snap(page, "01-listagem-eventos-admin")

    if "/users/login" in page.url:
        print("FALHA: sessao invalidada (login concorrente).")
        context.close()
        browser.close()
        raise SystemExit(1)

    # --- Dispensar modal de NPS se aparecer ---
    def dispensar_nps():
        try:
            btn = page.get_by_role("button", name="Pergunte depois")
            if btn.count() and btn.first.is_visible():
                btn.first.click()
                page.wait_for_timeout(1200)
                print("   [nps] modal dispensada")
        except Exception:
            pass
        # tambem tentar X
        try:
            x = page.locator("button:has-text('×'), .modal .close, [aria-label='Close']").first
            if x.count() and x.is_visible():
                x.click()
                page.wait_for_timeout(800)
        except Exception:
            pass

    dispensar_nps()

    # --- Procurar a trilha CASCADE na listagem ---
    # Tentar campo de busca da listagem
    print("[busca] procurando 'CASCADE' ...")
    try:
        busca = page.locator("input[type='search'], input[placeholder*='Pesquise'], input[placeholder*='Busque'], input[placeholder*='Pesquisar']").first
        busca.fill("CASCADE", timeout=8000)
        page.wait_for_timeout(3500)
    except Exception as e:
        print(f"   sem campo de busca direto: {e}")
    snap(page, "02-busca-cascade")

    # Dump de todos os cards/rows que mencionam CASCADE ou Trilha, com links
    candidatos = page.evaluate(
        """() => {
            const out = [];
            const seen = new Set();
            document.querySelectorAll('a, [onclick], tr, [class*="card"]').forEach(el => {
                const txt = (el.innerText || '').trim();
                if (!txt) return;
                if (!/cascade/i.test(txt) && !/trilha/i.test(txt)) return;
                const href = el.href || el.getAttribute('href') || '';
                const id = el.id || '';
                const key = txt.slice(0,60) + '|' + href;
                if (seen.has(key)) return;
                seen.add(key);
                out.push({ tag: el.tagName, txt: txt.slice(0,120), href, id });
            });
            return out.slice(0, 40);
        }"""
    )
    print(f"[busca] {len(candidatos)} candidatos com CASCADE/Trilha:")
    for c in candidatos:
        print(f"   <{c['tag']}> id={c['id']!r} href={c['href']!r}")
        print(f"        txt={c['txt']!r}")

    # salvar dump
    (PASTA / "_candidatos.txt").write_text(
        "\n".join(f"{c['tag']} | id={c['id']} | href={c['href']}\n  {c['txt']}" for c in candidatos),
        encoding="utf-8",
    )

    dispensar_nps()

    # --- Abrir o menu more_vert (3 pontos) da linha da trilha (JS click) ---
    print("[abrir] abrindo menu more_vert da linha da trilha CASCADE ...")
    abriu = page.evaluate(
        """() => {
            // achar a TR que contem 'Trilha para CASCADE'
            const rows = Array.from(document.querySelectorAll('tr'));
            const row = rows.find(r => /Trilha para CASCADE/.test(r.innerText||''));
            if (!row) return 'sem-row';
            // dentro da row, achar o icone/botao more_vert
            const cands = Array.from(row.querySelectorAll('*')).filter(el =>
                /^more_vert$/.test((el.textContent||'').trim()) ||
                /more/i.test(el.className||'') ||
                el.getAttribute && el.getAttribute('aria-haspopup'));
            const alvo = cands[cands.length-1];
            if (!alvo) return 'sem-kebab';
            alvo.click();
            return 'ok';
        }"""
    )
    print(f"   abrir kebab: {abriu}")
    page.wait_for_timeout(1800)
    snap(page, "03-menu-morevert")

    # Dump das opcoes do menu aberto
    opcoes = page.evaluate(
        """() => {
            const out = [];
            document.querySelectorAll('a, button, li, [role=menuitem]').forEach(el => {
                const t = (el.innerText||'').trim();
                if (!t || t.length > 40) return;
                if (el.offsetParent === null) return;
                if (/aprendizagem|inscri|participante|relat|desempenho/i.test(t)) {
                    out.push({tag: el.tagName, txt: t, href: el.href||''});
                }
            });
            return out.slice(0,30);
        }"""
    )
    print(f"[menu] {len(opcoes)} opcoes relevantes:")
    for a in opcoes:
        print(f"   <{a['tag']}> {a['txt'][:40]!r} href={a['href']!r}")

    # --- Localizar o BUTTON 'monitoring Aprendizagem' do DROPDOWN e clicar no centro (mouse) ---
    box = page.evaluate(
        """() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const alvo = btns.find(el => {
                if (el.offsetParent === null) return false;
                if (el.closest('aside, nav, .sidebar, [class*="sidebar"], [class*="Sidebar"]')) return false;
                const t = (el.textContent||'').replace(/\\s+/g,' ').trim();
                return /monitoring\\s*Aprendizagem/i.test(t);
            });
            if (!alvo) return null;
            const r = alvo.getBoundingClientRect();
            return {x: r.x + r.width/2, y: r.y + r.height/2};
        }"""
    )
    print(f"   box do botao dropdown Aprendizagem: {box}")

    # Clique NATIVO no menuitem do Chakra (seletor estavel data-index=4 = Aprendizagem)
    clicou_apr = "nao"
    try:
        mi = page.locator("[role=menuitem][data-index='4']").filter(has_text="Aprendizagem")
        if mi.count() == 0:
            mi = page.locator("#events-807406-custom-element-1-button-4")
        mi.first.hover(timeout=4000)
        page.wait_for_timeout(300)
        mi.first.click(timeout=6000, force=True)
        clicou_apr = "menuitem-ok"
    except Exception as e:
        print(f"   click menuitem falhou: {repr(e)[:160]}")
    print(f"   clicou Aprendizagem dropdown: {clicou_apr}")
    page.wait_for_timeout(5000)
    # Se abriu nova aba, trocar pra ela
    if len(context.pages) > 1:
        page = context.pages[-1]
        page.bring_to_front()
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        print("   [tab] trocou pra nova aba")
    dispensar_nps()
    print(f"   url apos Aprendizagem: {page.url}")
    page.wait_for_timeout(2000)
    snap(page, "04-aba-aprendizagem")

    # --- Extrair tabela de participantes (participante/progresso/desempenho/pontuacao) ---
    page.wait_for_timeout(2000)
    tabela = page.evaluate(
        """() => {
            // pega linhas que tenham um % (progresso) e tentar mapear colunas
            const rows = [];
            document.querySelectorAll('tr, [class*="row"], [class*="participant"]').forEach(r => {
                const t = (r.innerText||'').replace(/\\n+/g,' | ').trim();
                if (!t) return;
                if (/@/.test(t) && /%/.test(t)) rows.push(t.slice(0,200));
            });
            return [...new Set(rows)].slice(0,30);
        }"""
    )
    print(f"\n[tabela] {len(tabela)} linhas de participante:")
    for row in tabela:
        print(f"   {row}")
    (PASTA / "_tabela_aprendizagem.txt").write_text("\n".join(tabela), encoding="utf-8")
    snap(page, "05-tabela-final")

    page.wait_for_timeout(1500)
    print("\n[FIM] Veja evidencias/19602_desempenho_trilha/")
    context.close()
    browser.close()
