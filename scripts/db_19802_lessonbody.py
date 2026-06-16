# -*- coding: utf-8 -*-
"""19802 — modelos com >=2 designs de CORPO do tipo Aula (resource_type=
DesignEditorConfig), que é o que a rotação do fix #374 exige p/ aula."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

print("== templates com >1 design de body resource_type=DesignEditorConfig (corpo de AULA) ==")
rows = db_rc.q("""SELECT td.content_template_id tid, ct.organization_id org, ct.event_id ev, COUNT(*) nbody
                  FROM template_designs td JOIN content_templates ct ON ct.id=td.content_template_id
                  WHERE td.design_format='body' AND td.resource_type='DesignEditorConfig'
                  GROUP BY td.content_template_id, ct.organization_id, ct.event_id
                  HAVING nbody>1 ORDER BY nbody DESC LIMIT 30""")
print(f"encontrados: {len(rows)}")
for r in rows:
    print(f"  tpl={r['tid']} org={r['org']} event={r['ev']} corpos_aula={r['nbody']}")
ACC = (37061, 36675, 19653, 37048, 36912)
acc = [r for r in rows if r["org"] in ACC]
print(f"\nacessíveis (37061/36675/19653/37048/36912): {len(acc)}")
for r in acc:
    nm = db_rc.q("SELECT name FROM events WHERE id=%s", (r["ev"],))
    print(f"  tpl={r['tid']} org={r['org']} event={r['ev']} corpos_aula={r['nbody']} nome={nm[0]['name'] if nm else '?'!r}")
