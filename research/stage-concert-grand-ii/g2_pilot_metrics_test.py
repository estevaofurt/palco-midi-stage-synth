import numpy as np
from g2_pilot_metrics import *
def rejected(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('expected rejection')
a=np.full((32,2),2.);b=np.full((32,2),.5)
g=freeze_gain({'a':a,'b':b},['a','b'])
assert abs(np.max(apply_gain(a,g['gain']))-10**(-6/20))<1e-14
assert abs(np.max(apply_gain(a,g['gain']))/np.max(apply_gain(b,g['gain']))-4)<1e-14
rejected(lambda:freeze_gain({'a':a},['a','b']))
rejected(lambda:freeze_gain({'a':a},['a','a']))
rejected(lambda:freeze_gain({'a':np.zeros_like(a)},['a']))
rejected(lambda:apply_gain(a*3,g['gain']))
rejected(lambda:apply_gain(np.array([[np.nan,0.]]),1.))
x=np.repeat(np.array([.1,.001,.0002,.00005,0.]),FS)[:,None]*np.ones((1,2))
r=decay_proxy(x,0)
assert r['relative']['lastEndS']==3 and r['digital']['lastEndS']==3 and r['joint']['lastEndS']==3
assert not r['joint']['rightCensored'] and r['windows'][-1]['rmsDbfs'] is None
y=np.repeat(np.array([.01,.00005,.00002]),FS)[:,None]*np.ones((1,2))
q=decay_proxy(y,0)
assert q['relative']['rightCensored'] and q['relative']['lastEndS']==3
assert q['digital']['lastEndS']==1 and not q['digital']['rightCensored']
assert decay_proxy(np.vstack([np.zeros((200,2)),x,np.zeros((11,2))]),200)['partialSamples']==11
rejected(lambda:decay_proxy(np.zeros((FS,2)),0))
rejected(lambda:decay_proxy(x,-1))
# Interruption does not turn separated windows into continuous audibility.
z=x.copy();z[4*FS:]=.0002
t=decay_proxy(z,0)
assert t['joint']['lastEndS']==5 and t['joint']['passingWindows']==4 and t['joint']['rightCensored']
print('G2_PILOT_METRICS_PASS 14 synthetic checks')
