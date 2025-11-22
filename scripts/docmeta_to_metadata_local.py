#!/usr/bin/env python3
import sys
from pathlib import Path
import json

def main():
    if len(sys.argv) < 3:
        print('usage: docmeta_to_metadata_local.py <docmeta.jsonl> <outdir>')
        return 2
    p = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    count = 0
    if not p.exists():
        print('docmeta not found', p)
        return 1
    with p.open(encoding='utf-8') as fh:
        for line in fh:
            line=line.strip()
            if not line:
                continue
            doc = json.loads(line)
            docname = doc.get('doc') or doc.get('file_id') or None
            if not docname:
                continue
            out = outdir / (docname + '.json')
            with out.open('w', encoding='utf-8') as of:
                json.dump(doc, of, ensure_ascii=False)
            count += 1
    print('Wrote', count, 'metadata files to', outdir)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
