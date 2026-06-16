# -*- coding: utf-8 -*-
"""19972 — analisa oauth_access_tokens da app copilot-internal (id=1) no stage:
padrão de criação por usuário (reúso vs 1-por-request) e expires_in (TTL)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

APP = 1  # copilot-internal

print("== colunas oauth_access_tokens ==")
cols = db_rc.q("SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='oauth_access_tokens' ORDER BY ORDINAL_POSITION")
print([c["COLUMN_NAME"] for c in cols])

print("\n== total de tokens da app copilot (id=1) ==")
print(db_rc.q("SELECT COUNT(*) n FROM oauth_access_tokens WHERE application_id=%s", (APP,)))

print("\n== tokens por DIA (created_at) — ver mudança de volume pós-deploy do fix ==")
for r in db_rc.q("""SELECT DATE(created_at) dia, COUNT(*) n, COUNT(DISTINCT resource_owner_id) usuarios,
                    GROUP_CONCAT(DISTINCT expires_in) ttls
                    FROM oauth_access_tokens WHERE application_id=%s
                    GROUP BY DATE(created_at) ORDER BY dia DESC LIMIT 20""", (APP,)):
    print(f"  {r['dia']}: {r['n']} tokens | {r['usuarios']} usuarios | ttls={r['ttls']}")

print("\n== top usuários por nº de tokens nas últimas 48h (bug = muitos por usuário) ==")
for r in db_rc.q("""SELECT resource_owner_id uid, COUNT(*) n,
                    MIN(created_at) primeiro, MAX(created_at) ultimo
                    FROM oauth_access_tokens
                    WHERE application_id=%s AND created_at >= NOW() - INTERVAL 48 HOUR
                    GROUP BY resource_owner_id ORDER BY n DESC LIMIT 10""", (APP,)):
    print(f"  user {r['uid']}: {r['n']} tokens | {r['primeiro']} -> {r['ultimo']}")

print("\n== detalhe: para o usuário mais ativo nas 48h, gaps entre tokens ==")
top = db_rc.q("""SELECT resource_owner_id uid FROM oauth_access_tokens
                 WHERE application_id=%s AND created_at >= NOW() - INTERVAL 48 HOUR
                 GROUP BY resource_owner_id ORDER BY COUNT(*) DESC LIMIT 1""", (APP,))
if top:
    uid = top[0]["uid"]
    rows = db_rc.q("""SELECT id, created_at, expires_in, revoked_at, scopes
                      FROM oauth_access_tokens
                      WHERE application_id=%s AND resource_owner_id=%s
                      ORDER BY created_at DESC LIMIT 25""", (APP, uid))
    print(f"  usuário {uid}: últimos {len(rows)} tokens:")
    for r in rows:
        print(f"    id={r['id']} created={r['created_at']} ttl={r['expires_in']} revoked={r['revoked_at']} scopes={r['scopes']}")
