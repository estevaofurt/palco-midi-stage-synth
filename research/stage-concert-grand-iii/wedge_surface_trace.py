"""Construct the exact side trace of the layered wedge without volume FEM.
Replicate the boundary subdivisions and the sorted-index tetrahedral
diagonals of closed_cavity.mesh and inclined_lid.build.
This predicts trace observability only, not acoustic impedance.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss
from lid_exterior import Panel
from acoustic_trace_resolution import panel_capture

from mesh_grading import graded_fractions

def surface_panels(poly,n,angle,height,layers,count,*,edge_grading=0.,layer_grading=0.):
    poly=np.asarray(poly,float)
    if poly.ndim!=2 or poly.shape[1]!=2 or len(poly)<3 or not 0<angle<90 or n<2 or layers<1 or height<=0:
        raise ValueError('invalid wedge trace geometry')
    if not isinstance(n,int) or not isinstance(layers,int):raise ValueError('integer subdivisions required')
    layer_fractions=graded_fractions(layers,layer_grading)
    graded_fractions(1,edge_grading)
    h=poly[:,0].min();a=np.deg2rad(angle);step=max(np.ptp(poly,axis=0))/n
    disp=np.array([np.cos(a)-1,0.,np.sin(a)])
    divisions=[max(1,int(np.ceil(np.linalg.norm(v-u)/step))) for u,v in zip(poly,np.roll(poly,-1,axis=0))]
    starts=np.r_[0,np.cumsum(divisions)];nb=int(starts[-1]);result=[]
    for i,(u,v,m) in enumerate(zip(poly,np.roll(poly,-1,axis=0),divisions)):
        edge=np.r_[v-u,0.];normal=np.cross(edge,disp);scale=np.linalg.norm(normal)
        A=scale*((u[0]+v[0])/2-h)
        if A<=1e-12:continue
        normal/=scale
        rimXY=u+(v-u)*np.arange(m+1)[:,None]/m if edge_grading==0 else u+(v-u)*graded_fractions(m,edge_grading)[:,None]
        rim=np.c_[rimXY,np.full(m+1,height)]
        top=rim+(rim[:,0]-h)[:,None]*disp
        corners=[]
        for x in (rim[0],rim[-1],top[-1],top[0]):
            if not any(np.linalg.norm(x-y)<1e-12 for y in corners):corners.append(x)
        panel=Panel(np.asarray(corners),normal,count)
        xyz=[];ids=np.empty((layers+1,m+1),int)
        for k in range(layers+1):
            f=k/layers if layer_grading==0 else layer_fractions[k]
            for j in range(m+1):
                if k and rim[j,0]-h<=1e-12:ids[k,j]=ids[0,j]
                else:
                    ids[k,j]=len(xyz);xyz.append((1-f)*rim[j]+f*top[j])
        faces=[]
        for j in range(m):
            ia=(int(starts[i])+j)%nb;ib=(ia+1)%nb
            x,y=(j,j+1) if ia<ib else (j+1,j)
            for k in range(layers):
                p,q,r,s=ids[k,x],ids[k,y],ids[k+1,x],ids[k+1,y]
                for face in ([p,q,s],[p,r,s]):
                    if len(set(face))==3:faces.append(face)
        xyz=np.asarray(xyz);faces=np.asarray(faces,int)
        if abs(panel.basis.area-A)>1e-10:raise ValueError('panel area mismatch')
        result.append((panel,xyz,faces,m))
    return result

def trace_matrix(panel,xyz,faces,order=None):
    if order is None:order=6 if panel.basis.count in (45,55) else 5
    z,w=leggauss(order);z=(z+1)/2;w=w/2
    u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    L=np.c_[1-u,u*(1-v),u*v];W=(w[:,None]*w[None,:]).ravel()*u
    C=np.zeros((len(xyz),panel.basis.count))
    for face in faces:
        t=xyz[face];J=np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))
        V=panel.basis(panel.local(L@t))
        C[face]+=L.T@((J*W)[:,None]*V)
    np.testing.assert_allclose(C.sum(0),np.r_[1.,np.zeros(panel.basis.count-1)],atol=1e-10)
    return C

def surface_capture(panel,xyz,faces):
    return panel_capture(xyz,faces,trace_matrix(panel,xyz,faces),panel)
