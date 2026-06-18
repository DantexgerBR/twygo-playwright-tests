"""retrabalho_ia_registros_18120.py — Valida o "Preencher com IA" do form de
Registro externo (Aprendizagem > Registros) no STAGE principal (org 36675).
A org 36675 tem creditos de IA (goatwy/36676 esta zerada).

Bug 18120: o "Preencher com IA" não puxava nenhum dado.
Cenário A: upload de certificado PNG (gerado aqui) -> IA preenche campos.
Cenário B: link do YouTube -> IA preenche campos.

Critérios CRÍTICOS (A): Nome (Conteúdo) + Carga horária preenchidos.
Critério (B): pelo menos alguma info puxada.

Rodar pelo venv: python scripts/retrabalho_ia_registros_18120.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "ia_registros_18120"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)
CERT_PNG = EVID / "certificado_teste.png"
RESULTADO_TXT = EVID / "resultado_dom.txt"

LINHAS_LOG = []


def log(msg):
    print(msg)
    LINHAS_LOG.append(str(msg))


CERT_HTML = """
<!DOCTYPE html><html lang="pt-br"><head><meta charset="utf-8">
<style>
  html,body{margin:0;padding:0;}
  .cert{width:1100px;height:780px;background:#fffdf7;border:14px double #b8860b;
        box-sizing:border-box;padding:70px 80px;font-family:Georgia,'Times New Roman',serif;
        color:#222;text-align:center;}
  .cert h1{font-size:64px;letter-spacing:10px;color:#8a6d00;margin:10px 0 40px;}
  .cert .corpo{font-size:30px;line-height:1.7;margin:30px 40px;}
  .cert .nome{font-size:40px;font-weight:bold;color:#1a1a1a;}
  .cert .meta{font-size:26px;margin-top:50px;line-height:1.9;}
  .cert .assina{margin-top:70px;font-size:24px;}
</style></head>
<body>
  <div class="cert">
    <h1>CERTIFICADO</h1>
    <div class="corpo">
      Certificamos que <span class="nome">Joao da Silva</span> concluiu com
      aproveitamento o curso de <b>Lideranca Agil e Gestao de Times</b>.
    </div>
    <div class="meta">
      Carga horaria: 480 minutos<br>
      Emitido em 15/03/2024
    </div>
    <div class="assina">_____________________________<br>Coordenacao Academica</div>
  </div>
</body></html>
"""


def gerar_certificado(page):
    """Renderiza o HTML do certificado e salva como PNG legivel."""
    page.set_content(CERT_HTML, wait_until="load")
    el = page.locator(".cert")
    el.screenshot(path=str(CERT_PNG))
    log(f"[cert] gerado: {CERT_PNG.name}")


def abrir_form(page, c):
    """Abre o form 'Novo conteudo externo' direto pela URL."""
    page.goto(f"{c['base_url']}/o/{c['org_id']}/records/new",
              wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)


def ler_campos(page, etapa=""):
    """Le os valores dos campos do form via DOM e retorna dict."""
    dados = page.evaluate(
        r"""() => {
            const out = {};
            // helper: valor de input por seletor
            const v = (sel)=>{const e=document.querySelector(sel);return e?(e.value||''):null;};
            out.workload_seconds = v('#workload_seconds');
            out.startDate = v('#startDate');
            out.endDate = v('#endDate');
            out.approvalDate = v('#approvalDate');
            out.certificateDate = v('#certificateDate');
            out.expirationDate = v('#expirationDate');

            // Conteudo (nome): input cujo placeholder fala em "nome do conteudo"
            let nome = null;
            document.querySelectorAll('input').forEach(i=>{
                const ph=(i.getAttribute('placeholder')||'').toLowerCase();
                if(ph.includes('nome do conte')) nome = i.value||'';
            });
            out.conteudo_nome = nome;

            // Descricao (textarea)
            const ta = document.querySelector('textarea');
            out.descricao = ta ? (ta.value||'') : null;

            // react-select: pega os valores selecionados (single-value / multi-value)
            const singles = Array.from(document.querySelectorAll('[class*="-singleValue"]'))
                .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean);
            const multis = Array.from(document.querySelectorAll('[class*="-multiValue"]'))
                .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean);
            out.selects_single = singles;
            out.selects_multi = multis;

            // Website
            let website=null;
            document.querySelectorAll('input').forEach(i=>{
                const ph=(i.getAttribute('placeholder')||'').toLowerCase();
                if(ph.includes('exemplo.com')||ph.includes('http')) website=i.value||'';
            });
            out.website = website;
            return out;
        }"""
    )
    log(f"\n===== CAMPOS LIDOS {etapa} =====")
    for k, val in dados.items():
        log(f"  {k}: {val!r}")
    return dados


def ler_modal_bloqueio(page):
    """Detecta modal de bloqueio (ex.: 'Limite de creditos atingido') apos o clique."""
    return page.evaluate(
        r"""() => {
            const dlgs = Array.from(document.querySelectorAll('[role=dialog],[role=alertdialog],.chakra-modal__content'))
                .filter(d=>{const c=getComputedStyle(d);return c.visibility!=='hidden'&&c.display!=='none';});
            if(!dlgs.length) return null;
            const d = dlgs[dlgs.length-1];
            return (d.innerText||'').replace(/\s+/g,' ').trim().slice(0,300);
        }"""
    )


def clicar_preencher_ia(page):
    """Clica no botao 'Preencher com IA'."""
    btn = page.get_by_role("button", name=re.compile("Preencher com IA", re.I)).first
    if not btn.count():
        # fallback: qualquer elemento clicavel com o texto
        btn = page.get_by_text(re.compile("Preencher com IA", re.I)).first
    btn.scroll_into_view_if_needed()
    btn.click(timeout=8000)
    log("[ia] cliquei em 'Preencher com IA'")


_JS_SNAPSHOT = r"""() => {
    const v=(s)=>{const e=document.querySelector(s);return e?(e.value||''):'';};
    let nome='';
    document.querySelectorAll('input').forEach(i=>{
        const ph=(i.getAttribute('placeholder')||'').toLowerCase();
        if(ph.includes('nome do conte')) nome=i.value||'';
    });
    const ta=document.querySelector('textarea');
    const singles=Array.from(document.querySelectorAll('[class*="-singleValue"]')).map(e=>e.innerText||'').join('|');
    const multis=Array.from(document.querySelectorAll('[class*="-multiValue"]')).map(e=>e.innerText||'').join('|');
    return [nome, v('#workload_seconds'), ta?ta.value:'', singles, multis,
            v('#certificateDate'), v('#startDate')].join('###');
}"""


def snapshot(page):
    return page.evaluate(_JS_SNAPSHOT)


def aguardar_ia(page, baseline, timeout_s=120):
    """Polling: aguarda QUALQUER campo relevante mudar em relacao ao baseline."""
    import time
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        page.wait_for_timeout(3000)
        atual = snapshot(page)
        if atual != baseline:
            log(f"[ia] form mudou apos {int(time.time()-t0)}s")
            page.wait_for_timeout(5000)  # deixa os demais campos assentarem
            return True
    log(f"[ia] timeout {timeout_s}s — nenhum campo relevante mudou")
    return False


def main():
    c = tw.cfg("")  # org principal 36675 (tem creditos de IA)
    log(f"[cfg] base={c['base_url']} org={c['org_id']} email={c['email']}")

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)

        # gerar o certificado primeiro (usa a propria page antes do login)
        gerar_certificado(page)

        log("[login] logando + switch admin...")
        tw.login(page, c)
        log(f"[login] url atual: {page.url}")

        # ---------------- CENARIO A: ARQUIVO ----------------
        log("\n########## CENARIO A — UPLOAD DE CERTIFICADO ##########")
        abrir_form(page, c)
        tw.snap(page, EVID, "A1_form_vazio", full=True)

        # upload no input file de EVIDENCIA (#drop-zone-upload-input).
        # NAO usar .first: idx 0 e o anexo de e-mail ao admin -> botao IA fica disabled.
        page.locator("#drop-zone-upload-input").set_input_files(str(CERT_PNG))
        page.wait_for_timeout(4000)
        ia_disabled = page.evaluate(
            "()=>{const b=document.querySelector('[data-test-id=\"records-form-ai-autofill-button\"]');return b?b.disabled:null;}"
        )
        log(f"[A] botao IA disabled apos upload?: {ia_disabled}")
        tw.snap(page, EVID, "A2_pos_upload", full=True)

        base_a = ler_campos(page, "A (antes da IA)")
        snap_a = snapshot(page)
        clicar_preencher_ia(page)
        page.wait_for_timeout(2500)
        modal_a = ler_modal_bloqueio(page)
        log(f"[A] MODAL apos clique IA: {modal_a!r}")
        tw.snap(page, EVID, "A3_apos_clique_ia", full=True)

        if modal_a and "rédito" in modal_a:
            mudou_a = False
            log("[A] BLOQUEADO por limite de creditos de IA — IA nao executou.")
        else:
            mudou_a = aguardar_ia(page, snap_a, timeout_s=120)
        dados_a = ler_campos(page, "A (apos IA)")
        tw.snap(page, EVID, "A4_pos_ia_preenchido", full=True)

        # ---------------- CENARIO B: LINK YOUTUBE ----------------
        log("\n########## CENARIO B — LINK DO YOUTUBE ##########")
        abrir_form(page, c)
        page.wait_for_timeout(1500)

        # preencher Website (#website)
        page.locator("#website").fill("https://www.youtube.com/watch?v=k_rYoyLEZKg")
        log("[B] website preenchido com link do YouTube")
        page.wait_for_timeout(1500)
        ia_disabled_b = page.evaluate(
            "()=>{const b=document.querySelector('[data-test-id=\"records-form-ai-autofill-button\"]');return b?b.disabled:null;}"
        )
        log(f"[B] botao IA disabled apos preencher website?: {ia_disabled_b}")
        page.wait_for_timeout(1000)
        tw.snap(page, EVID, "B1_link_preenchido", full=True)

        base_b = ler_campos(page, "B (antes da IA)")
        snap_b = snapshot(page)
        clicar_preencher_ia(page)
        page.wait_for_timeout(2500)
        modal_b = ler_modal_bloqueio(page)
        log(f"[B] MODAL apos clique IA: {modal_b!r}")
        tw.snap(page, EVID, "B2_apos_clique_ia", full=True)

        if modal_b and "rédito" in modal_b:
            mudou_b = False
            log("[B] BLOQUEADO por limite de creditos de IA — IA nao executou.")
        else:
            mudou_b = aguardar_ia(page, snap_b, timeout_s=120)
        dados_b = ler_campos(page, "B (apos IA)")
        tw.snap(page, EVID, "B3_pos_ia_preenchido", full=True)

        # ---------------- RESUMO ----------------
        log("\n########## RESUMO ##########")
        log(f"[A] IA respondeu (mudou campo)?: {mudou_a}")
        log(f"[A] Nome/Conteudo: {dados_a.get('conteudo_nome')!r}")
        log(f"[A] Carga horaria (#workload_seconds): {dados_a.get('workload_seconds')!r}")
        log(f"[A] selects single: {dados_a.get('selects_single')}")
        log(f"[A] selects multi: {dados_a.get('selects_multi')}")
        log(f"[A] datas: cert={dados_a.get('certificateDate')!r} start={dados_a.get('startDate')!r} "
            f"end={dados_a.get('endDate')!r} approval={dados_a.get('approvalDate')!r} exp={dados_a.get('expirationDate')!r}")
        log(f"[B] IA respondeu (mudou campo)?: {mudou_b}")
        log(f"[B] Nome/Conteudo: {dados_b.get('conteudo_nome')!r}")
        log(f"[B] Carga horaria: {dados_b.get('workload_seconds')!r}")
        log(f"[B] selects single: {dados_b.get('selects_single')}")
        log(f"[B] descricao: {dados_b.get('descricao')!r}")

        RESULTADO_TXT.write_text("\n".join(LINHAS_LOG), encoding="utf-8")
        log(f"\n[ok] resultado salvo em {RESULTADO_TXT}")

        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
