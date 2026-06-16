# -*- coding: utf-8 -*-
"""19802 — encontra tabelas de modelos/templates/designs e um modelo (org 37061,
lesson) cujo formato Corpo tenha MÚLTIPLAS variantes de design."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_rc

print("== tabelas model/template/design ==")
for r in db_rc.q("""SELECT TABLE_NAME, TABLE_ROWS FROM information_schema.tables
                    WHERE TABLE_SCHEMA=DATABASE() AND (TABLE_NAME LIKE %s OR TABLE_NAME LIKE %s OR TABLE_NAME LIKE %s)
                    ORDER BY TABLE_NAME""", ("%model%", "%template%", "%design%")):
    print(f"  {r['TABLE_NAME']} ~{r['TABLE_ROWS']} rows")
