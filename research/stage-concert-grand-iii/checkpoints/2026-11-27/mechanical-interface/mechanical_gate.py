"""Necessary provenance gate, not sufficient to prove coordinate equivalence."""
import argparse, hashlib, json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();rows=[]
    for line in Path(__file__).with_name('REQUIRED_MECHANICAL.sha256').read_text().splitlines():
        h,name=line.split(maxsplit=1);f=a.root/name;state='missing' if not f.is_file() else 'verified' if hashlib.sha256(f.read_bytes()).hexdigest()==h else 'divergent';rows.append(dict(path=name,state=state))
    print(json.dumps(rows,indent=2));return 0 if all(x['state']=='verified' for x in rows) else 2
if __name__=='__main__':raise SystemExit(main())
