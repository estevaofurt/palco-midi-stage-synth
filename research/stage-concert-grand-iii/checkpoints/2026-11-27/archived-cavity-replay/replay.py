"""Physical archived-operator replay; no reconstruction of geometry required."""
import argparse, ast, json, time
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from scipy.signal import fftconvolve
FINE=384000
GAMMA=2*np.pi*5

def rel(a,b):
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-300))

def load_defs(root, filename, names):
    path=root/filename
    tree=ast.parse(path.read_text())
    nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),globals())

def incidence(z,idx,sc):
    p=len(idx)//2; n=30
    assert np.all(idx[:p]<80) and np.all(idx[p:]>=80)
    assert idx[p]==80 and np.all(z['mass']==0)
    area=sc[p]**2
    top=z['T'][:,idx[:p]]*np.sqrt(area)/sc[:p]
    ix=z['ix'][idx[p:]-80]
    expected=np.sqrt(area)*np.sinc((ix//n)/(2*n))*np.sinc((ix%n)/(2*n))
    np.testing.assert_allclose(sc[p:],expected,rtol=1e-13,atol=0)
    np.testing.assert_allclose(np.linalg.norm(top,axis=0),1,rtol=1e-13,atol=0)
    F=np.zeros((n*n,2*p));F[:,:p]=top;F[ix,p+np.arange(p)]=1
    F=np.repeat(F,2,axis=0);F[1::2,p:]*=-1
    return F[z['ch']],float(area)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--blocks',type=int,default=128);ap.add_argument('--ports',nargs='+',type=int,default=[6,12,24,48]);a=ap.parse_args();root=a.root
    load_defs(root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);load_defs(root,'G3_Acoplamento_Multirate/multirate.py',['basis','block_kernel']);load_defs(root,'G3_Acoplamento_Multirate/temporal.py',['cavity_markov','simulate'])
    z=np.load(root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');rows=[]
    for n in a.ports:
        if n==6:
            k=np.load(root/'G3_Exterior_Acoplamento/exterior-384000.npz');h=np.load(root/'G3_Exterior_Acoplamento/receiver-384000.npz');K,H=k['K'],h['K'];np.testing.assert_array_equal(k['idx'],h['idx']);np.testing.assert_array_equal(k['scale'],h['scale'])
        else:
            k=np.load(root/('G3_Acoplamento_Multirate/expanded-kernels.npz' if n==12 else f'G3_Multirate_Expansao/ports{n}.npz'));K,H=k['K'],k['H']
        B,area=incidence(z,k['idx'],k['scale']);c=Cavity(z['lam'],z['res'],B,FINE);e=c.check();print('ports',n,'area',area,'modal expm',e,flush=True)
        assert e<1e-10
        for d in ([2,3] if n<=12 else [3]):
            for kind in ('noise','pulse','high'):
                row=simulate(c,K,H,8,d,kind,N=a.blocks);row.update(ports=n,cell_area=area,expm=e);rows.append(row);print(row,flush=True)
                Path(__file__).with_name('results.json').write_text(json.dumps(rows,indent=2))
    for row in rows:
        assert max(row[k] for k in ['energy_residual','work_residual','continuity','cavity_replay','receiver_replay'])<1e-10,row
        assert min(row[k] for k in ['min_inside','min_outside','min_total'])>=-1e-10,row
    print('PASS',len(rows),'trials',flush=True)
if __name__=='__main__':main()
