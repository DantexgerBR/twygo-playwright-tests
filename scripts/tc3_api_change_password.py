"""tc3_api_change_password.py — Altera senha do QA11TC3 via API Rails + CSRF correto."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
USER_ID = "4298402"
TC3_EMAIL = "qa11tc342588@twygotest.com"
TC3_NOVA_SENHA = "twygoqa2026"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def main():
    log("=" * 60)
    log("tc3_api_change_password.py")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            # Login admin na pagina de usuarios (onde ha CSRF token)
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

            # Navega para a pagina de usuarios (onde o CSRF token fica disponivel)
            page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            # Pega o CSRF token
            csrf_token = page.evaluate(
                "document.querySelector('meta[name=csrf-token]')?.content || 'NAO_ENCONTRADO'"
            )
            log(f"CSRF token obtido: {bool(csrf_token and csrf_token != 'NAO_ENCONTRADO')}")

            # Tenta varios formatos de payload para o PATCH
            payloads_to_try = [
                # Formato Rails padrao
                '{"user":{"password":"twygoqa2026","password_confirmation":"twygoqa2026"}}',
                # Formato com change_password
                '{"user":{"new_password":"twygoqa2026","new_password_confirmation":"twygoqa2026"}}',
                # Formato alternativo
                '{"password":"twygoqa2026","password_confirmation":"twygoqa2026"}',
            ]

            for payload in payloads_to_try:
                result = page.evaluate(
                    """async (args) => {
                        const {url, token, payload} = args;
                        try {
                            const resp = await fetch(url, {
                                method: 'PATCH',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRF-Token': token,
                                    'Accept': 'application/json',
                                    'X-Requested-With': 'XMLHttpRequest'
                                },
                                body: payload
                            });
                            const text = await resp.text();
                            return {status: resp.status, body: text.slice(0, 500), ok: resp.ok};
                        } catch(e) {
                            return {error: e.message};
                        }
                    }""",
                    {
                        "url": f"{BASE_URL}/o/{ORG_ID}/users/{USER_ID}",
                        "token": csrf_token,
                        "payload": payload
                    }
                )
                log(f"  PATCH payload={payload[:50]!r}: status={result.get('status')} ok={result.get('ok')}")
                if result.get("status") not in (422, 404, 401, 403):
                    log(f"    body: {result.get('body', '')[:200]}")
                if result.get("ok") or result.get("status") in (200, 201, 204):
                    log("  SUCESSO!")
                    break

            # Tenta tambem via form tradicional Rails (multipart)
            log("\nTentando via FormData com _method=patch...")
            result_form = page.evaluate(
                """async (args) => {
                    const {base, org, user_id, token, senha} = args;
                    const fd = new FormData();
                    fd.append('_method', 'patch');
                    fd.append('authenticity_token', token);
                    fd.append('user[password]', senha);
                    fd.append('user[password_confirmation]', senha);
                    try {
                        const resp = await fetch(`${base}/o/${org}/users/${user_id}`, {
                            method: 'POST',
                            headers: {'X-CSRF-Token': token, 'Accept': 'application/json'},
                            body: fd
                        });
                        const text = await resp.text();
                        return {status: resp.status, ok: resp.ok, body: text.slice(0, 400)};
                    } catch(e) {
                        return {error: e.message};
                    }
                }""",
                {
                    "base": BASE_URL, "org": ORG_ID, "user_id": USER_ID,
                    "token": csrf_token, "senha": TC3_NOVA_SENHA
                }
            )
            log(f"  FormData resultado: status={result_form.get('status')} ok={result_form.get('ok')}")
            log(f"  body: {result_form.get('body', '')[:300]}")

            # Tenta endpoint especifico de change_password que o Twygo possa ter
            log("\nTentando endpoints alternativos...")
            endpoints = [
                f"/o/{ORG_ID}/users/{USER_ID}/set_password",
                f"/o/{ORG_ID}/users/{USER_ID}/admin_change_password",
                f"/o/{ORG_ID}/professionals/{USER_ID}/change_password",
                f"/o/{ORG_ID}/users/{USER_ID}/password",
            ]
            for ep in endpoints:
                result_ep = page.evaluate(
                    """async (args) => {
                        const {url, token, senha} = args;
                        try {
                            const resp = await fetch(url, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRF-Token': token,
                                    'Accept': 'application/json'
                                },
                                body: JSON.stringify({password: senha, password_confirmation: senha})
                            });
                            return {status: resp.status};
                        } catch(e) {
                            return {error: e.message};
                        }
                    }""",
                    {"url": f"{BASE_URL}{ep}", "token": csrf_token, "senha": TC3_NOVA_SENHA}
                )
                log(f"  {ep}: status={result_ep.get('status')}")

        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("FIM")
    log("=" * 60)


if __name__ == "__main__":
    main()
