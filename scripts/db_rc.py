# -*- coding: utf-8 -*-
"""Helper de conexão read-only ao twygo_db_rc (MySQL). Só SELECT."""
import os, sys
from pathlib import Path
from dotenv import load_dotenv
import pymysql

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

def conn():
    return pymysql.connect(
        host=os.environ["DB_HOST_RC"],
        port=int(os.environ.get("DB_PORT_RC", "3306")),
        user=os.environ["DB_USER_RC"],
        password=os.environ["DB_PASS_RC"],
        database=os.environ["DB_NAME_RC"],
        connect_timeout=15,
        read_timeout=120,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

def q(sql, args=None):
    with conn() as c, c.cursor() as cur:
        cur.execute(sql, args or ())
        return cur.fetchall()

if __name__ == "__main__":
    print("[1] versão / db:", q("SELECT VERSION() v, DATABASE() db"))
    # tabelas oauth
    print("[2] tabelas oauth:", [r["TABLE_NAME"] for r in q(
        "SELECT TABLE_NAME FROM information_schema.tables WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME LIKE 'oauth%%'")])
    # aplicações copilot
    try:
        apps = q("SELECT id,name,uid,created_at FROM oauth_applications WHERE name LIKE %s OR name LIKE %s",
                 ("%copilot%", "%opilot%"))
        print("[3] apps copilot:", apps)
    except Exception as e:
        print("[3] erro apps:", e)
    # é stage? checar se org 37061 existe (NOVOEST stage)
    try:
        orgs = q("SELECT id,name FROM organizations WHERE id IN (37061,36675,19653) LIMIT 5")
        print("[4] orgs (37061/36675/19653 = stage):", orgs)
    except Exception as e:
        print("[4] erro orgs:", e)
