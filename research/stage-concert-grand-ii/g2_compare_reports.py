"""Compare reports without equating performance levels or mic response."""
import argparse,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument("c5",type=Path);p.add_argument("iowa",type=Path);p.add_argument("out",type=Path);a=p.parse_args()
    c=json.loads(a.c5.read_text());s=json.loads(a.iowa.read_text())
    cidx={(x["note"],x["layer"]):x for x in c["cases"]}
    sidx={(x["note"],x["dynamic"]):x for x in s["cases"]}
    assert len(cidx)==len(sidx)==15
    rows=[]
    for n in range(3,8):
        for v,l in [("pp",1),("mf",8),("ff",16)]:
            row={"note":f"C{n}","nominal_level":v}
            for name,x in [("c5",cidx[(f"C{n}",l)]),("iowa",sidx[(f"C{n}",v)])]:
                det=x["onset_diagnostics"];assert "rms-v2" in det["method"]
                w=x["windows"];ref=w["0.02-0.08"]["rms_dbfs"]
                row[name]={"onset":det,"relative_rms_db":{k:v["rms_dbfs"]-ref for k,v in w.items()},"partials_body_db":w.get("0.25-0.75",{}).get("partial_band_relative_db"),"early_low_pct":w.get("0-0.02",{}).get("below_0_7_f0_pct")}
            rows.append(row)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps({"scope":"descriptive comparison, levels not physically matched; flagged attacks need review; late windows may be noise or release", "rows":rows},indent=2,allow_nan=False))
    for r in rows:print("G2_COMPARE "+json.dumps(r),flush=True)
if __name__=="__main__":main()
