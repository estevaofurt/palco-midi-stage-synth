#!/usr/bin/env python3
"""Exact-hash C5 FLAC fetch in ephemeral runner; write numeric results, delete audio in workflow."""
from pathlib import Path
import argparse,json,time,urllib.request,os
from c5_c4_analysis import SOURCES, REPO, PINNED_COMMIT, sha256_file, main as analyze


def download_sources(folder:Path):
    folder.mkdir(parents=True,exist_ok=True)
    for layer,desc in SOURCES.items():
        dst=folder/desc['file'];url=f'{REPO}{PINNED_COMMIT}/Samples/{desc["file"]}'
        for attempt in range(1,4):
            try:
                print('Fetching original C5 layer',layer,'attempt',attempt,flush=True)
                req=urllib.request.Request(url,headers={'User-Agent':'StageSynth-F1-provenance-audit/1.0','Accept':'application/octet-stream'})
                with urllib.request.urlopen(req,timeout=65) as response, dst.open('wb') as out:
                    while True:
                        block=response.read(128*1024)
                        if not block:break
                        out.write(block)
                        if out.tell()>desc['size_bytes']+1024:raise ValueError('Unexpected oversize download')
                actual=sha256_file(dst)
                if dst.stat().st_size!=desc['size_bytes'] or actual!=desc['sha256']:
                    raise ValueError(f'Authenticity check FAILED for {layer}: {dst.stat().st_size}, {actual}')
                print('C5_SHA256_VERIFIED',layer,actual,flush=True)
                break
            except (OSError,TimeoutError,ValueError) as e:
                if dst.exists():dst.unlink()
                if attempt==3:raise RuntimeError(f'C5 original unavailable or tampered: {layer}: {e}') from e
                time.sleep(attempt*3)


def main():
    a=argparse.ArgumentParser()
    a.add_argument('--tmp-dir',type=Path,required=True)
    a.add_argument('--v10-profiles',type=Path,required=True)
    a.add_argument('--output',type=Path,required=True)
    args=a.parse_args()
    if not args.v10_profiles.exists():raise FileNotFoundError(args.v10_profiles)
    download_sources(args.tmp_dir)
    result=analyze(['--source-dir',str(args.tmp_dir),'--v10-profiles',str(args.v10_profiles),'--output',str(args.output)])
    assert len(result['layers'])==len(SOURCES) and len(result['c5_vs_v10'])==len(SOURCES)
    print('C5_VERIFIED_RESULTS_BEGIN',flush=True)
    for layer,r in result['layers'].items():
        p=r.get('inharmonicity_estimate') or {}
        m=result['c5_vs_v10'].get(layer,{})
        line={'layer':layer,'duration_s':r['duration_s'],'f1_hz':p.get('fundamental_fit_hz'),
              'B':p.get('B_fit'),'attack_diff_db':m.get('attack_35_255ms',{}).get('mean_absolute_difference_db'),
              'body_diff_db':m.get('body_260_700ms',{}).get('mean_absolute_difference_db'),
              'tail_diff_db':m.get('tail_900_1400ms',{}).get('mean_absolute_difference_db')}
        print('C5_VERIFIED_METRICS',json.dumps(line,sort_keys=True),flush=True)
    print('C5_VERIFIED_RESULTS_END',flush=True)
if __name__=='__main__':main()
