import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.app import create_app

app = create_app('development')
app.testing = True

with app.test_client() as client:
    res = client.get('/corpus/search', query_string={'q': 'casa', 'search_mode': 'text', 'include_regional': '1'})
    print('Status:', res.status_code)
    print('Length:', len(res.data))
    # If HTML error, show content snippet
    print(res.data[:800])
