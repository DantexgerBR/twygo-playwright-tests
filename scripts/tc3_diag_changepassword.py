"""tc3_diag_changepassword.py — Diagnostica rotas de change_password e tenta API direta."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
USER_ID = "4298402"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def main():
    log("=" * 60)
    log("tc3_diag_changepassword.py")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            # Login admin
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.fill("#user_email", "dante.tavares@twygo.com")
            page.fill("#user_password", "123456")
            page.click("#user_submit")
            page.wait_for_timeout(3000)
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
                wait_until="domcontentloaded"
            )
            page.wait_for_timeout(2000)
            log(f"Admin logado: {page.url[:60]}")

            # Testa a URL change_password diretamente
            url_cp = f"{BASE_URL}/o/{ORG_ID}/users/{USER_ID}/change_password"
            page.goto(url_cp, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)
            log(f"URL change_password: {page.url[:80]}")
            log(f"Titulo: {page.title()[:60]}")

            # Verifica inputs
            inputs_info = page.evaluate(
                "Array.from(document.querySelectorAll('input')).map(i => "
                "({type: i.type, id: i.id, name: i.name, placeholder: i.placeholder, "
                "visible: i.offsetParent !== null}))"
            )
            log(f"Inputs encontrados: {len(inputs_info)}")
            for inp in inputs_info:
                log(f"  {inp}")
            tw.snap(page, EVID, "tc3_diag_change_password_url")

            # Se nao houver form de senha, tenta POST direto para definir senha
            # Twygo Rails usa CSRF token - precisa pegar o token
            csrf_token = page.evaluate(
                "document.querySelector('meta[name=csrf-token]')?.content || 'NAO_ENCONTRADO'"
            )
            log(f"CSRF token: {csrf_token[:20] if csrf_token else 'ausente'}...")

            # Tenta PUT para /o/:org_id/users/:user_id com senha
            # Formato tipico do Rails: user[password] e user[password_confirmation]
            if csrf_token and csrf_token != "NAO_ENCONTRADO":
                log("\nTentando PUT /users/:id com nova senha...")
                result = page.evaluate(
                    """async (args) => {
                        const {url, token, senha} = args;
                        const formData = new FormData();
                        formData.append('_method', 'put');
                        formData.append('authenticity_token', token);
                        formData.append('user[password]', senha);
                        formData.append('user[password_confirmation]', senha);
                        try {
                            const resp = await fetch(url, {
                                method: 'POST',
                                body: formData,
                                headers: {'X-CSRF-Token': token, 'Accept': 'application/json, text/plain, */*'}
                            });
                            const text = await resp.text();
                            return {status: resp.status, url: resp.url, body: text.slice(0, 300)};
                        } catch(e) {
                            return {error: e.message};
                        }
                    }""",
                    {
                        "url": f"{BASE_URL}/o/{ORG_ID}/users/{USER_ID}",
                        "token": csrf_token,
                        "senha": "twygoqa2026"
                    }
                )
                log(f"  Resultado PUT: {result}")

            # Tambem tenta PATCH JSON
            log("\nTentando PATCH JSON /users/:id...")
            result_patch = page.evaluate(
                """async (args) => {
                    const {url, token, senha} = args;
                    try {
                        const resp = await fetch(url, {
                            method: 'PATCH',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRF-Token': token,
                                'Accept': 'application/json'
                            },
                            body: JSON.stringify({
                                user: {password: senha, password_confirmation: senha}
                            })
                        });
                        const text = await resp.text();
                        return {status: resp.status, url: resp.url, body: text.slice(0, 300)};
                    } catch(e) {
                        return {error: e.message};
                    }
                }""",
                {
                    "url": f"{BASE_URL}/o/{ORG_ID}/users/{USER_ID}",
                    "token": csrf_token,
                    "senha": "twygoqa2026"
                }
            )
            log(f"  Resultado PATCH: {result_patch}")

            # Tenta via endpoint especifico de change_password
            log("\nTentando POST /change_password endpoint...")
            result_cp = page.evaluate(
                """async (args) => {
                    const {base, org, user_id, token, senha} = args;
                    const endpoints = [
                        `${base}/o/${org}/users/${user_id}/change_password`,
                        `${base}/o/${org}/professionals/${user_id}/change_password`,
                    ];
                    const results = [];
                    for (const url of endpoints) {
                        try {
                            const resp = await fetch(url, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRF-Token': token,
                                    'Accept': 'application/json'
                                },
                                body: JSON.stringify({
                                    password: senha,
                                    password_confirmation: senha
                                })
                            });
                            const text = await resp.text();
                            results.push({url: url, status: resp.status, body: text.slice(0, 200)});
                        } catch(e) {
                            results.push({url: url, error: e.message});
                        }
                    }
                    return results;
                }""",
                {
                    "base": BASE_URL,
                    "org": ORG_ID,
                    "user_id": USER_ID,
                    "token": csrf_token,
                    "senha": "twygoqa2026"
                }
            )
            log(f"  Resultado endpoints change_password: {result_cp}")

        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("DIAGNOSTICO CONCLUIDO")
    log("=" * 60)


if __name__ == "__main__":
    main()
