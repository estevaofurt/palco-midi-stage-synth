"""Measure the L2 projection of aperture flux fields onto the P1 trace.
This is a geometric observability diagnostic, not an acoustic solve.
For basis mass I/A, the captured norm matrix is A C^T M_trace^-1 C.
A small eigenvalue identifies a combination invisible to the trace mesh.
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu

def surface_mass(xyz,faces):
    xyz=np.asarray(xyz,float);faces=np.asarray(faces,int)
    if xyz.ndim!=2 or xyz.shape[1] not in (2,3) or faces.ndim!=2 or faces.shape[1]!=3 or len(faces)==0:
        raise ValueError('invalid triangle surface')
    nodes,inv=np.unique(faces,return_inverse=True);ids=inv.reshape(faces.shape)
    if nodes.min()<0 or nodes.max()>=len(xyz):raise ValueError('invalid node index')
    t=xyz[faces];a=t[:,1]-t[:,0];b=t[:,2]-t[:,0]
    area=np.linalg.norm(np.cross(a,b),axis=1)/2 if xyz.shape[1]==3 else abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])/2
    if not np.isfinite(area).all() or min(area)<=0:raise ValueError('degenerate triangle')
    M=area[:,None,None]*(np.ones((3,3))+np.eye(3))/12
    i=np.repeat(ids,3,axis=1).ravel();j=np.tile(ids,(1,3)).ravel()
    return nodes,coo_matrix((M.ravel(),(i,j)),shape=(len(nodes),len(nodes))).tocsc(),float(area.sum())

def capture(M,C,area):
    C=np.asarray(C,float)
    if M.shape!=(len(C),len(C)) or C.ndim!=2 or area<=0 or not np.isfinite(C).all():
        raise ValueError('incompatible trace matrix')
    X=splu(M.tocsc()).solve(C)
    G=area*C.T@X
    if np.linalg.norm(G-G.T)>1e-9*max(np.linalg.norm(G),1e-30):
        raise ValueError('non-symmetric projection')
    return (G+G.T)/2

def describe(G,T=None):
    if T is not None:G=T.T@G@T
    e=np.linalg.eigvalsh(G)
    if e.min()<-1e-8 or e.max()>1+1e-8:
        raise ValueError('trace projection violates L2 norm bounds')
    # Tiny roundoff only; report raw eigenvalues as well.
    return dict(modes=len(e),minimumCapturedEnergy=float(e.min()),maximumCapturedEnergy=float(e.max()),
        meanCapturedEnergy=float(e.mean()),worstProjectionResidual=float(np.sqrt(max(0.,1-e.min()))),
        averageProjectionResidual=float(np.sqrt(max(0.,1-e.mean()))),
        nearNullModes=int(np.sum(e<1e-6)),eigenvalues=e.tolist())

def panel_capture(xyz,faces,C,panel):
    nodes,M,A=surface_mass(xyz,faces)
    if abs(A-panel.basis.area)>1e-10:raise ValueError('trace area mismatch')
    if C.shape!=(len(xyz),panel.basis.count):raise ValueError('trace dimensions')
    mask=np.ones(len(xyz),bool);mask[nodes]=False
    if np.linalg.norm(C[mask])>1e-12:raise ValueError('trace support outside panel')
    return capture(M,C[nodes],A),len(nodes)
