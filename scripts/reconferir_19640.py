"""19640 — RECONFERIR o desempenho (alguem olhou na org e nao bateu).
Re-abre a lista de Aprendizagem fresca, mapeia colunas pelo cabecalho (TH),
extrai TODAS as linhas por data-item-id com valor exato de cada coluna, e tira
screenshot claro. Tambem captura a definicao do '?' de Desempenho.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://recertificacao-testeqa.stage.twygoead.com"
EMAIL, SENHA = "agents.claude@claude.com", "123456"
TRILHA_ID = "807406"
PASTA = ROOT / "evidencias" / "19640_pontuacao_reinscricao"


def dispensar_nps(page):
    for sel in ["button:has-text('Pergunte depois')", ".chakra-modal__close-btn", "[aria-label='Close']"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(): b.click(timeout=1500); page.wait_for_timeout(500)
        except Exception: pass


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    context = browser.new_context(viewport={"width": 1600, "height": 950}, locale="pt-BR")
    page = context.new_page()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded"); page.fill("#user_email", EMAIL)
    page.fill("#user_password", SENHA); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    page.goto(f"{BASE_URL}/e/{TRILHA_ID}/learning", wait_until="domcontentloaded", timeout=30000)
    try: page.wait_for_load_state("networkidle", timeout=15000)
    except Exception: pass
    page.wait_for_timeout(4000); dispensar_nps(page)
    print(f"[url] {page.url}")

    # mapear colunas pelo cabecalho e extrair TODAS as linhas
    dados = page.evaluate(
        r"""() => {
            const heads = Array.from(document.querySelectorAll('thead th, thead td')).map(h => (h.innerText||'').replace(/\s+/g,' ').trim());
            const idxDesemp = heads.findIndex(h => /Desempenho/i.test(h));
            const idxProg = heads.findIndex(h => /Progresso/i.test(h));
            const idxPont = heads.findIndex(h => /Pontua/i.test(h));
            const idxCert = heads.findIndex(h => /Certificado/i.test(h));
            const rows = [];
            document.querySelectorAll('tr[data-item-id]').forEach(r => {
                const tds = Array.from(r.querySelectorAll('td')).map(td => (td.innerText||'').replace(/\s+/g,' ').trim());
                const email = ((r.innerText||'').match(/[\w.\-]+@[\w.\-]+/)||[''])[0];
                rows.push({
                    itemId: r.getAttribute('data-item-id'), email,
                    progresso: tds[idxProg], desempenho: tds[idxDesemp],
                    pontuacao: tds[idxPont], certificado: tds[idxCert],
                });
            });
            return {heads, idxDesemp, idxProg, idxPont, idxCert, rows};
        }""")
    print(f"[heads] {dados['heads']}")
    print(f"[idx] prog={dados['idxProg']} desemp={dados['idxDesemp']} pont={dados['idxPont']} cert={dados['idxCert']}")
    print(f"\n[TODAS as inscricoes — {len(dados['rows'])}]:")
    for r in dados["rows"]:
        print(f"   {r['itemId']:>10} | {r['email']:30} | prog={r['progresso']:>6} | desemp={r['desempenho']:>8} | pont={r['pontuacao']:>5} | {r['certificado']}")
    print("\n[SO agents.claude]:")
    for r in dados["rows"]:
        if r["email"] == "agents.claude@claude.com":
            print(f"   {r['itemId']} -> prog={r['progresso']} desemp={r['desempenho']} pont={r['pontuacao']} cert={r['certificado']}")
    (PASTA / "_reconferencia.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    page.screenshot(path=str(PASTA / "19-reconferencia-full.png"), full_page=True)
    print("   [snap] 19-reconferencia-full.png")

    # capturar definicao do '?' de Desempenho (tooltip)
    try:
        q = page.locator("thead [data-icon], thead svg, thead button").filter(has_text="").first
        # hover no help ao lado de Desempenho
        help_icon = page.get_by_text("Desempenho", exact=False).first
        help_icon.hover(timeout=3000); page.wait_for_timeout(1500)
        tip = page.evaluate("""() => Array.from(document.querySelectorAll('[role=tooltip],.chakra-tooltip')).filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim())""")
        print(f"[tooltip desempenho] {tip}")
    except Exception as e:
        print(f"   tooltip err: {repr(e)[:80]}")

    page.wait_for_timeout(1200)
    context.close(); browser.close()
