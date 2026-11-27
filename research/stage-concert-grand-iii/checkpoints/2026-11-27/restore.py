"""Verify archives, restore sibling layout, and audit exact missing dependencies."""
import argparse, hashlib, json, zipfile
from pathlib import Path

def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def entries(p):
    for line in p.read_text(encoding='utf-8').splitlines():
        if line.strip():
            h, name = line.split(maxsplit=1)
            yield h, name.lstrip('*')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archives', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    if args.output.exists():
        ap.error('Output must not exist (preserve historical files).')
    manifest = Path(__file__).with_name('ARCHIVES.sha256')
    sources = []
    for h, name in entries(manifest):
        p = args.archives / name
        if not p.exists():
            p = args.archives / name.replace('.zip', '(1).zip')
        if not p.is_file() or digest(p) != h:
            raise SystemExit(f'Missing or hash mismatch: {name}')
        sources.append((name, p))
    args.output.mkdir(parents=True)
    verified = 0
    for name, p in sources:
        root = args.output / 'G3_Cavidade_Compactacao_Local' if name == 'G3_Cavidade_Compactacao_Local.zip' else args.output
        with zipfile.ZipFile(p) as z:
            for item in z.infolist():
                target = (root / item.filename).resolve()
                if not target.is_relative_to(root.resolve()):
                    raise SystemExit(f'Unsafe ZIP entry: {item.filename}')
                if not item.is_dir() and target.exists():
                    raise SystemExit(f'Collision: {target}')
            z.extractall(root)
            for m in (i for i in z.namelist() if i == 'SHA256SUMS' or i.count('/') == 1 and i.endswith('/SHA256SUMS')):
                for h, relative in entries(root / m):
                    if digest((root / m).parent / relative) != h:
                        raise SystemExit(f'Internal hash mismatch: {m}: {relative}')
                    verified += 1
    audit = args.output / 'G3_Memoria_Causal_Particionada' / 'DEPENDENCIAS_FALTANTES.sha256'
    results = dict(archives=len(sources), manifest_entries=verified, recovered=[], missing=[], divergent=[])
    for h, relative in entries(audit):
        p = audit.parent / relative
        key = 'missing' if not p.is_file() else 'recovered' if digest(p) == h else 'divergent'
        results[key].append(relative)
    print(json.dumps(results, indent=2))
    if results['divergent']:
        raise SystemExit(1)
    if results['missing']:
        raise SystemExit(2)

if __name__ == '__main__':
    main()
