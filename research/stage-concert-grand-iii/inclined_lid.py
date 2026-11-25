"""Conforming 3-D upper fluid and side apertures for a rigid hinged lid.
Exterior radiation/diffraction is NOT solved by this module.
"""
import numpy as np
from scipy.sparse import coo_matrix, block_diag
from board_contour import properties
from closed_cavity import assemble as closed_assemble
from aperture_modes import response

def build(poly,n,nz,height,angle,field,c=343.,rho=1.204,*,wedge_layers=1,boundary_n=None):
    if not isinstance(wedge_layers,int) or isinstance(wedge_layers,bool) or wedge_layers<1:
        raise ValueError('positive integer wedge_layers required')
    poly=np.asarray(poly,dtype=float)
    if not np.isfinite(angle) or not 0<=angle<90: raise ValueError('lid angle')
    m=closed_assemble(poly,n,nz,height,field,c,rho,boundary_n=boundary_n)
    if angle==0:
        return m,np.zeros((len(m['xyz']),0)),dict(areaM2=0.,wedgeVolumeM3=0.,faces=0,ports=0,gate=True)
    xy=m['xy']; N=len(xy); old=len(m['xyz']); rim=old-N+np.arange(N)
    h=poly[:,0].min(); a=np.deg2rad(angle); dx=xy[:,0]-h
    top=np.c_[h+np.cos(a)*dx,xy[:,1],height+np.sin(a)*dx]
    moving=dx>1e-12
    # Each intermediate section is an affine interpolation of rim and
    # rigid lid. Hinge vertices are shared by every layer; the same
    # sorted triangle ordering gives conforming diagonals on shared faces.
    sections=[rim];blocks=[m['xyz']];offset=old
    for layer in range(1,wedge_layers+1):
        f=layer/wedge_layers
        points=top if layer==wedge_layers else (1-f)*m['xyz'][rim]+f*top
        ids=rim.copy();ids[moving]=offset+np.arange(sum(moving))
        sections.append(ids);blocks.append(points[moving]);offset+=int(sum(moving))
    xyz=np.vstack(blocks);extra=[]
    for bottom,upper in zip(sections[:-1],sections[1:]):
        for t in m['tri']:
            i,j,k=np.sort(t)
            for ids in ([bottom[i],bottom[j],bottom[k],upper[k]],
                        [bottom[i],bottom[j],upper[j],upper[k]],
                        [bottom[i],upper[i],upper[j],upper[k]]):
                if len(set(ids))==4: extra.append(ids)
    extra=np.asarray(extra,dtype=int).reshape(-1,4)
    ii=[];jj=[];mm=[];kk=[];vol=0.
    for ids in extra:
        t=xyz[ids];J=(t[1:]-t[0]).T;V=abs(np.linalg.det(J))/6
        assert V>0
        grad=np.vstack([-np.ones(3),np.eye(3)])@np.linalg.inv(J)
        M=V/(20*c*c)*(np.ones((4,4))+np.eye(4));K=V*grad@grad.T
        ii.extend(np.repeat(ids,4));jj.extend(np.tile(ids,4));mm.extend(M.ravel());kk.extend(K.ravel());vol+=V
    size=len(xyz); pad=coo_matrix((size-old,size-old))
    M=block_diag((m['M'],pad),format='csc')+coo_matrix((mm,(ii,jj)),shape=(size,size)).tocsc()
    K=block_diag((m['K'],pad),format='csc')+coo_matrix((kk,(ii,jj)),shape=(size,size)).tocsc()
    tet=np.vstack([m['tet'],extra])
    A,center,_=properties(poly);expected=A*(center[0]-h)*np.sin(a)
    assert abs(vol-expected)<1e-10
    assert abs(float(np.ones(size)@(M@np.ones(size)))*c*c-(m['volume']+vol))<1e-10
    constant=float(np.linalg.norm(K@np.ones(size)));assert constant<1e-9
    # Extract the actual exterior boundary from tetrahedral incidence. A face
    # on a side aperture has rim/lid vertices and is not on the rigid lid plane.
    allfaces=np.sort(np.vstack([tet[:,[0,1,2]],tet[:,[0,1,3]],tet[:,[0,2,3]],tet[:,[1,2,3]]]),axis=1)
    f,counts=np.unique(allfaces,axis=0,return_counts=True)
    assert max(counts)==2
    boundary=f[counts==1]; q=xyz[boundary]
    above=np.max(q[:,:,2],axis=1)>height+1e-12
    roof=np.all(abs((q[:,:,2]-height)*np.cos(a)-(q[:,:,0]-h)*np.sin(a))<1e-10,axis=1)
    apertures=boundary[above&~roof]
    # Use the original polygon edge as a port label. Side faces are planar,
    # parallel to the displacement vector of the hinged lid.
    disp=np.array([np.cos(a)-1,0.,np.sin(a)])
    areas=[];columns=[];faces_used=[];normals=[];port_faces=[];port_polygons=[]
    for u,v in zip(poly,np.roll(poly,-1,axis=0)):
        edge=np.r_[v-u,0.]; normal=np.cross(edge,disp)
        scale=np.linalg.norm(normal); area=scale*((u[0]+v[0])/2-h)
        if area<=1e-12:continue
        normal/=scale
        origin=np.r_[u,height]
        ids=apertures[np.all(abs((xyz[apertures]-origin)@normal)<1e-10,axis=1)]
        tri=xyz[ids];weights=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
        assert len(ids)>0 and abs(sum(weights)-area)<1e-10
        col=np.zeros(size)
        np.add.at(col,ids.ravel(),np.repeat(weights/3/area,3))
        assert abs(col.sum()-1)<1e-10 and min(col)>=0
        # Exact physical vertices independent of the tetrahedral mesh.
        rim_u=np.r_[u,height];rim_v=np.r_[v,height]
        lid_u=rim_u+(u[0]-h)*disp;lid_v=rim_v+(v[0]-h)*disp
        corners=[]
        for point in (rim_u,rim_v,lid_v,lid_u):
            if not any(np.linalg.norm(point-x)<1e-12 for x in corners):corners.append(point)
        port_polygons.append(np.array(corners))
        port_faces.append(ids);areas.append(float(area));columns.append(col);faces_used.extend(map(tuple,ids));normals.append(normal.tolist())
    assert sorted(faces_used)==sorted(map(tuple,apertures)), 'missing or duplicated side face'
    # Each rim triangle must now be internal, except at zero angle.
    rimfaces=np.sort(rim[m['tri']],axis=1)
    assert not set(map(tuple,rimfaces)) & set(map(tuple,boundary))
    B=np.pad(m['B'],((0,size-old),(0,0)))
    model=dict(m,M=M,K=K,B=B,xyz=xyz,tet=tet,volume=m['volume']+vol,constantResidual=constant,apertureFaces=port_faces,aperturePolygons=port_polygons)
    report=dict(areaM2=sum(areas),portAreasM2=areas,portNormalsXYZ=normals,wedgeVolumeM3=vol,
        expectedWedgeVolumeM3=float(expected),volumeM3=model['volume'],faces=len(apertures),ports=len(areas),
        nodes=size,tetrahedra=len(tet),wedgeLayers=wedge_layers,boundaryN=n if boundary_n is None else boundary_n,constantResidual=constant,gate=True)
    return model,np.column_stack(columns),report

def matched_fixture(model,C,report,s,points):
    """Positive-real LOCAL termination for FEM/port verification only.
    Not a physical radiation impedance: excludes all mutual exterior coupling.
    """
    Z=np.diag(model['rho']*model['c']/np.asarray(report['portAreasM2']))
    return response(model,C,s,points,Z.astype(complex))
