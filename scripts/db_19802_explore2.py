# -*- coding: utf-8 -*-
"""19802 — detalha o modelo 2-corpos (tpl 70/71) e mapeia como slides gerados
referenciam designs (design_editor_configs)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

def cols(t):
    return [c["COLUMN_NAME"] for c in db_rc.q(
        "SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION", (t,))]

print("design_editor_configs cols:", cols("design_editor_configs"))
print("design_editor_lesson_videos cols:", cols("design_editor_lesson_videos"))

print("\n== modelos 2-corpos no 36675 (tpl 70,71): designs ==")
for tid in (70, 71):
    ev = db_rc.q("SELECT event_id FROM content_templates WHERE id=%s", (tid,))
    nm = db_rc.q("SELECT name FROM events WHERE id=%s", (ev[0]["event_id"],)) if ev else []
    print(f"  tpl {tid}: event={ev[0]['event_id'] if ev else '?'} nome={nm[0]['name'] if nm else '?'!r}")
    for d in db_rc.q("""SELECT id, name, design_format, sequence, resource_type, resource_id
                        FROM template_designs WHERE content_template_id=%s ORDER BY design_format, sequence""", (tid,)):
        print(f"     design id={d['id']} fmt={d['design_format']} seq={d['sequence']} name={d['name']!r} res={d['resource_type']}/{d['resource_id']}")
