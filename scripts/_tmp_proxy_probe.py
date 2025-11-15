import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.app import create_app

app = create_app('development')

with app.test_client() as client:
    res = client.get('/bls/corapan/hits', query_string={
        'patt': '[word="casa"]',
        'listvalues': 'tokid,start_ms,end_ms,word,lemma,pos,country,speaker_type,sex,mode,discourse,filename,radio',
        'first': 0,
        'number': 1,
    })
    print('Status:', res.status_code)
    print('Headers:', res.headers.get('Content-Type'))
    print(res.data[:1000])
