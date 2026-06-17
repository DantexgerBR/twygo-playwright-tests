# -*- coding: utf-8 -*-
"""20075 — checa no banco (twygo_db_rc) o conteudo 807533: event_contents.narrator_script
e estrutura de roteiros (slides). DEV: na Aula o roteiro e por slide, nao narrator_script."""
import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc
log = lambda *a: print(*a, flush=True)

CID = 807533

def show(title, rows):
    log(f"\n=== {title} ({len(rows)}) ===")
    for r in rows[:15]: log("  ", {k: (str(v)[:60] if v is not None else None) for k, v in r.items()})

try:
    # colunas de event_contents
    cols = db_rc.q("SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_NAME='event_contents' AND TABLE_SCHEMA=DATABASE() ORDER BY ORDINAL_POSITION")
    names = [c["COLUMN_NAME"] for c in cols]
    log("event_contents colunas:", names)
    has_ns = "narrator_script" in names
    log("tem narrator_script:", has_ns)

    # busca o conteudo por id direto e por event_id
    for sql, args, t in [
        ("SELECT * FROM event_contents WHERE id=%s", (CID,), "event_contents.id=807533"),
        ("SELECT * FROM event_contents WHERE event_id=%s LIMIT 10", (CID,), "event_contents.event_id=807533"),
    ]:
        try: show(t, db_rc.q(sql, args))
        except Exception as e: log(t, "ERRO:", str(e)[:80])

    # se achou, foca em narrator_script
    if has_ns:
        for sql, args, t in [
            ("SELECT id, event_id, kind, LENGTH(narrator_script) ns_len, LEFT(narrator_script,80) ns FROM event_contents WHERE id=%s OR event_id=%s", (CID, CID), "narrator_script de 807533"),
        ]:
            try: show(t, db_rc.q(sql, args))
            except Exception as e: log(t, "ERRO:", str(e)[:80])
except Exception as e:
    log("ERRO geral:", e); log(traceback.format_exc()[-400:])
