# -*- coding: utf-8 -*-
"""19802 — conta variantes de design por formato em cada content_template do 37061,
pra escolher um modelo com MÚLTIPLAS variantes de Corpo (body)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

print("== content_templates do 37061 e contagem de designs por formato ==")
tpls = db_rc.q("""SELECT id, event_id, additional_characteristics, use_as_default_model
                  FROM content_templates WHERE organization_id=37061""")
for t in tpls:
    fmts = db_rc.q("""SELECT design_format, COUNT(*) n FROM template_designs
                      WHERE content_template_id=%s GROUP BY design_format ORDER BY design_format""", (t["id"],))
    seed = (t["additional_characteristics"] or "")[:60]
    fmt_str = ", ".join(f"{r['design_format']}={r['n']}" for r in fmts)
    nbody = next((r["n"] for r in fmts if r["design_format"] == "body"), 0)
    print(f"  template id={t['id']} event={t['event_id']} default={t['use_as_default_model']} | BODY={nbody} | {fmt_str} | {seed}")

print("\n== designs de body do melhor candidato (mais variantes) ==")
best = None; bestn = 0
for t in tpls:
    n = db_rc.q("SELECT COUNT(*) n FROM template_designs WHERE content_template_id=%s AND design_format='body'", (t["id"],))[0]["n"]
    if n > bestn: bestn = n; best = t["id"]
print(f"melhor template id={best} com {bestn} variantes de body")
if best:
    for r in db_rc.q("""SELECT id, name, sequence, resource_type, resource_id
                        FROM template_designs WHERE content_template_id=%s AND design_format='body'
                        ORDER BY sequence""", (best,)):
        print(f"  body design id={r['id']} name={r['name']!r} seq={r['sequence']} res={r['resource_type']}/{r['resource_id']}")
    ev = db_rc.q("SELECT event_id FROM content_templates WHERE id=%s", (best,))[0]["event_id"]
    print(f">>> MODELO ALVO: content_template_id={best} event_id(curso modelo)={ev} body_variants={bestn}")
