"""Screen positive modal truncation using contribution bounds and independent frequencies."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import reduce as a
import replay as r

def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('previous',type=Path);v=p.parse_args();out=Path(__file__).parent
 for base,manifest in [(v.root,out/'INPUT_SHA256SUMS'),(v.previous,v.previous/'SHA256SUMS')]:
  for h,name in (line.split(maxsplit=1) for line in manifest.read_text().splitlines() if line.strip()):assert hashlib.sha256((base/name).read_bytes()).hexdigest()==h,name
 r.load_defs(v.root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);z=np.load(v.root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');g=np.load(v.previous/'grid-b64.npz');F,W=a.weights(g['A'],g['B']);Q=g['Q'];fs=np.array(a.DEV+a.RES);freq=(fs[:,None]+np.arange(8)*a.RATE).ravel();ref=a.channels(z,freq)
 # Preserve exact low-frequency poles and mode at zero; upper bound per modal port matrix in continuous domain.
 l,res,ch=(z[k] for k in ('lam','res','ch'));f=np.sqrt(l)/(2*np.pi);score=res*np.sum(F[ch]**2,axis=1);score/=max(score);rows=[];candidates={}
 for cut in (8000,12000,24000):
  for threshold in (1e-8,1e-7,1e-6,1e-5,1e-4,1e-3):
   keep=(f<=cut)|(score>=threshold);c={k:z[k][keep] if k in ('lam','res','ch') else z[k] for k in ('lam','res','ch','T','ix','mass')};e=a.metric(a.channels(c,freq),ref,W,Q,fs);assert np.all(c['res']>0) and (c['lam']==0).sum()==1
   row=dict(cut=cut,threshold=threshold,terms=int(keep.sum()),states=2*int(keep.sum())-1,dev_max=max(e[:len(a.DEV)]),reserved_max=max(e[len(a.DEV):]),errors=e,discarded_residue_fraction=float(res[~keep].sum()/res.sum()));rows.append(row);candidates[(cut,threshold)]=keep;print(cut,threshold,row['states'],row['dev_max'],row['reserved_max'],flush=True)
 eligible=[x for x in rows if x['dev_max']<=.01];best=min(eligible,key=lambda x:x['states']) if eligible else None
 if best:
  keep=candidates[(best['cut'],best['threshold'])];np.savez_compressed(out/'candidate.npz',**{k:z[k][keep] if k in ('lam','res','ch') else z[k] for k in ('lam','res','ch','T','ix','mass')})
 (out/'prune.json').write_text(json.dumps(dict(dev=a.DEV,reserved=a.RES,rows=rows,selected=best),indent=2));print('selected',best,flush=True)
if __name__=='__main__':main()
