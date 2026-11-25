"""G3 foundation: validate governance contract, not physical correctness."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
IDS=[f'G3.{i:02}' for i in range(12)]
def validate(c):
    if c['schemaVersion']!=1 or c['generation']!='G3':raise ValueError('schema')
    r=c['requirements']
    if r['midiKeys']!=[21,108] or r['polyphony']!=[32,64] or r['output']!={'sampleRateHz':48000,'channels':2,'bits':24}:raise ValueError('instrument')
    if r['intermediateListening'] or r['externalAudioInEngine']:raise ValueError('policy')
    if r['sustainC4']!={'ppSeconds':[10,15],'ffSeconds':[30,35],'heldRenderMinSeconds':40}:raise ValueError('sustain')
    if r['f12_5']!={'keys':88,'velocities':[24,76,127],'minWindows':3,'maxCentsIncludingUncertainty':5}:raise ValueError('tuning')
    ref=c['reference'];cap=ref['capture']
    if ref['commit']!='3382bf9496bba2486f5ab0de55a264d1dfc38404' or ref['mode']!='raw natural FLAC':raise ValueError('reference')
    if cap['heightAboveStringsM']!={'value':.12,'status':'published_approximate'}:raise ValueError('reference datum')
    for k in ('heightStringsAboveBoardM','spacingM','xyM','polarPattern','orientation','lid','hammerSpeedMps','room','calibratedSpl'):
        if cap[k]!={'value':None,'status':'unknown'}:raise ValueError('unverified reference parameter: '+k)
    phases=c['phases']
    if [p['id'] for p in phases]!=IDS:raise ValueError('phase inventory')
    passed=set()
    for i,p in enumerate(phases):
        if p['depends']!=IDS[max(0,i-1):i]:raise ValueError('phase dependency')
        if p['status'] not in ('pending','implemented','passed','blocked'):raise ValueError('status')
        if not p['gate']:raise ValueError('gate')
        if p['status']=='passed':
            if not set(p['depends'])<=passed or not p['evidence']:raise ValueError('missing predecessor or evidence')
            for e in p['evidence']:
                if not isinstance(e,dict) or not e.get('commit') or not e.get('report'):raise ValueError('evidence metadata')
            passed.add(p['id'])
    technical=set(IDS[:10])<=passed
    if ref['holdoutOpened'] and not technical:raise ValueError('premature holdout')
    if phases[10]['status']!='pending' and not technical:raise ValueError('premature listening')
    return {'phases':len(phases),'passed':len(passed),'listeningEligible':technical,'scope':'contract validation only'}
if __name__=='__main__':
    print(json.dumps(validate(json.loads((ROOT/'contrato.json').read_text())),ensure_ascii=False))
