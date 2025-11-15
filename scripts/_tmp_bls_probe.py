import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.app import create_app
from src.app.search import advanced_api

app = create_app('development')

with app.app_context():
    # Build params
    params = {'q': 'casa', 'mode': 'lemma', 'sensitive': '1', 'country_code': 'VEN'}
    filters = advanced_api.build_filters(params)
    cql_pattern = advanced_api.build_cql_with_speaker_filter(params, filters)
    print('filters:', filters)
    print('cql:', cql_pattern)
    
    # Compose bls params as advanced_api would
    bls_params = {
        'first': 0,
        'number': 5,
        'wordsaroundhit': 10,
        'listvalues': 'word,tokid,start_ms,end_ms,utterance_id,speaker_code',
        'patt': cql_pattern
    }

    try:
        resp = advanced_api._make_bls_request('/corpora/corapan/hits', bls_params)
        print('BLS returned status:', resp.status_code)
        data = resp.json()
        print('summary:', data.get('summary', {}).get('resultsStats', {}))
        print('first hit match lemma:', data.get('hits', [])[0].get('match', {}).get('lemma', [None])[0])
    except Exception as e:
        print('BLS request error:', e)

    # Now call the datatable_data route via test_client to inspect the JSON
    client = app.test_client()
    query_string = '?q=casa&mode=lemma&country_code=VEN&length=5&draw=1'
    res = client.get('/search/advanced/data' + query_string)
    print('\nDatatable response status:', res.status_code)
    print('JSON:', res.get_json())
