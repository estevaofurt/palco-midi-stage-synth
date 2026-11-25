"""Synthetic fixtures only: verify listening package software, never piano quality."""
import json,sys,tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
import g2_r1_listening_pack as pack
def write(p,obj):p.write_text(json.dumps(obj))
def fixture(root,proof):
    proof.mkdir();write(proof/'r1_report.json',dict(gate=True,passed=6,required=6))
    root.mkdir()
    for case in pack.CASES:
        dur=1.5 if case in pack.CASES[:3] else 5.
        n=round(dur*pack.FS);t=np.arange(n)/pack.FS
        x=np.column_stack((np.sin(2*np.pi*261.6*t),np.sin(2*np.pi*261.6*t+.1)))*.05*np.exp(-t)[:,None]
        for mode in (['dry'] if case=='C4-held' else ['release-only','dry']):
            d=root/f'G2-R1-{case}-{mode}';d.mkdir()
            p=d/f'{case}-{mode}.wav';o=d/f'{case}-original.wav'
            sf.write(o,x,pack.FS,subtype='PCM_24')
            sf.write(p,x*(.7 if mode=='dry' else .9),pack.FS,subtype='PCM_24')
            raw=d/'pressure.npz';np.savez(raw,pressurePa=x.T)
            write(d/'manifest.json',dict(case=case,mode=mode,commit=pack.COMMIT,originalCommit='dbd007fdeab3def76c3ff8cb3cae47741655429b',radiation=dict(gate=True),wavSha256=pack.sha(p),originalSha256=pack.sha(o),rawSha256=pack.sha(raw),events=[[0,60,1]],releases=[] if case=='C4-held' else [[.5,60]],scoreSha256='fixture',gain=.18491857409775692,durationS=dur,windows=[],postReleaseGaps=[],peakDbfs=-26,mechanical=dict(damperLossJ=.001,damperGroupLossJ=[.001])))
def run(root,proof,out):
    old=sys.argv;sys.argv=['test','--root',str(root),'--proof',str(proof),'--out',str(out)]
    try:pack.main()
    finally:sys.argv=old
def reject(root,proof,out):
    try:run(root,proof,out)
    except (AssertionError,FileNotFoundError):return
    raise AssertionError('invalid fixture accepted')
def main():
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp);root=p/'input';proof=p/'proof';fixture(root,proof)
        out=p/'valid';run(root,proof,out)
        assert len(list((out/'escuta-cega').rglob('*.wav')))==17
        assert len(list((out/'ganho-original').rglob('*.wav')))==17
        key=json.loads((out/'gabarito.json').read_text())
        assert len(key)==6 and all(len(q['files'])==(2 if q['case']=='C4-held' else 3) for q in key)
        for q in key:
            for z in q['files']:assert pack.sha(out/'escuta-cega'/q['case']/(z['label']+'.wav'))==z['sha256']
        d=root/'G2-R1-C4-held-dry';m=d/'manifest.json';b=m.read_bytes()
        m.unlink();reject(root,proof,p/'missing');m.write_bytes(b)
        row=json.loads(b);row['wavSha256']='invalid';write(m,row);reject(root,proof,p/'hash');m.write_bytes(b)
        row=json.loads(b);row['radiation']['gate']=False;write(m,row);reject(root,proof,p/'radiation');m.write_bytes(b)
        write(proof/'r1_report.json',dict(gate=False,passed=5,required=6));reject(root,proof,p/'proof-fail')
        print('G2_R1_PACK_SOFTWARE_GATE '+json.dumps(dict(checks=5,passed=5,gate=True,scope='synthetic packaging fixtures only')))
if __name__=='__main__':main()
