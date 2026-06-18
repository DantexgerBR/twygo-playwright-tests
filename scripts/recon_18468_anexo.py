"""RECON anexo 18468 — anexar o doc pelo CLIPE do composer de importacao (filechooser)
e confirmar que aparece o chip do arquivo. Tambem mapeia o container das mensagens
do assistente (pra escopar deteccao de tabela/pipes). Read-ish (so anexa, nao envia).
"""
import re
import _twygo as tw

c = tw.cfg("MIGR")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "18468_recon"
DOC = tw.ROOT / "evidencias" / "18468" / "quiz_grande.docx"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{BASE}/o/{ORG}/question_lists", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    page.get_by_role("button", name=re.compile(r"Importa.{0,4}o Inteligente", re.I)).first.click(force=True)
    page.wait_for_timeout(3000)

    # composer: textarea 'Escreva uma mensagem'. O clipe fica a esquerda dele.
    composer = page.locator("textarea[placeholder*='Escreva']").first
    # achar o botao/icone de anexo (paperclip) no composer
    clip = page.locator("button:has-text('attach_file'), [class*=attach], label[for='message_attachments']")
    print(f"[clip candidatos] {clip.count()}")

    anexou = False
    # tentar via filechooser clicando no clipe (icone material 'attach_file' ou svg)
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            # clicar no elemento de clipe perto do textarea
            page.get_by_text("attach_file").first.click(timeout=3000)
        fc.value.set_files(str(DOC))
        anexou = True
        print("[anexo] via filechooser (attach_file)")
    except Exception as e:
        print(f"[anexo] falhou via attach_file: {e}")

    if not anexou:
        # fallback: todos os inputs file e setar em cada um, ver qual gera chip
        inputs = page.locator("input[type=file]")
        print(f"[inputs file total] {inputs.count()}")
        for i in range(inputs.count()):
            try:
                inputs.nth(i).set_input_files(str(DOC))
            except Exception as e:
                print(f"  input {i} erro {e}")
        page.wait_for_timeout(1500)

    page.wait_for_timeout(2500)
    tw.snap(page, PASTA, "30-pos-anexo")

    # detectar chip do arquivo (nome do doc no chat)
    tem_chip = page.evaluate(
        "(nome)=>{const t=document.body.innerText||'';return t.includes(nome)||/quiz_grande|\\.docx/i.test(t);}",
        "quiz_grande")
    print(f"[chip do arquivo visivel?] {tem_chip}")

    # mapear container das mensagens (onde a resposta do assistente renderiza)
    cont = page.evaluate(
        r"""()=>{
            // o overlay de importacao tem o header 'Agente de importacao inteligente'
            const hdr=Array.from(document.querySelectorAll('*')).find(e=>/Agente de importa/i.test((e.textContent||''))&&e.children.length<=6);
            let panel=hdr; for(let k=0;k<8&&panel;k++){ if(panel.querySelector && panel.querySelector('textarea')) break; panel=panel.parentElement; }
            const sel=panel?(panel.tagName+'.'+(panel.className||'').toString().trim().split(/\s+/).slice(0,2).join('.')):null;
            return {painel:sel};
        }""")
    print(f"[painel importacao] {cont}")

    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
