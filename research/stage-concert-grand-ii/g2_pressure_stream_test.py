import json
import numpy as np
from g2_radiation import pressure
from g2_pressure_stream import PressureStream,render_blocks
rng=np.random.default_rng(9307)
rows=[]
def oracle(a,ks):
    raw=[pressure(a,k) for k in ks];n=max(map(len,raw))
    return np.stack([np.pad(x,(0,n-len(x))) for x in raw])
def check(a,ks,block,batch,id):
    y=render_blocks(a,ks,block,batch);ref=oracle(a,ks)
    assert y.shape==ref.shape and np.all(np.isfinite(y))
    scale=max(1.,float(np.max(abs(ref))))
    error=float(np.max(abs(y-ref)))
    assert error<=1e-10*scale
    for j,k in enumerate(ks):
        nz=np.flatnonzero(np.any(k!=0,axis=0))
        if len(nz):assert np.all(y[j,:nz[0]]==0)
        else:assert np.all(y[j]==0)
    rows.append(dict(id=id,modes=a.shape[0],samples=a.shape[1],block=block,batch=batch,maxError=error))
a=rng.normal(size=(7,293))
ks=[rng.normal(size=(7,n)) for n in (31,53,39)]
for k,d in zip(ks,(10,13,9)):k[:,:d]=0
for block in (1,8,31,64,128,512):check(a,ks,block,3,'random')
for block in (4,32,64):
    impulse=np.zeros((7,85));impulse[3,17]=1.
    check(impulse,ks,block,2,'impulse')
check(a,[np.zeros((7,21)),ks[1],ks[2]],17,7,'zero-channel')
check(a,[np.ones((7,1))],25,32,'zero-tail')
# Large mode count, longer than one block, unequal receiver delays.
a=rng.normal(size=(620,2051))*1e-3
ks=[rng.normal(size=(620,n))*1e-3 for n in (390,421,419)]
for k in ks:k[:,:280]=0
check(a,ks,512,32,'620-modes')
# irregular stream chunk sizes, including chunks smaller than propagation tail.
a=rng.normal(size=(7,293));ks=[rng.normal(size=(7,n)) for n in (31,53,39)]
for k in ks:k[:,:12]=0
s=PressureStream(ks,64,3);out=[];at=0
for n in [1,3,64,5,11,64,2,64,64,15]:
    if at==a.shape[1]:break
    n=min(n,a.shape[1]-at);out.append(s.process(a[:,at:at+n]));at+=n
assert at==a.shape[1]
out.append(s.finish());y=np.concatenate(out,axis=1);ref=oracle(a,ks)
assert np.max(abs(y-ref))<=1e-10*max(1.,np.max(abs(ref)))
assert np.all(y[:,:12]==0)
for fn in [lambda:s.finish(),lambda:s.process(a[:,:1]),lambda:PressureStream(ks,0),lambda:PressureStream([np.ones((3,4)),np.ones((2,5))]),lambda:PressureStream(ks,4).process(a[:,:5])]:
    try:fn()
    except ValueError:continue
    raise AssertionError('invalid stream accepted')
print('G2_PRESSURE_STREAM_PASS '+json.dumps(dict(cases=len(rows)+1,invalid=5,maxError=max(r['maxError'] for r in rows),rows=rows)))
