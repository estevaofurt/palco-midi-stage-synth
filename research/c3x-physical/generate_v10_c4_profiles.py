#!/usr/bin/env python3
"""Generate numeric ONLY reference profiles for the estimated V10 C4; no C5 PCM is input."""
from pathlib import Path
import argparse,json,sys
here=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'research/c3x-python/v10'))
from stage_synth_c3x.continuous_engine import render_sequence_v10_action
from c5_c4_analysis import measure

def generate(output:Path):
    mapping={'v1':25,'v8':75,'v16':115}
    obj={'schema':'c3x-v10-c4-numeric-reference-only-v1','source':'Stage_Synth_C3X_Etapa_10 Python physical prototype',
      'no_c5_pcm_as_synthesis_input':True,'midi':60,'samplerate_hz':48000,
      'velocity_mapping':'V10 MIDI [25,75,115] approximate illustration; NOT measured match to C5 v1/8/16',
      'layers':{}}
    for layer,vel in mapping.items():
        print('rendering',layer,vel,flush=True)
        wav=render_sequence_v10_action([(.025,60,1.30,vel)],length=1.80,fs=48000,normalize=False)
        obj['layers'][layer]=measure(wav,48000,'V10 estimated MIDI velocity '+str(vel))
        obj['layers'][layer]['virtual_velocity']=vel
    output.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();generate(a.output)
