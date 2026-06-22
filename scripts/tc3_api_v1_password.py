"""tc3_api_v1_password.py — Tenta alterar senha do QA11TC3 via /api/v1/o/:org_id/professionals/:id."""
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
    log("tc3_api_v1_password.py")
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
            page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            csrf = page.evaluate(
                "document.querySelector('meta[name=csrf-token]')?.content || ''"
            )
            log(f"CSRF: {bool(csrf)}")

            # API v1 endpoints para alterar senha
            api_endpoints = [
                f"/api/v1/o/{ORG_ID}/professionals/{USER_ID}/change_password",
                f"/api/v1/o/{ORG_ID}/users/{USER_ID}/change_password",
                f"/api/v1/o/{ORG_ID}/professionals/{USER_ID}",
            ]

            payloads = [
                {"password": TC3_NOVA_SENHA, "password_confirmation": TC3_NOVA_SENHA},
                {"user": {"password": TC3_NOVA_SENHA, "password_confirmation": TC3_NOVA_SENHA}},
                {"professional": {"password": TC3_NOVA_SENHA, "password_confirmation": TC3_NOVA_SENHA}},
            ]

            for ep in api_endpoints:
                for payload in payloads:
                    import json
                    result = page.evaluate(
                        """async (args) => {
                            const {url, token, payload, method} = args;
                            try {
                                const resp = await fetch(url, {
                                    method: method,
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'X-CSRF-Token': token,
                                        'Accept': 'application/json',
                                        'X-Requested-With': 'XMLHttpRequest'
                                    },
                                    body: JSON.stringify(payload)
                                });
                                const text = await resp.text();
                                return {status: resp.status, body: text.slice(0, 200)};
                            } catch(e) {
                                return {error: e.message};
                            }
                        }""",
                        {
                            "url": f"{BASE_URL}{ep}",
                            "token": csrf,
                            "payload": payload,
                            "method": "POST" if "change_password" in ep else "PATCH"
                        }
                    )
                    status = result.get("status")
                    if status not in (404, 405):
                        log(f"  {ep} [{json.dumps(payload)[:30]}]: status={status}")
                        log(f"    body: {result.get('body', '')[:150]}")
                    if status in (200, 201, 204):
                        log("  *** SUCESSO! ***")

            # Tenta o endpoint que REALMENTE existe via network sniff
            # O botao "Alterar senha" no Chakra UI provavelmente chama uma rota especifica
            # Vamos tentar via fetch com os cookies da sessao atual
            log("\nTentando variantes com credentials: include...")
            result_creds = page.evaluate(
                """async (args) => {
                    const {base, org, user_id, token, senha} = args;
                    // Tenta a rota Rails que o botao provavelmente chama
                    const resp = await fetch(`${base}/o/${org}/users/${user_id}/change_password`, {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': token,
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify({
                            new_password: senha,
                            new_password_confirmation: senha,
                            user_id: user_id
                        })
                    });
                    const text = await resp.text();
                    return {status: resp.status, body: text.slice(0, 300)};
                }""",
                {"base": BASE_URL, "org": ORG_ID, "user_id": USER_ID, "token": csrf, "senha": TC3_NOVA_SENHA}
            )
            log(f"  change_password credentials:include: {result_creds}")

        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("FIM")
    log("=" * 60)


if __name__ == "__main__":
    main()
