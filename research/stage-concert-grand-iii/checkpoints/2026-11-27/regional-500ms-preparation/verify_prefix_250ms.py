"""Compare the canonical first 250 ms NPY byte streams to archived full-file hashes.
No old raw arrays are needed. A mismatch is reported, never silently waived.
The NPY header is reconstructed using the same format version as the new file.
A header-only discrepancy cannot be excluded without the historical raw file.
"""
import hashlib, io, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
N=96000
def sha_prefix(path):
    with path.open('rb') as f:
        version=np.lib.format.read_magic(f)
    a=np.load(path,mmap_mode='r',allow_pickle=False)
    assert a.shape[0]==192000 and a.dtype==np.float64 and a.flags.c_contiguous
    header=io.BytesIO()
    spec=dict(descr=np.lib.format.dtype_to_descr(a.dtype),fortran_order=False,shape=(N,*a.shape[1:]))
    writers={(1,0):np.lib.format.write_array_header_1_0,(2,0):np.lib.format.write_array_header_2_0}
    if version not in writers:raise ValueError(f'Unsupported NPY header version: {version}')
    writers[version](header,spec)
    h=hashlib.sha256(header.getvalue())
    for i in range(0,N,1200):h.update(np.ascontiguousarray(a[i:min(i+1200,N)]).tobytes())
    return h.hexdigest()
def main():
    rows={}
    for line in (ROOT/'SINAIS_250ms.sha256').read_text().splitlines():
        expected,name=line.split(maxsplit=1)
        folder,filename=name.split('/')
        new=ROOT/folder.replace('long-250ms-','long-500ms-')/filename
        got=sha_prefix(new)
        rows[name]=dict(expected=expected,actual=got,exact=got==expected)
    assert len(rows)==10
    report=dict(gate=all(x['exact'] for x in rows.values()),files=rows,scope='Canonical reconstructed NPY header and 96000-sample prefix; any mismatch requires investigation against historical original arrays.')
    (ROOT/'prefix-250ms-of-500ms.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
