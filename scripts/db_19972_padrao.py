# -*- coding: utf-8 -*-
"""19972 — analisa os tokens copilot mais recentes (scan por id DESC, indexado)
pra ver o padrão de criação por usuário: reúso (~1/janela) vs 1-por-request."""
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

print("[..] buscando tokens copilot mais recentes por id DESC (pode demorar)")
rows = db_rc.q("""SELECT id, resource_owner_id uid, created_at, expires_in, revoked_at
                  FROM oauth_access_tokens
                  WHERE application_id=1
                  ORDER BY id DESC LIMIT 300""")
print(f"[ok] {len(rows)} tokens copilot recentes")
if rows:
    print(f"  janela: {rows[-1]['created_at']}  ->  {rows[0]['created_at']}")
    ttls = sorted(set(r["expires_in"] for r in rows))
    print(f"  expires_in distintos: {ttls}  (fix amplia p/ 3600=1h)")
    # agrupar por usuário e medir nº de tokens + menor gap entre criações
    porуser = defaultdict(list)
    for r in rows:
        porуser[r["uid"]].append(r["created_at"])
    print(f"  usuários distintos: {len(porуser)}")
    print("  top usuários por nº de tokens nessa janela (e menor gap entre tokens):")
    rank = sorted(porуser.items(), key=lambda kv: len(kv[1]), reverse=True)[:12]
    for uid, ts in rank:
        ts_sorted = sorted(ts)
        gaps = [(ts_sorted[i+1]-ts_sorted[i]).total_seconds() for i in range(len(ts_sorted)-1)]
        min_gap = min(gaps) if gaps else None
        span = (ts_sorted[-1]-ts_sorted[0]).total_seconds() if len(ts_sorted)>1 else 0
        print(f"    user {uid}: {len(ts)} tokens | span={span/60:.1f}min | menor_gap={f'{min_gap:.0f}s' if min_gap is not None else '-'}")
