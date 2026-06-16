# -*- coding: utf-8 -*-
"""19843 — confirma no banco que o botão "Concluir geração com IA" disparou a
geração GERAL: tarefas recém-criadas (auto_approve, completion_run_id) p/ várias
atividades do curso 807533 (org 37061)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

ORG = 37061
print("== ai_generation_tasks criadas HOJE na org 37061 (últimas) ==")
rows = db_rc.q("""SELECT id, target_resource_type tgt, target_resource_id tid, artifact_type art,
                         status, error_code, auto_approve, completion_run_id crun, wave_index w, created_at
                  FROM ai_generation_tasks
                  WHERE organization_id=%s AND created_at >= NOW() - INTERVAL 30 MINUTE
                  ORDER BY created_at DESC LIMIT 80""", (ORG,))
print(f"total recém-criadas (30min): {len(rows)}")
# agrupar por completion_run_id
from collections import defaultdict
runs = defaultdict(list)
for r in rows: runs[r["crun"]].append(r)
for crun, ts in runs.items():
    alvos = set((t["tgt"], t["tid"]) for t in ts)
    auto = set(t["auto_approve"] for t in ts)
    sts = defaultdict(int)
    for t in ts: sts[(t["status"], t["error_code"])] += 1
    print(f"\n  completion_run_id={crun}: {len(ts)} tarefas | {len(alvos)} atividades-alvo | auto_approve={auto}")
    for (s, e), n in sts.items():
        print(f"     status={s} error={e}: {n}")
# amostra
print("\n  amostra de tarefas:")
for r in rows[:12]:
    print(f"    id={r['id']} alvo={r['tgt']}/{r['tid']} art={r['art']} status={r['status']} err={r['error_code']} auto={r['auto_approve']} run={r['crun']} wave={r['w']}")
