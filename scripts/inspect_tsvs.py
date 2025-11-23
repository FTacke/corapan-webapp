from pathlib import Path

def check_tsvs(tsv_dir='data/blacklab_export/tsv', max_files=1000):
    p=Path(tsv_dir)
    files=sorted(p.glob('*.tsv'))
    print('Checking',len(files),'TSV files in',tsv_dir)
    errors=[]
    for f in files[:max_files]:
        with f.open(encoding='utf-8', errors='replace') as fh:
            header = fh.readline().rstrip('\n').split('\t')
            header_len = len(header)
            for i,line in enumerate(fh, start=2):
                cols = line.rstrip('\n').split('\t')
                if len(cols) != header_len:
                    errors.append((f.name,i,len(cols),header_len,line[:160]))
                    break
    print('Found',len(errors),'files with mismatches')
    for e in errors[:100]:
        print(e)
    return errors

if __name__ == '__main__':
    check_tsvs()
