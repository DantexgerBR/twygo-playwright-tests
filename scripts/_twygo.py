"""_twygo.py — utilitários compartilhados dos scripts de validação QA Twygo.

Centraliza o que os scripts repetiam (login, switch admin, dispensar NPS, abrir
kebab/menu Chakra, extrair a tabela de Aprendizagem) e tira credenciais do código:
tudo vem do .env (veja .env.example). Import nos scripts:

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))  # garante scripts/ no path
    import _twygo as tw

    c = tw.cfg("RECERT")                       # {base_url, org_id, email, senha}
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        tw.login(page, c)                      # loga + troca pra admin
        tw.ir_learning(page, c, "807406")
        linhas = tw.extrair_tabela(page)
        ...
        ctx.close(); browser.close()
"""
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright  # re-exportado p/ conveniência

# Console pt-BR (cp1252) quebra ao imprimir acentos/superscripts vindos do stage.
# Reconfigura stdout/stderr pra utf-8 (com replace) — imune a console encoding.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

__all__ = [
    "ROOT", "sync_playwright", "cfg", "nova_pagina", "snap", "dispensar_nps",
    "login", "ir_learning", "abrir_kebab", "menu_visivel", "click_menuitem",
    "item_reinscricao", "item_bloqueado_por_cor", "extrair_tabela",
]


# --------------------------------------------------------------------------- #
# Config (sem credencial hardcoded — tudo do .env)
# --------------------------------------------------------------------------- #
def cfg(prefix: str = "") -> dict:
    """Lê base_url/org_id/email/senha do .env.

    prefix="" → BASE_URL / ORG_ID / ADMIN_EMAIL / ADMIN_PASSWORD (org principal).
    prefix="RECERT" → RECERT_BASE_URL / RECERT_ORG_ID / RECERT_EMAIL / RECERT_SENHA.
    prefix="EDUAPI" → EDUAPI_*.
    """
    if prefix:
        p = prefix + "_"
        base = os.environ.get(p + "BASE_URL")
        org = os.environ.get(p + "ORG_ID")
        email = os.environ.get(p + "EMAIL")
        senha = os.environ.get(p + "SENHA")
    else:
        base = os.environ.get("BASE_URL")
        org = os.environ.get("ORG_ID")
        email = os.environ.get("ADMIN_EMAIL")
        senha = os.environ.get("ADMIN_PASSWORD")
    faltam = [k for k, v in {"base_url": base, "email": email, "senha": senha}.items() if not v]
    if faltam:
        raise SystemExit(
            f"[_twygo] faltam no .env (perfil '{prefix or 'principal'}'): {faltam}. Veja .env.example"
        )
    return {"base_url": base.rstrip("/"), "org_id": org, "email": email, "senha": senha}


# --------------------------------------------------------------------------- #
# Browser / página
# --------------------------------------------------------------------------- #
def nova_pagina(p, headless: bool = False, slow_mo: int = 350, width: int = 1500, height: int = 950):
    """Cria browser+context+page com os defaults do projeto (pt-BR, viewport amplo)."""
    browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
    ctx = browser.new_context(viewport={"width": width, "height": height}, locale="pt-BR")
    return browser, ctx, ctx.new_page()


