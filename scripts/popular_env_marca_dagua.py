r"""Automatiza a config do .env para a suíte marca_dagua: VERIFICA que o conteúdo
de vídeo com marca d'água ainda existe no stage (org principal) e popula os IDs
no .env. Só grava o que validar — nunca chuta.

IDs conhecidos (docs/casos/T-1599 e T-1600): curso 787696 / atividade 9280032
("Construindo times de alta performance" > "Novo 1"). O legado (T-1600) usa o mesmo
par (proxy via setup_t1600).

Uso: .\.venv\Scripts\python.exe scripts/popular_env_marca_dagua.py
NÃO popula ALUNO_*/destinatária/TOKEN (precisam de conta/geração que não temos).
"""
import re

import _twygo as tw

CANDIDATO_EVENTO = "787696"
CANDIDATO_ATIVIDADE = "9280032"
ENV_PATH = tw.ROOT / ".env"


def set_env_key(texto: str, chave: str, valor: str) -> str:
    """Substitui (ou adiciona) KEY=VALOR no conteúdo do .env."""
    linha = f"{chave}={valor}"
    if re.search(rf"^{re.escape(chave)}=.*$", texto, flags=re.M):
        return re.sub(rf"^{re.escape(chave)}=.*$", linha, texto, flags=re.M)
    sep = "" if texto.endswith("\n") or not texto else "\n"
    return texto + sep + linha + "\n"


def main():
    c = tw.cfg()  # org principal (BASE_URL / ADMIN_*)
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, headless=True)
        tw.login(page, c, admin=False)  # não precisa do switch p/ abrir /e/.../edit
        url = f"{c['base_url']}/e/{CANDIDATO_EVENTO}/contents/{CANDIDATO_ATIVIDADE}/edit"
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        tw.dispensar_nps(page)

        estado = page.evaluate(
            "()=>{const cb=document.querySelector('#water-mark-video-enabled');"
            "const lbl=document.querySelector(\"label.chakra-checkbox\");"
            "return {temCheckbox:!!cb, url:location.href,"
            "titulo:(document.querySelector('h1,h2,[class*=title]')||{}).innerText||''};}")
        print(f"[verify] url={estado['url']}")
        print(f"[verify] tem checkbox marca d'água: {estado['temCheckbox']}")
        ctx.close(); browser.close()

    if not estado["temCheckbox"]:
        print("\n[ABORT] o conteúdo 787696/9280032 não tem o checkbox de marca d'água "
              "(deletado/mudou no stage). NÃO gravei nada no .env. "
              "Descubra um vídeo com marca d'água e ajuste os candidatos.")
        return 1

    # válido → popular .env
    txt = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
    pares = {
        "EVENTO_ID": CANDIDATO_EVENTO,
        "ATIVIDADE_VIDEO_MARCA_DAGUA_ID": CANDIDATO_ATIVIDADE,
        "EVENTO_LEGADO_ID": CANDIDATO_EVENTO,       # proxy T-1600 (mesmo conteúdo)
        "ATIVIDADE_LEGADA_ID": CANDIDATO_ATIVIDADE,
    }
    for k, v in pares.items():
        txt = set_env_key(txt, k, v)
    ENV_PATH.write_text(txt, encoding="utf-8")
    print("\n[OK] .env atualizado com:")
    for k, v in pares.items():
        print(f"   {k}={v}")
    print("\nFalta (precisa de conta/geração — não automatizável aqui): "
          "ALUNO_EMAIL/ALUNO_PASSWORD, BASE_URL_DESTINATARIA, "
          "ADMIN_DESTINATARIA_*, TOKEN_DESTINATARIA (ORG_DESTINATARIA_ID=37018 conhecido).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
