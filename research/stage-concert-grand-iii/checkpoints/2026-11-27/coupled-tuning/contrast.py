"""Equal-norm common and differential force transfer at conservative modes.
Diagnostic force basis, not a hammer excitation or a decay measurement.
"""
from tuning import *
from scipy.linalg import null_space

def main():
 ac=Acoustic();modes=json.loads((ROOT.parent/'G3_Convergencia_Regional/dry-modes.json').read_text());rows=[]
 for key in (48,60,64):
  m=Mechanical(key);n=len(m.ids);common=np.ones(n)/np.sqrt(n);diff=null_space(common[None,:]);out=[]
  for q in next(x['modes'] for x in modes if x['key']==key and x['rank']==128):
   if q['wire_first_indicator']<.5:continue
   f=q['hz'];s=2j/h*np.tan(np.pi*f/FS);Z,U,L,H=ac.symbol(f);J=m.K/s+s*m.M+m.D;J[:80,:80]+=L;X=solve(J,m.P,assume_a='gen',check_finite=False);P=H@U@X[:80];v0=abs(P@common);vd=np.linalg.norm(P@diff,axis=1);mob=m.P.T@X
   row=dict(frequency=f,indicator=q['wire_first_indicator'],common_pressure=v0.tolist(),max_differential_pressure=vd.tolist(),differential_to_common=(vd/np.maximum(v0,1e-300)).tolist(),common_contact_norm=float(np.linalg.norm(mob@common)),differential_contact_norm=float(np.linalg.norm(mob@diff,2)),mobility_symmetry=rel(mob,mob.T));assert row['mobility_symmetry']<1e-10;out.append(row)
  rows.append(dict(key=key,modes=out));print(key,out,flush=True)
 (ROOT/'contrast.json').write_text(json.dumps(rows,indent=2))
if __name__=='__main__':main()
