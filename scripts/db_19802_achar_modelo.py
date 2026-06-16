# -*- coding: utf-8 -*-
"""19802 — colunas de content_templates/template_designs, formatos, e modelos com
múltiplas variantes de Corpo (org 37061 ou global)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

def cols(t):
    return [c["COLUMN_NAME"] for c in db_rc.q(
        "SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION", (t,))]

print("content_templates:", cols("content_templates"))
print("template_designs:", cols("template_designs"))

print("\n== formatos distintos em template_designs ==")
for r in db_rc.q("SELECT design_format, COUNT(*) n FROM template_designs GROUP BY design_format"):
    print(" ", r)

print("\n== amostra content_templates (org 37061 + globais) ==")
for r in db_rc.q("""SELECT * FROM content_templates
                    WHERE organization_id=37061 OR organization_id IS NULL LIMIT 15"""):
    print(" ", {k: r[k] for k in list(r)[:8]})
