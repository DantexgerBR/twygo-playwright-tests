# -*- coding: utf-8 -*-
"""Conexão read-only ao postgres de logs (twygo-logs-staging)."""
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

def conn():
    return psycopg.connect(
        host=os.environ["PGLOGS_HOST"],
        port=int(os.environ.get("PGLOGS_PORT", "5432")),
        dbname=os.environ["PGLOGS_DB"],
        user=os.environ["PGLOGS_USER"],
        password=os.environ["PGLOGS_PASS"],
        connect_timeout=15,
        autocommit=True,
    )

def q(sql, args=None):
    with conn() as c, c.cursor() as cur:
        cur.execute(sql, args or ())
        cols = [d[0] for d in cur.description] if cur.description else []
        return [dict(zip(cols, row)) for row in cur.fetchall()]

if __name__ == "__main__":
    print("[1] versão:", q("SELECT version() v")[0]["v"][:40])
    print("[2] tabelas (schema public):")
    for r in q("""SELECT table_name FROM information_schema.tables
                  WHERE table_schema='public' ORDER BY table_name LIMIT 40"""):
        print("   ", r["table_name"])
