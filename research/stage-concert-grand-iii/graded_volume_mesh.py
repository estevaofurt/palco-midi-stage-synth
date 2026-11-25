"""Geometry-only volumetric wedge trial with matching graded boundary.
No matrices or harmonic response are assembled here.
"""
import numpy as np
from scipy.spatial import cKDTree
from closed_cavity import mesh
from mesh_grading import graded_fractions
from board_contour import properties
from wedge_surface_trace import surface_panels

def build(poly,n,b,layers,height,angle,eg,lg):
    xy,tri,base,tet=mesh(poly,n,1,height,boundary_n=b,edge_grading=eg)
    N=len(xy);rim=N+np.arange(N);h=poly[:,0].min();a=np.deg2rad(angle);dx=xy[:,0]-h
    top=np.c_[h+np.cos(a)*dx,xy[:,1],height+np.sin(a)*dx];moving=dx>1e-12
    blocks=[base];sections=[rim];offset=len(base)
    for f in graded_fractions(layers,lg)[1:]:
        points=top if f==1 else (1-f)*base[rim]+f*top
        ids=rim.copy();ids[moving]=offset+np.arange(sum(moving));offset+=int(sum(moving))
        sections.append(ids);blocks.append(points[moving])
    extra=[]
    for bottom,upper in zip(sections[:-1],sections[1:]):
        i,j,k=np.sort(tri,axis=1).T
        for v in (np.c_[bottom[i],bottom[j],bottom[k],upper[k]],np.c_[bottom[i],bottom[j],upper[j],upper[k]],np.c_[bottom[i],upper[i],upper[j],upper[k]]):
            vv=np.sort(v,axis=1);extra.append(v[np.all(np.diff(vv,axis=1)>0,axis=1)])
    xyz=np.vstack(blocks);extra=np.vstack(extra);alltet=np.vstack([tet,extra])
    return dict(xyz=xyz,tet=alltet,baseTets=len(tet),rim=rim,tri=tri,xy=xy)

def quality(xyz,tet):
    t=xyz[tet];J=np.transpose(t[:,1:]-t[:,:1],(0,2,1));V=abs(np.linalg.det(J))/6
    if not np.isfinite(V).all() or np.any(V<=0):raise ValueError('degenerate tetrahedron')
    # Mean ratio: 1 for a regular tetrahedron; tends to zero for slivers.
    e=sum(np.sum((t[:,i]-t[:,j])**2,axis=1) for i in range(4) for j in range(i+1,4))
    q=12*(3*V)**(2/3)/e
    if q.max()>1+1e-10:raise ValueError('invalid mean ratio')
    return dict(volume=float(V.sum()),minimumVolume=float(V.min()),minimumMeanRatio=float(q.min()),
        meanRatioPercentiles=np.percentile(q,[1,5,50,95]).tolist(),maximumJacobianCondition=float(np.linalg.cond(J).max()))

def audit(model,poly,b,layers,height,angle,eg,lg):
    xyz,tet=model['xyz'],model['tet'];nbase=model['baseTets'];a=np.deg2rad(angle);h=poly[:,0].min()
    A,center,_=properties(poly);base=quality(xyz,tet[:nbase]);wedge=quality(xyz,tet[nbase:])
    expected=A*(center[0]-h)*np.sin(a)
    assert abs(base['volume']-A*height)<=1e-10 and abs(wedge['volume']-expected)<=1e-10
    # Check oriented incidence, not merely absolute volume: orient each tet
    # consistently before verifying opposing internal face normals.
    tt=tet.copy();z=xyz[tt];negative=np.linalg.det(z[:,1:]-z[:,:1])<0
    tt[negative,0],tt[negative,1]=tt[negative,1].copy(),tt[negative,0].copy()
    F=np.vstack([tt[:,[1,2,3]],tt[:,[0,3,2]],tt[:,[0,1,3]],tt[:,[0,2,1]]])
    sign=np.where(((F[:,0]>F[:,1]).astype(int)+(F[:,0]>F[:,2]).astype(int)+(F[:,1]>F[:,2]).astype(int))%2,-1,1)
    unique,idx,cnt=np.unique(np.sort(F,axis=1),axis=0,return_inverse=True,return_counts=True)
    sums=np.bincount(idx.ravel(),weights=sign)
    assert cnt.max()==2 and np.all(sums[cnt==2]==0)
    boundary=unique[cnt==1];q=xyz[boundary]
    above=np.max(q[:,:,2],axis=1)>height+1e-12
    roof=np.all(abs((q[:,:,2]-height)*np.cos(a)-(q[:,:,0]-h)*np.sin(a))<1e-10,axis=1)
    apertures=boundary[above&~roof];used=[];checks=[]
    for p,x,f,m in surface_panels(poly,b,angle,height,layers,55,edge_grading=eg,layer_grading=lg):
        normal=np.cross(p.axes[:,0],p.axes[:,1])
        ids=apertures[np.all(abs((xyz[apertures]-p.origin)@normal)<1e-10,axis=1)]
        nodes=np.unique(ids);dist,ix=cKDTree(xyz[nodes]).query(x)
        assert len(nodes)==len(x) and len(np.unique(ix))==len(x) and max(dist)<=1e-10
        target=np.sort(nodes[ix][f],axis=1)
        assert np.array_equal(np.array(sorted(map(tuple,target))),np.array(sorted(map(tuple,ids))))
        used.extend(map(tuple,ids));checks.append(dict(faces=len(ids),nodes=len(nodes),maxCoordinateDifference=float(max(dist))))
    assert sorted(used)==sorted(map(tuple,apertures))
    rimfaces=np.sort(model['rim'][model['tri']],axis=1)
    assert not set(map(tuple,rimfaces))&set(map(tuple,boundary))
    return dict(gate=True,nodes=len(xyz),tetrahedra=len(tet),base=base,wedge=wedge,expectedWedgeVolume=expected,
        apertureFaces=len(apertures),panels=checks,orientationAndIncidencePassed=True)
