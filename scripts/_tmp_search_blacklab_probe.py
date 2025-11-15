import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.app import create_app
from src.app.services.blacklab_search import search_blacklab

app = create_app('development')

with app.app_context():
    with app.test_request_context('/', base_url='http://localhost:8000'):
        params = {
            'query': 'casa',
            'search_mode': 'text',
            'sensitive': 1,
            'page': 1,
            'page_size': 5,
            'include_regional': '1'
        }
        print('Params:', params)
        try:
            res = search_blacklab(params)
            print('Returned total:', res['total'])
            for r in res['items']:
                print(' -', r.get('tokid'), r.get('text')[:30], 'country=', r.get('country_code'))
        except Exception as e:
            print('Exception:', e)
            raise
