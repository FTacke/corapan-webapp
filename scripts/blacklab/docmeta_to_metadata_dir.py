#!/usr/bin/env python3
from pathlib import Path
import json

def main():
    p = Path('data/blacklab_export/docmeta.jsonl')
    md_dir = Path('data/blacklab_export/metadata')
    md_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    if not p.exists():
        print('docmeta.jsonl not found:', p)
        return 0
    with p.open(encoding='utf-8') as fh:
        for line in fh:
            line=line.strip()
            if not line:
                continue
            doc = json.loads(line)
            docname = doc.get('doc') or doc.get('file_id') or None
            if not docname:
                continue
            out = md_dir / (docname + '.json')
            with out.open('w', encoding='utf-8') as of:
                json.dump(doc, of, ensure_ascii=False)
            count += 1
    print('Wrote', count, 'metadata files to', md_dir)
    return count

if __name__ == '__main__':
    main()
