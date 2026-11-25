"""Guard independent mesh and quadrature convergence comparisons."""
import hashlib
import numpy as np

def signature(t,labels):
    t=np.ascontiguousarray(t,dtype='<f8');labels=np.ascontiguousarray(labels,dtype='<i8')
    if t.ndim!=3 or t.shape[1:]!=(3,3) or labels.shape!=(len(t),):
        raise ValueError('incompatible triangle and label dimensions')
    if not np.isfinite(t).all():raise ValueError('nonfinite mesh')
    h=hashlib.sha256()
    h.update(np.asarray(t.shape,dtype='<i8').tobytes());h.update(t.tobytes());h.update(labels.tobytes())
    return h.hexdigest()

def require_same_mesh(a,b):
    if a!=b:raise ValueError('quadrature comparison changed the mesh or surface labels')
    return True
