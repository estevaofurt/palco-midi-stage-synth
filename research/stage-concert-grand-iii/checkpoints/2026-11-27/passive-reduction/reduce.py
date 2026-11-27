"""Positive-residue per-channel aggregation; preserve inverse moment and total residue."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.fft import dctn
import replay as r
FS=384000; RATE=48000
DEV=[130.8128,329.6276,1000,2000,4000,5183.7,7851.2,12000,18000,23000]
RES=[217.9,987.4,2873.1,4672.3,6712.9,7943.6,10371,15321,21431]
def reduce(z,cut,ratio):
 l,res,ch=(z[k] for k in ('lam','res','ch'));f=np.sqrt(l)/(2*np.pi);keep=f<=cut;ii=np.flatnonzero(~keep);bins=np.floor(np.log(f[ii]/cut)/np.log(ratio)).astype(int);keys=np.c_[ch[ii],bins];u,inv=np.unique(keys,axis=0,return_inverse=True);w=np.bincount(inv,weights=res[ii]);mom=np.bincount(inv,weights=res[ii]/l[ii]);assert np.all(w>0) and np.all(mom>0)
 out=dict(lam=np.r_[l[keep],w/mom],res=np.r_[res[keep],w],ch=np.r_[ch[keep],u[:,0]])
 for k in ('T','ix','mass'):out[k]=z[k]
 return out

def moments(z):
 l,res,ch=(z[k] for k in ('lam','res','ch'));nz=l>0;return [np.bincount(ch,weights=res,minlength=1800),np.bincount(ch[nz],weights=res[nz]/l[nz],minlength=1800)]

def channels(z,fs):
 c=r.Cavity(z['lam'],z['res'],np.zeros((len(z['lam']),1)),FS);ch=z['ch'];rows=[]
 for f in fs:
  zz=np.exp(2j*np.pi*f/FS);det=(zz-c.a)*(zz-c.d)-c.b*c.c;xx=((zz-c.d)*c.g0+c.b*c.g1)/det;vv=(c.c*c.g0+(zz-c.a)*c.g1)/det;v=c.cx*xx+c.cv*vv+c.feed
  rows.append(np.bincount(ch,weights=v.real,minlength=1800)+1j*np.bincount(ch,weights=v.imag,minlength=1800))
 return np.array(rows)

def weights(A,B):
 a=dctn(A.reshape(30,30,-1),axes=(0,1),norm='ortho').reshape(900,-1);b=dctn(B.reshape(30,30,-1),axes=(0,1),norm='ortho').reshape(900,-1);F=np.repeat(np.c_[a,b],2,axis=0);F[1::2,A.shape[1]:]*=-1
 return F,(F@F.T)**2

def metric(x,y,W,Q,fs):
 out=[]
 for j,f in enumerate(fs):
  E=np.exp(2j*np.pi*np.outer(np.arange(8),f+np.arange(8)*RATE)/FS)/np.sqrt(8);T=Q.T@E
  J=np.einsum('aj,bj->abj',T,T.conj()).reshape(9,8)
  d=J@(x[j*8:j*8+8]-y[j*8:j*8+8]);ref=J@y[j*8:j*8+8]
  def norm(v):return np.sqrt(max(0,float(np.sum((v.conj()*(v@W)).real))))
  out.append(float(norm(d)/max(norm(ref),1e-300)))
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('previous',type=Path);a=ap.parse_args();out=Path(__file__).parent
 for base,manifest in [(a.root,out/'INPUT_SHA256SUMS'),(a.previous,a.previous/'SHA256SUMS')]:
  for h,name in (line.split(maxsplit=1) for line in manifest.read_text().splitlines() if line.strip()):assert hashlib.sha256((base/name).read_bytes()).hexdigest()==h,name
 r.load_defs(a.root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);z=np.load(a.root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');g=np.load(a.previous/'grid-b64.npz');F,W=weights(g['A'],g['B']);Q=g['Q'];fs=np.array(DEV+RES);freq=(fs[:,None]+np.arange(8)*RATE).ravel();ref=channels(z,freq);mom=moments(z);rows=[]
 for cut in (12000,24000,48000,96000,192000,384000):
  for ratio in (1.3,1.7,2.5):
   c=reduce(z,cut,ratio);v=channels(c,freq);e=metric(v,ref,W,Q,fs);mm=max(r.rel(x,y) for x,y in zip(moments(c),mom));assert mm<1e-12 and np.all(c['res']>0) and (c['lam']==0).sum()==1
   row=dict(cut=cut,ratio=ratio,terms=len(c['lam']),states=2*len(c['lam'])-1,dev_max=max(e[:len(DEV)]),reserved_max=max(e[len(DEV):]),moment_error=mm,errors=e);rows.append(row);print(row['cut'],row['ratio'],row['states'],row['dev_max'],row['reserved_max'],flush=True)
 eligible=[x for x in rows if x['dev_max']<=.01];best=min(eligible,key=lambda x:x['states']) if eligible else None
 if best:np.savez_compressed(out/'candidate.npz',**reduce(z,best['cut'],best['ratio']))
 (out/'screen.json').write_text(json.dumps(dict(dev=DEV,reserved=RES,rows=rows,selected=best),indent=2));print('selected',best,flush=True)
if __name__=='__main__':main()
