"""Read integrity-checked matrices from the spatial reference experiment.
A completed but physically unconverged experiment may be replayed for
diagnostics; never use a partial archive or grant solver approval.
"""
import hashlib,re
from pathlib import Path
import numpy as np
from split_radiation import relative
from dual_cavity_reference import couple
from nested_acoustic_ports import coupled_projection
from flow_modal_audit import audit_flow,pressure_defect

def read_npz(root,entry,shapes,frequencies):
    name=entry.get('file','');sha=entry.get('sha256','')
    if not isinstance(name,str) or not re.fullmatch(r'[a-zA-Z0-9_]+\.npz',name) or not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):
        raise ValueError('invalid archive reference')
    path=Path(root)/name
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=sha:
        raise ValueError('archive hash mismatch')
    with np.load(path,allow_pickle=False) as data:
        if set(data.files)!=set(shapes)|{'frequencies'}:raise ValueError('unexpected archive arrays')
        if not np.array_equal(data['frequencies'],frequencies):raise ValueError('wrong frequency grid')
        out={}
        for k,shape in shapes.items():
            x=data[k]
            if x.shape!=shape or x.dtype.kind not in 'fci' or not np.isfinite(x).all():
                raise ValueError('invalid matrix '+k)
            out[k]=x
    return out

def validate_manifest(doc,angle,sha,freq,configs):
    s=doc.get('summary',{});rows=doc.get('cases',[])
    if doc.get('scaleSha256')!=sha or doc.get('frequenciesHz')!=list(freq) or s.get('angleDeg')!=angle:
        raise ValueError('archive provenance mismatch')
    for k,v in dict(maximumModes=252,exteriorFixed=True,lowerFixed=True,directionalSpatialOnly=True,
                    commonFreeSpaceMonopolesOnly=True,fullCabinetReady=False,radiationReady=False,
                    modalConvergenceCertified=False,quadratureConvergenceCertified=False).items():
        if s.get(k)!=v:raise ValueError('invalid archive scope: '+k)
    if not isinstance(s.get('gate'),bool) or len(rows)!=len(configs):
        raise ValueError('incomplete archive manifest')
    if [(x.get('planarN'),x.get('boundaryN'),x.get('wedgeLayers')) for x in rows]!=list(configs):
        raise ValueError('unexpected mesh configurations')
    for row in rows:
        reports=row.get('reports',[])
        if row.get('gate') is not True or [r.get('frequencyHz') for r in reports]!=list(freq):
            raise ValueError('incomplete mesh results')
        if any(any(r.get(k,{}).get('gate') is not True for k in ('upper','lower','exterior','coupled')) for r in reports):
            raise ValueError('failed algebraic checks')
    return rows

def replay_full(Zu,Pu,Zl,Pl,Ze,Pe,Ystored,Fstored,nb):
    Y,p1,p2,p3,F,r=couple(Zu,Pu,Zl,Pl,Ze,Pe,nb,reference_kind='common-free-space-monopole')
    diff=dict(impedance=relative(Y,Ystored),flow=relative(F,Fstored))
    if not r['gate'] or max(diff.values())>1e-9:raise ValueError('archived solution could not be reproduced')
    return (Y,p1,p2,p3,F),diff

def modal_replay(matrices,Tu,Tl,nb,counts,areas,full):
    from scipy.linalg import block_diag
    Y,p1,p2,p3,F,r=coupled_projection(*matrices,Tu,Tl,nb)
    T=block_diag(Tu,Tl)
    loc=audit_flow(F,full[-1],T,counts,areas)
    Zu,Pu,Zl,Pl,Ze,Pe=matrices
    defect=pressure_defect(Zu,Zl,Ze,F,T,nb)
    if not r['gate'] or loc['orthogonalClosure']>1e-8 or defect['resolvedRelative']>1e-8:
        raise ValueError('invalid projected solution')
    return (Y,p1,p2,p3,F),dict(coupled=r,flow=loc,pressureDefect=defect)
