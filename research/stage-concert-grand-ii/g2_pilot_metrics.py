"""G2.03 operational supplement: deterministic pilot gain and digital decay proxy.
No sound generation, calibration, or claim of acoustic audibility.
"""
import math
import numpy as np
HEADROOM_DBFS=-6.
RELATIVE_FLOOR_DB=-60.
DIGITAL_FLOOR_DBFS=-80.
FS=48000
def stereo(x):
    a=np.asarray(x,dtype=np.float64)
    if a.ndim!=2 or a.shape[1]!=2 or not len(a) or not np.all(np.isfinite(a)):
        raise ValueError('finite stereo [samples,2] required')
    return a
def freeze_gain(clips,expected_ids):
    """One gain from a predeclared complete development set, never a holdout."""
    ids=list(expected_ids)
    if not ids or len(ids)!=len(set(ids)) or set(ids)!=set(clips):
        raise ValueError('incomplete or duplicate development manifest')
    peaks={i:float(np.max(abs(stereo(clips[i])))) for i in ids}
    peak=max(peaks.values())
    if peak<=0:raise ValueError('silent development set')
    gain=10**(HEADROOM_DBFS/20)/peak
    if not math.isfinite(gain):raise ValueError('invalid gain')
    return dict(gain=gain,headroomDbfs=HEADROOM_DBFS,anchorIds=ids,peaks=peaks,maximumInputPeak=peak)
def apply_gain(x,gain):
    if not math.isfinite(gain) or gain<=0:raise ValueError('gain')
    a=stereo(x)*gain
    if not np.all(np.isfinite(a)) or np.max(abs(a))>=1:raise ValueError('clipping or invalid output; do not renormalize')
    return a
def rms(x):return float(np.sqrt(np.mean(x*x)))
def db(a):return 20*math.log10(a) if a>0 else None
def decay_proxy(x,onset_sample,fs=FS):
    """Nonoverlapping full 1s windows from acoustic onset. Thresholds are digital only."""
    a=stereo(x)
    if fs!=FS or not isinstance(onset_sample,(int,np.integer)) or not 0<=onset_sample<len(a):
        raise ValueError('48k and valid onset required')
    z=a[onset_sample:];ref=z[round(.02*fs):round(.08*fs)]
    if len(ref)!=round(.06*fs):raise ValueError('short attack reference')
    ref_rms=rms(ref)
    if ref_rms<=0:raise ValueError('silent attack reference')
    relative=ref_rms*10**(RELATIVE_FLOOR_DB/20)
    absolute=10**(DIGITAL_FLOOR_DBFS/20)
    n=len(z)//fs
    if not n:raise ValueError('no complete decay window')
    windows=[]
    for i in range(n):
        v=rms(z[i*fs:(i+1)*fs])
        windows.append(dict(startS=i,endS=i+1,rmsDbfs=db(v),relativeDb=db(v/ref_rms),relativePass=v>=relative,digitalPass=v>=absolute))
    def last(predicate):
        passing=[w for w in windows if predicate(w)]
        return dict(lastEndS=passing[-1]['endS'] if passing else None,rightCensored=bool(passing and passing[-1]['endS']==n),passingWindows=len(passing))
    return dict(attackRmsDbfs=db(ref_rms),relativeFloorDb=RELATIVE_FLOOR_DB,digitalFloorDbfs=DIGITAL_FLOOR_DBFS,relative=last(lambda w:w['relativePass']),digital=last(lambda w:w['digitalPass']),joint=last(lambda w:w['relativePass'] and w['digitalPass']),completeSeconds=n,partialSamples=len(z)%fs,windows=windows)
