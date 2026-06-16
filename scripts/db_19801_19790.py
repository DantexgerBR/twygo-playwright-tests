# -*- coding: utf-8 -*-
"""19801 (tool_use) e 19790 (DynamoDB throughput) — checa ai_generation_tasks:
distribuição de status, erros distintos e se os erros pararam após o fix."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

print("== status das ai_generation_tasks ==")
for r in db_rc.q("SELECT status, COUNT(*) n, MIN(created_at) ini, MAX(created_at) fim FROM ai_generation_tasks GROUP BY status"):
    print(f"  {r['status']}: {r['n']} | {r['ini']} -> {r['fim']}")

print("\n== error_code distintos (tarefas com erro) ==")
for r in db_rc.q("""SELECT error_code, COUNT(*) n, MIN(created_at) ini, MAX(created_at) fim
                    FROM ai_generation_tasks WHERE error_code IS NOT NULL OR status='failed'
                    GROUP BY error_code ORDER BY n DESC"""):
    print(f"  code={r['error_code']!r}: {r['n']} | {r['ini']} -> {r['fim']}")

def busca(nome, termos):
    print(f"\n== {nome}: tarefas cujo error_message casa {termos} ==")
    like = " OR ".join(["error_message LIKE %s"] * len(termos))
    rows = db_rc.q(f"""SELECT id, status, error_code, created_at, LEFT(error_message,160) msg
                       FROM ai_generation_tasks WHERE {like}
                       ORDER BY created_at DESC LIMIT 30""", tuple(f"%{t}%" for t in termos))
    print(f"  ocorrências: {len(rows)}")
    for r in rows:
        print(f"    id={r['id']} status={r['status']} {r['created_at']} | {r['msg']}")
    if rows:
        print(f"  >>> ÚLTIMA ocorrência: {rows[0]['created_at']}")

busca("19801 tool_use", ["tool_use", "tool_result"])
busca("19790 DynamoDB", ["ProvisionedThroughput", "DynamoDb", "throughput", "checkpointer"])
