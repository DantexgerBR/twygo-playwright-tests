"""19640 — TESTE CONTROLADO pelo lado do ALUNO (muta dados, autorizado).
Conta: agents.claude (inscricao 100%/100.0%/110 na Trilha CASCADE, itemId conhecido).
Passos:
  1. ANTES (admin /e/807406/learning): registra inscricoes do agents.claude por itemId.
  2. ALUNO (/play): clica 'Reinscrever-se' no banner da trilha + confirma.
  3. DEPOIS (admin): re-extrai. A inscricao ANTERIOR (itemId 44275175, 100%/110) preservou
     seus valores (corrigido) ou foi zerada/igualada (bug)? Apareceu nova inscricao 0%?
"""
import re, json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
import _twygo as tw
_c = tw.cfg("RECERT")
BASE_URL, EMAIL, SENHA = _c["base_url"], _c["email"], _c["senha"]
TRILHA_ID = "807406"
ALVO = "agents.claude@claude.com"
PASTA = ROOT / "evidencias" / "19640_pontuacao_reinscricao"


def snap(page, nome, full=False):
    p = PASTA / f"{nome}.png"; page.screenshot(path=str(p), full_page=full); print(f"   [snap] {p.name}"); return p


def dispensar_nps(page):
    for sel in ["button:has-text('Pergunte depois')", ".chakra-modal__close-btn", "[aria-label='Close']"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(): b.click(timeout=1500); page.wait_for_timeout(500)
        except Exception: pass


def extrair(page):
    return page.evaluate(
        r"""() => {
            const out=[];
            document.querySelectorAll('tr[data-item-id]').forEach(r=>{
                const txt=(r.innerText||''); if(!/@/.test(txt)) return;
                const email=(txt.match(/[\w.\-]+@[\w.\-]+/)||[''])[0];
                const pcts=(txt.match(/(\d+(?:\.\d+)?)%/g)||[]);
                const pont=(txt.replace(/\d+(?:\.\d+)?%/g,'|').match(/\|\s*\|?\s*(\d{1,6})\b/)||['',''])[1];
                const cert=/Emitido/.test(txt)?'Emitido':/Substitu/.test(txt)?'Substituido':/Pendente/.test(txt)?'Pendente':'';
                out.push({itemId:r.getAttribute('data-item-id'),email,prog:pcts[0]||'',desemp:pcts[1]||'',pont,cert});
            });
            return out;
        }""")


def admin_learning(page):
    page.goto(f"{BASE_URL}/e/{TRILHA_ID}/learning", wait_until="domcontentloaded", timeout=30000)
    try: page.wait_for_load_state("networkidle", timeout=15000)
    except Exception: pass
    page.wait_for_timeout(4000); dispensar_nps(page)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=400)
    context = browser.new_context(viewport={"width": 1400, "height": 950}, locale="pt-BR")
    page = context.new_page()
    page.on("dialog", lambda d: (print(f"   [DIALOG] {d.type}: {d.message!r} -> accept"), d.accept()))
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded"); page.fill("#user_email", EMAIL)
    page.fill("#user_password", SENHA); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass

    # ---------- ANTES (admin) ----------
    admin_learning(page)
    antes = extrair(page)
    claude_antes = [l for l in antes if l["email"] == ALVO]
    print("[ANTES] agents.claude:")
    for l in claude_antes: print(f"   {l}")
    (PASTA / "_antes.json").write_text(json.dumps(antes, ensure_ascii=False, indent=2), encoding="utf-8")
    ids_antes = {l["itemId"] for l in claude_antes}
    naozero_antes = {l["itemId"]: l for l in claude_antes if l["pont"] not in ("", "0")}
    snap(page, "12-ANTES-admin")

    # ---------- ALUNO: Reinscrever-se ----------
    page.goto(f"{BASE_URL}/play", wait_until="domcontentloaded", timeout=30000)
    try: page.wait_for_load_state("networkidle", timeout=15000)
    except Exception: pass
    page.wait_for_timeout(3500); dispensar_nps(page)
    snap(page, "13-aluno-banner")

    print("[ALUNO] clicando 'Reinscrever-se' ...")
    clicou = False
    try:
        b = page.get_by_role("button", name=re.compile("Reinscrever", re.I)).first
        if b.count() == 0:
            b = page.get_by_text(re.compile("Reinscrever", re.I)).first
        b.click(timeout=8000)
        clicou = True
    except Exception as e:
        print(f"   click Reinscrever falhou: {repr(e)[:120]}")
    print(f"   clicou: {clicou}")
    page.wait_for_timeout(3000)
    snap(page, "14-aluno-pos-reinscrever")

    # confirmar modal se houver
    bdump = page.evaluate(
        r"""() => Array.from(document.querySelectorAll('button')).filter(b=>b.offsetParent!==null)
            .map(b=>(b.innerText||'').trim()).filter(Boolean).slice(0,20)""")
    print(f"   botoes visiveis: {bdump}")
    for nome in ["Confirmar", "Reinscrever", "Sim", "Continuar", "Iniciar", "Ok"]:
        try:
            bb = page.get_by_role("button", name=re.compile(f"^{nome}$", re.I))
            done=False
            for j in range(bb.count()):
                if bb.nth(j).is_visible(): print(f"   confirma '{nome}'"); bb.nth(j).click(timeout=4000); done=True; break
            if done: break
        except Exception: pass
    page.wait_for_timeout(4000)
    snap(page, "15-aluno-pos-confirma")

    # ---------- DEPOIS (admin) ----------
    admin_learning(page)
    depois = extrair(page)
    claude_depois = [l for l in depois if l["email"] == ALVO]
    print("\n[DEPOIS] agents.claude:")
    for l in claude_depois: print(f"   {l}")
    (PASTA / "_depois.json").write_text(json.dumps(depois, ensure_ascii=False, indent=2), encoding="utf-8")
    snap(page, "16-DEPOIS-admin")

    # ---------- VEREDITO ----------
    print("\n===== COMPARACAO =====")
    print(f"itemIds ANTES: {sorted(ids_antes)}")
    print(f"itemIds DEPOIS: {sorted({l['itemId'] for l in claude_depois})}")
    novas = [l for l in claude_depois if l["itemId"] not in ids_antes]
    print(f"NOVAS inscricoes (reinscricao criou): {[(l['itemId'],l['prog'],l['pont'],l['cert']) for l in novas]}")
    print("Imutabilidade das anteriores nao-zero:")
    for iid, l0 in naozero_antes.items():
        ld = next((x for x in claude_depois if x["itemId"]==iid), None)
        if ld is None:
            print(f"   itemId={iid}: SUMIU (era {l0['desemp']}/{l0['pont']})")
        else:
            ok = ld["pont"]==l0["pont"] and ld["desemp"]==l0["desemp"]
            print(f"   itemId={iid}: {l0['desemp']}/{l0['pont']} -> {ld['desemp']}/{ld['pont']} cert={ld['cert']} | PRESERVADO={ok}")
    if not novas:
        print("\n!! Nenhuma nova inscricao criada — reinscricao pode nao ter ocorrido (inconclusivo).")

    page.wait_for_timeout(1500)
    context.close(); browser.close()
