# -*- coding: utf-8 -*-
"""19972 — acha o usuário NOVOEST e mostra o baseline de tokens copilot (app 1)
dele (consulta por resource_owner_id, que é indexado)."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

EMAIL = os.environ["NOVOEST_EMAIL"]
print(f"[email] ...{EMAIL[-12:]}")  # não exibe email completo

# achar tabela de usuários e o id
user = None
for tab, col in [("users", "email"), ("people", "email")]:
    try:
        r = db_rc.q(f"SELECT id, email FROM {tab} WHERE email=%s LIMIT 1", (EMAIL,))
        if r:
            user = r[0]; print(f"[user] tabela={tab} id={user['id']}"); break
    except Exception as e:
        print(f"[user] {tab}: {e}")

if user:
    uid = user["id"]
    print(f"\n== tokens copilot (app 1) do usuário {uid} — por resource_owner_id (indexado) ==")
    rows = db_rc.q("""SELECT id, created_at, expires_in, revoked_at, scopes
                      FROM oauth_access_tokens
                      WHERE resource_owner_id=%s AND application_id=1
                      ORDER BY created_at DESC LIMIT 30""", (uid,))
    print(f"  total recentes listados: {len(rows)}")
    for r in rows[:30]:
        print(f"    id={r['id']} created={r['created_at']} ttl={r['expires_in']} revoked={r['revoked_at']}")
    # total geral do usuário (indexado, ok)
    tot = db_rc.q("SELECT COUNT(*) n FROM oauth_access_tokens WHERE resource_owner_id=%s AND application_id=1", (uid,))
    print(f"  TOTAL tokens copilot do usuário: {tot}")
