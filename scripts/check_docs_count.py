from pathlib import Path
files = [
  'data/blacklab_export/tsv/2022-01-18_VEN_RCR.tsv',
  'data/blacklab_export/tsv/2022-03-14_VEN_RCR.tsv',
  'data/blacklab_export/tsv/2022-04-22_VEN_RCR.tsv',
  'data/blacklab_export/tsv/2022-06-10_VEN_RCR.tsv',
  'data/blacklab_export/tsv/2022-08-15_VEN_RCR.tsv'
]
for f in files:
    p = Path(f)
    if not p.exists():
        print(f, 'MISSING')
        continue
    with p.open('r', encoding='utf-8') as fh:
        header = fh.readline().rstrip('\n').split('\t')
        # try to find utterance_id or sentence_id column
        col = None
        for name in ('utterance_id','sentence_id'):
            if name in header:
                col = header.index(name)
                break
        if col is None:
            print(f, 'no doc-col')
            continue
        doc_prefixes = set()
        for i,line in enumerate(fh):
            parts = line.rstrip('\n').split('\t')
            if len(parts) <= col:
                continue
            val = parts[col]
            # doc prefix is characters up to ':' if present
            if ':' in val:
                doc_prefix = val.split(':')[0]
            else:
                doc_prefix = val
            doc_prefixes.add(doc_prefix)
        print(p.name, 'unique docs:', len(doc_prefixes))
