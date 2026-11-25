"""Only verify availability of the reserved Iowa holdout. Never download audio."""
import hashlib,json,tomllib,urllib.request
from pathlib import Path
m=json.loads(Path(__file__).with_name("holdout_g2.json").read_text())
u="https://huggingface.co/datasets/sondalex/university-iowa-piano-samples/resolve/"+m["iowa"]["commit"]+"/checksums.toml"
with urllib.request.urlopen(u,timeout=45) as r:raw=r.read(100001)
assert len(raw)<=100000
c=tomllib.loads(raw.decode())["sha256"]
files={p:c[p] for p in m["iowa"]["files"]}
assert len(files)==9 and all(len(v)==64 and all(x in "0123456789abcdef" for x in v) for v in files.values())
out={"metadata_only":True,"mirror_commit":m["iowa"]["commit"],"checksums_file_sha256":hashlib.sha256(raw).hexdigest(),"files":files}
Path("/tmp/g2-holdout.json").write_text(json.dumps(out,indent=2))
print("G2_HOLDOUT_METADATA "+json.dumps(out))
