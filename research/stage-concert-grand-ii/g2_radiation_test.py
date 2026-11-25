import json
from pathlib import Path
import numpy as np
from g2_radiation import *
OUT=Path('/tmp/g2-radiation')
data=json.loads((OUT/'shapes.json').read_text());L=data['L'];W=data['W']
shapes=[{'id':'uniform'},{'id':'antisymmetric'},*data['selected']]
freq=np.array([0,100,130.81,261.63,500,1046.5,2000,3000,4000,5000,6000])
bands={'low':(freq>=100)&(freq<=500),'mid':(freq>500)&(freq<=2000),'high':(freq>2000)}
def err(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-30))
def collect(nx,ny,gauss=False):
    x,y,area=grid(L,W,nx,ny,gauss);S=shape_matrix(shapes,x,y,L,W);responses=[];geoms=[]
    for loc in LISTENERS:
        delay,weight=geometry(x,y,area,loc);geoms.append((delay,weight))
        responses.append(response(S,delay,weight,freq))
    return S,geoms,np.array(responses)
fine=collect(256,192);ind=collect(160,120,True)
# independent Gauss-Legendre quadrature: continuous reference comparison
oracle={k:err(fine[2][:,:,v],ind[2][:,:,v]) for k,v in bands.items()}
assert all(e<=.05 for e in oracle.values())
rows=[];checks=[]
for nx,ny in [(64,48),(128,96),(256,192)]:
    S,geoms,A=collect(nx,ny) if nx!=256 else fine
    errors={k:err(A[:,:,v],fine[2][:,:,v]) for k,v in bands.items()}
    checks.append(dict(kind='spatial',nx=nx,ny=ny,errors=errors,pass_=all(e<=.05 for e in errors.values())))
    delay,weight=geoms[0]
    anti=float(np.max(abs(A[0,1,:]))/np.sum(abs(S[1]*weight)))
    assert anti<1e-8
    assert A[0,0,0].real>0 and abs(A[0,0,0].imag)<1e-12
    for sr in [48000,96000]:
        for method in ['linear','cubic']:
            B=[];arrival=[]
            for j,(delay,weight) in enumerate(geoms):
                k=kernels(S,delay,weight,sr,method)
                r=kernel_response(k,sr,freq)
                B.append(r)
                assert np.max(abs(r[:,0]-A[j,:,0]))<1e-10
                first=int(np.floor(np.min(delay)*sr+.5));assert np.all(k[:,:first]==0)
                impulse=np.zeros((len(shapes),32));impulse[0,3]=1
                out=pressure(impulse,k)
                expected=np.zeros_like(out);expected[3:3+k.shape[1]]=k[0]
                assert np.max(abs(out-expected))<1e-10
                assert len(out)==32+k.shape[1]-1
                arrival.append(first/sr)
            B=np.array(B);target=A*np.exp(-1j*np.pi*freq/sr)[None,None,:]
            e={name:err(B[:,:,v],target[:,:,v]) for name,v in bands.items()}
            row=dict(nx=nx,ny=ny,sr=sr,method=method,errors=e,pass_=all(x<=.05 for x in e.values()),arrivalS=arrival,antisymmetricError=anti)
            rows.append(row)
            print('G2_RADIATION '+json.dumps(row),flush=True)
# Farther centered receiver must have reduced DC uniform pressure; mirror ports equal.
x,y,area=grid(L,W,128,96);S=shape_matrix(shapes,x,y,L,W)
d,w=geometry(x,y,area,[.7,.55,2.]);far=response(S,d,w,[0])[0,0].real
near=fine[2][0,0,0].real
assert 0<far<near
assert np.max(abs(fine[2][1,0]-fine[2][2,0]))<1e-10
# Gate: medium grid and selected fractional delay both rates; coarse is diagnostic.
spatial=next(r for r in checks if r['nx']==128)
method=next((m for m in ['linear','cubic'] if all(r['pass_'] for r in rows if r['nx']==128 and r['method']==m)),None)
gate=spatial['pass_'] and method is not None
report=dict(scope='one-way Rayleigh pressure observer, independent prescribed acceleration; no acoustic load',selectedModes=[m['frequencyHz'] for m in data['selected']],oracle=oracle,spatial=checks,rows=rows,selectedMethod=method,gate=gate,uniformNear=float(near),uniformFar=float(far))
(OUT/'report.json').write_text(json.dumps(report,indent=2))
print('G2_RADIATION_GATE '+json.dumps({k:report[k] for k in ('oracle','spatial','selectedMethod','gate','uniformNear','uniformFar')}),flush=True)
if not gate:raise SystemExit(1)
