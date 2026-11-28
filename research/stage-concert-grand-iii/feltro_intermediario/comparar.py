"""Compare the intermediate felt with the archived physical endpoints."""
import argparse
import json
from pathlib import Path

import numpy as np

CASES = ('107-24', '107-76', '108-24', '108-76')
CUTS = ((60, 100), (60, 90), (70, 100))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('run', 'archive', 'matrix'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    reference = json.loads(args.matrix.read_text())
    report = {}
    for case in CASES:
        archived = args.archive / case
        candidate = args.run / case
        base = json.loads((archived / 'resultados.json').read_text())
        new = json.loads((candidate / 'resultados.json').read_text())
        for key in ('key', 'midi', 'partials', 'rate_hz', 'steps', 'impact_speed_mps'):
            assert new[key] == base[key]
        rate, steps = new['rate_hz'], new['steps']
        assert new['energy_residual'] < 1e-8 and new['continuity'] < 1e-10
        with np.load(archived / 'pressao.npz', allow_pickle=False) as data:
            traces = {felt: data[felt][:steps] for felt in ('original', 'graduado')}
        with np.load(candidate / 'sinais.npz', allow_pickle=False) as data:
            traces['intermediario'] = data['pressure']
            force = data['force']
        assert force.shape[0] == new['capture_step'] and np.all(force >= 0)
        np.testing.assert_allclose(force.sum()/rate, new['impulse_Ns'], rtol=1e-12)
        np.testing.assert_allclose(force.sum(axis=1).max(), new['peak_N'], rtol=1e-12)
        assert all(trace.shape == (steps, 2) for trace in traces.values())
        row = {'metrics': new, 'contact_ms': {
                   felt: base['cases'][felt]['capture_step'] * 1000/rate
                   for felt in ('original', 'graduado')},
               'impulse_Ns': {felt: base['cases'][felt]['impulse_Ns']
                              for felt in ('original', 'graduado')},
               'windows': {}}
        row['contact_ms']['intermediario'] = new['capture_step'] * 1000/rate
        row['impulse_Ns']['intermediario'] = new['impulse_Ns']
        nfft = round(.040 * rate)
        hz = np.fft.rfftfreq(nfft, 1/rate)
        mask = (hz >= 300) & (hz < 650)
        for start, stop in CUTS:
            begin, end = (round(ms * rate / 1000) for ms in (start, stop))
            for taper, weights in (('hann', np.hanning(end-begin)),
                                   ('rectangular', np.ones(end-begin))):
                power = {label: (abs(np.fft.rfft(trace[begin:end] * weights[:, None],
                                                n=nfft, axis=0)[mask])**2).sum(axis=0)
                         for label, trace in traces.items()}
                row['windows'][f'{start}-{stop}_{taper}'] = {
                    label: (10*np.log10(power[label]/power['original'])).tolist()
                    for label in ('intermediario', 'graduado')}
        np.testing.assert_allclose(
            [row['windows'][window]['graduado'] for window in reference['windows']],
            reference['cases'][case]['full'], rtol=1e-12, atol=1e-12)
        report[case] = row
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
