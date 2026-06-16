# -*- coding: utf-8 -*-
"""19972 — separa tokens copilot por TTL (900 pré-fix / 3600 pós-fix) e mede o
padrão de criação PÓS-fix (3600): se esparso (~1/janela = reúso) ou em rajada."""
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

rows = db_rc.q("""SELECT id, resource_owner_id uid, created_at, expires_in ttl, revoked_at
                  FROM oauth_access_tokens WHERE application_id=1
                  ORDER BY id DESC LIMIT 300""")
rows.sort(key=lambda r: r["id"])  # cronológico

g900 = [r for r in rows if r["ttl"] == 900]
g3600 = [r for r in rows if r["ttl"] == 3600]
print(f"total={len(rows)} | ttl=900(pré-fix)={len(g900)} | ttl=3600(pós-fix)={len(g3600)}")
if g900:
    print(f"  ttl=900 período: {g900[0]['created_at']} -> {g900[-1]['created_at']}")
if g3600:
    print(f"  ttl=3600 período: {g3600[0]['created_at']} -> {g3600[-1]['created_at']}  (fix entrou ~aqui)")

def analisa(grp, nome):
    print(f"\n== {nome} ({len(grp)} tokens) — gaps por usuário ==")
    by = defaultdict(list)
    for r in grp: by[r["uid"]].append(r["created_at"])
    for uid, ts in sorted(by.items(), key=lambda kv: len(kv[1]), reverse=True):
        ts.sort()
        gaps = [(ts[i+1]-ts[i]).total_seconds() for i in range(len(ts)-1)]
        if gaps:
            curtos = sum(1 for g in gaps if g < 300)  # <5min = provável rajada/1-por-request
            print(f"  user {uid}: {len(ts)} tokens | span={(ts[-1]-ts[0]).total_seconds()/60:.0f}min | "
                  f"min_gap={min(gaps):.0f}s | mediana_gap={sorted(gaps)[len(gaps)//2]:.0f}s | gaps<5min={curtos}/{len(gaps)}")
        else:
            print(f"  user {uid}: 1 token (sem gap)")

analisa(g3600, "PÓS-FIX (ttl=3600)")

print("\n== últimos 15 tokens (mais recentes) ==")
for r in rows[-15:]:
    print(f"  id={r['id']} {r['created_at']} user={r['uid']} ttl={r['ttl']}")
