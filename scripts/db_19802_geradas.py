# -*- coding: utf-8 -*-
"""19802 — explora como aulas geradas guardam designs/cenas, na org 36952 (tem
modelo de múltiplos corpos). Objetivo: medir variação de design de corpo nas aulas
geradas pós-fix, 100%% via banco."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

ORG = 36952
print("== design_editor_configs recentes na org 36952 (resumo) ==")
for r in db_rc.q("""SELECT id, resource_type, resource_id, layout, scenes_quantity,
                           LENGTH(canva_content) tam_canva, is_draft, created_at
                    FROM design_editor_configs
                    WHERE organization_id=%s
                    ORDER BY created_at DESC LIMIT 20""", (ORG,)):
    print(f"  cfg id={r['id']} res={r['resource_type']}/{r['resource_id']} layout={str(r['layout'])[:25]} "
          f"cenas={r['scenes_quantity']} canva={r['tam_canva']}B draft={r['is_draft']} {r['created_at']}")

print("\n== resource_types distintos em design_editor_configs (org 36952) ==")
for r in db_rc.q("""SELECT resource_type, COUNT(*) n FROM design_editor_configs
                    WHERE organization_id=%s GROUP BY resource_type""", (ORG,)):
    print("  ", r)
