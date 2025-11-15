import httpx

base = 'http://localhost:8000/bls/corpora/corapan/hits'
params = {
    'patt': '[word="casa"]',
    'first': 0,
    'number': 1,
    'listvalues': 'tokid,start_ms,end_ms,word,lemma,pos,country,speaker_type,sex,mode,discourse,filename,radio'
}

print('Request URL:', base)
print('Params:', params)
print('Sending...')
resp = httpx.get(base, params=params, timeout=10)
print('Status:', resp.status_code)
print('Body length:', len(resp.content))
try:
    print('JSON summary:', resp.json().get('summary', {}).get('resultsStats', {}))
except Exception:
    print('Not JSON or error parsing JSON')
