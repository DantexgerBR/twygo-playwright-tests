# -*- coding: utf-8 -*-
"""Explora onde os erros 19801 (tool_use) e 19790 (DynamoDB throughput) podem
estar registrados: tabelas do postgres de logs + ai_generation_tasks no MySQL."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pglogs, db_rc

print("== [LOGS PG] tabelas copilot/generation/ai/error/tool/checkpoint/studio ==")
try:
    for r in pglogs.q("""SELECT table_name FROM information_schema.tables
                         WHERE table_schema='public' AND (
                           table_name ILIKE %s OR table_name ILIKE %s OR table_name ILIKE %s
                           OR table_name ILIKE %s OR table_name ILIKE %s OR table_name ILIKE %s)
                         ORDER BY table_name""",
                       ("%copilot%", "%generation%", "%error%", "%tool%", "%checkpoint%", "%studio%")):
        print("  ", r["table_name"])
except Exception as e:
    print("  erro:", e)

print("\n== [MySQL] ai_generation_tasks: colunas ==")
try:
    cols = db_rc.q("SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='ai_generation_tasks' ORDER BY ORDINAL_POSITION")
    print("  ", [c["COLUMN_NAME"] for c in cols])
except Exception as e:
    print("  erro:", e)

print("\n== [MySQL] tabelas com 'generation' ou 'copilot' ==")
try:
    for r in db_rc.q("""SELECT TABLE_NAME, TABLE_ROWS FROM information_schema.tables
                        WHERE TABLE_SCHEMA=DATABASE() AND (TABLE_NAME LIKE %s OR TABLE_NAME LIKE %s)
                        ORDER BY TABLE_NAME""", ("%generation%", "%copilot%")):
        print(f"   {r['TABLE_NAME']} ~{r['TABLE_ROWS']} rows")
except Exception as e:
    print("  erro:", e)
