# -*- coding: utf-8 -*-
"""19802 — procura content_templates (qualquer org) com MÚLTIPLAS variantes de
body, pra localizar onde dá pra testar a rotação do fix #374."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

print("== templates com >1 variante de body (qualquer org) ==")
rows = db_rc.q("""SELECT td.content_template_id tid, ct.organization_id org, ct.event_id ev,
                         COUNT(*) nbody
                  FROM template_designs td
                  JOIN content_templates ct ON ct.id = td.content_template_id
                  WHERE td.design_format='body'
                  GROUP BY td.content_template_id, ct.organization_id, ct.event_id
                  HAVING nbody > 1
                  ORDER BY nbody DESC LIMIT 25""")
print(f"encontrados: {len(rows)}")
for r in rows:
    print(f"  template={r['tid']} org={r['org']} event={r['ev']} body_variants={r['nbody']}")

# orgs que tenho acesso (perfis .env): 37061, 36675, 19653, 37048, 36912
print("\n== desses, em orgs acessíveis (37061/36675/19653/37048/36912) ==")
acc = [r for r in rows if r["org"] in (37061, 36675, 19653, 37048, 36912)]
for r in acc:
    print(f"  template={r['tid']} org={r['org']} event={r['ev']} body_variants={r['nbody']}")
print(f"total acessível: {len(acc)}")