def snap(page, pasta, nome: str, full: bool = False):
    """Screenshot em <pasta>/<nome>.png (cria a pasta). Retorna o Path."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    fp = pasta / f"{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")
    return fp


def dispensar_nps(page):
    """Fecha a modal de NPS / modais bloqueantes, se aparecerem."""
    for sel in ["button:has-text('Pergunte depois')", ".chakra-modal__close-btn", "[aria-label='Close']"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible():
                b.click(timeout=1500)
                page.wait_for_timeout(500)
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# Login + navegação
# --------------------------------------------------------------------------- #
def login(page, c: dict, admin: bool = True) -> str:
    """Loga e, se admin=True e houver org_id, troca pro perfil admin da org.

    Twygo cai em /dashboard_students após login; o switch admin é obrigatório.
    Aborta se a sessão cair em /login (credencial errada / sessão concorrente).
    """
    page.goto(f"{c['base_url']}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", c["email"])
    page.fill("#user_password", c["senha"])
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    if admin and c.get("org_id"):
        page.goto(
            f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
            wait_until="domcontentloaded", timeout=30000,
        )
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(3000)
    dispensar_nps(page)
    if "/users/login" in page.url:
        raise SystemExit(f"[_twygo] sessão inválida (login concorrente?): {page.url}")
    return page.url


def ir_learning(page, c: dict, evento_id: str):
    """Vai direto pra aba Aprendizagem (learning) de um conteúdo: /e/{id}/learning."""
    page.goto(f"{c['base_url']}/e/{evento_id}/learning", wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(4000)
    dispensar_nps(page)


# --------------------------------------------------------------------------- #
# Kebab / menu Chakra (o Chakra monta TODOS os menus; só 1 fica visível)
# --------------------------------------------------------------------------- #
# JS reutilizável: pega o [role=menu] realmente aberto (visibility:visible + opacity~1)
_JS_MENU_VISIVEL = (
    "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
    "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;})"
)


def abrir_kebab(page, row_locator):
    """Abre o kebab (td com texto 'more_vert') de uma linha <tr> (clique NATIVO)."""
    row_locator.locator("td", has_text="more_vert").last.click(timeout=5000, force=True)
    page.wait_for_timeout(1200)


def menu_visivel(page):
    """Itens (texto) do menu Chakra atualmente aberto — útil pra depurar."""
    return page.evaluate(
        "()=>{const ms=" + _JS_MENU_VISIVEL + ";const m=ms[ms.length-1];return m?"
        "Array.from(m.querySelectorAll('[role=menuitem]')).map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()):[];}"
    )


def click_menuitem(page, texto: str) -> bool:
    """Clica, pelo id exato, no menuitem do menu VISÍVEL cujo texto casa com `texto`
    (regex, case-insensitive). Evita acertar item de menu oculto (stale)."""
    rid = page.evaluate(
        "(pal)=>{const ms=" + _JS_MENU_VISIVEL + ";const m=ms[ms.length-1];if(!m)return '';"
        "const it=Array.from(m.querySelectorAll('[role=menuitem]'))"
        ".find(e=>new RegExp(pal,'i').test(e.innerText||''));return it?it.id:'';}",
        texto,
    )
    if not rid:
        return False
    try:
        page.locator(f'[id="{rid}"]').click(timeout=4000)
        return True
    except Exception:
        return False


def item_reinscricao(page) -> dict:
    """Lê o item 'Iniciar reinscrição' (ícone data-icon=replay) do menu visível:
    {achou, texto, corIcone, id}. Use item_bloqueado_por_cor(corIcone) p/ saber se
    está bloqueado (ícone cinza) ou habilitado (azul)."""
    return page.evaluate(
        "()=>{const ms=" + _JS_MENU_VISIVEL + ";const m=ms[ms.length-1];if(!m)return {achou:false};"
        "const items=Array.from(m.querySelectorAll('[role=menuitem]'));"
        "const el=items.find(it=>it.querySelector('[data-icon=\"replay\"]')||/reinscri/i.test(it.innerText||''));"
        "if(!el)return {achou:false};el.scrollIntoView({block:'center'});"
        "const ic=el.querySelector('[data-icon=\"replay\"]');"
        "return {achou:true,texto:(el.innerText||'').replace(/\\s+/g,' ').trim(),id:el.id,"
        "corIcone:ic?getComputedStyle(ic).color:null};}"
    )


def item_bloqueado_por_cor(cor_rgb: str) -> bool:
    """True se a cor é cinza (R≈G≈B) = item bloqueado/disabled. Azul = habilitado."""
    m = re.findall(r"\d+", cor_rgb or "")
    return len(m) >= 3 and abs(int(m[0]) - int(m[1])) < 12 and abs(int(m[1]) - int(m[2])) < 12


# --------------------------------------------------------------------------- #
# Extração da tabela de Aprendizagem (colunas mapeadas pelo CABEÇALHO, não regex)
# --------------------------------------------------------------------------- #
def extrair_tabela(page, filtro_email: str = None) -> list:
    """Extrai as linhas tr[data-item-id] mapeando colunas pelo cabeçalho.

    Retorna [{itemId, email, progresso, desempenho, pontuacao, certificado, aprovado}].
    `filtro_email` restringe a um participante. Mapear por cabeçalho evita o erro de
    regex que atribui valor à coluna errada.
    """
    return page.evaluate(
        r"""(filtro)=>{
            const heads=Array.from(document.querySelectorAll('thead th,thead td')).map(h=>(h.innerText||'').replace(/\s+/g,' ').trim());
            const iP=heads.findIndex(h=>/Progresso/i.test(h)), iD=heads.findIndex(h=>/Desempenho/i.test(h)),
                  iPt=heads.findIndex(h=>/Pontua/i.test(h)), iC=heads.findIndex(h=>/Certificado/i.test(h));
            const out=[];
            document.querySelectorAll('tr[data-item-id]').forEach(r=>{
                const email=((r.innerText||'').match(/[\w.\-]+@[\w.\-]+/)||[''])[0];
                if(filtro && email!==filtro) return;
                const tds=Array.from(r.querySelectorAll('td')).map(td=>(td.innerText||'').replace(/\s+/g,' ').trim());
                const sw=r.querySelector('input[type=checkbox]');
                out.push({itemId:r.getAttribute('data-item-id'),email,
                    progresso:iP>=0?tds[iP]:'',desempenho:iD>=0?tds[iD]:'',
                    pontuacao:iPt>=0?tds[iPt]:'',certificado:iC>=0?tds[iC]:'',
                    aprovado:sw?sw.checked:null});
            });
            return out;
        }""",
        filtro_email,
    )
