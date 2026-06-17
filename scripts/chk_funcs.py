import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c = tw.cfg("MIGR"); org = c["org_id"]; base = c["base_url"].rstrip("/")
with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    pg.goto(base+f"/o/{org}/succession_people_analysis", wait_until="domcontentloaded", timeout=25000); pg.wait_for_timeout(1500)
    data = pg.evaluate(r"""async (org)=>{const res=await fetch('/api/v1/o/'+org+'/succession_people_analysis?page=1&per_page=50',{headers:{'Accept':'application/json'}});return await res.json();}""", org)
    ppl = data["data"]["succession_people_analysis"]
    com_func = [p for p in ppl if p.get("organization_chart_roles")]
    com_mgr = [p for p in ppl if p.get("manager_id")]
    print(f"total pessoas: {len(ppl)}", flush=True)
    print(f"com funcao (organization_chart_roles): {len(com_func)}", flush=True)
    for p in com_func[:5]: print("  ", p["name"], "->", [r.get("name") for r in p["organization_chart_roles"]], flush=True)
    print(f"com manager: {len(com_mgr)}", flush=True)
    for p in com_mgr[:5]: print("  ", p["name"], "mgr=", p.get("manager_name"), p.get("manager_id"), flush=True)
    ctx.close(); b.close()
