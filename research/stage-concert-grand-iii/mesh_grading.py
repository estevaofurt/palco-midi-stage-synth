import numpy as np

def graded_fractions(n,strength):
    if not isinstance(n,int) or isinstance(n,bool) or n<1 or not np.isfinite(strength) or not 0<=strength<=1:
        raise ValueError('invalid grading')
    t=np.arange(n+1)/n
    if strength==0:return t
    q=(1-strength)*t+strength*(1-np.cos(np.pi*t))/2
    q[0]=0.;q[-1]=1.
    if np.any(np.diff(q)<=0):raise ValueError('nonmonotone grading')
    return q

