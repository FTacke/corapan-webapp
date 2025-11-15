import sys
from pathlib import Path

# Ensure project root is on sys.path to import src.* packages
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.app.search.cql import build_cql_with_speaker_filter, build_filters

tests = [
	{'q':'casa','mode':'lemma','sensitive':'1'},
	{'q':'casa','mode':'lemma','sensitive':'1','country_code':'VEN'},
	{'q':'casa','mode':'lemma','sensitive':'1','country_code':'ARG'},
	{'q':'Casa','mode':'forma','sensitive':'0'},
	{'q':'alcalde','mode':'forma','sensitive':'1','include_regional':'0'},
]

for i, params in enumerate(tests, start=1):
	filters = build_filters(params)
	cql = build_cql_with_speaker_filter(params, filters)
	print(f"Test {i}: params={params}")
	print(' Filters:', filters)
	print(' CQL:    ', cql)
	print('-' * 80)
