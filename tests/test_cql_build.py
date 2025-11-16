"""Test CQL build logic."""
from src.app.search.cql import build_cql

# Test POS search
params_pos = {"q": "VERB", "mode": "pos"}
cql_pos = build_cql(params_pos)
print(f"POS search: {cql_pos}")

# Test word search
params_word = {"q": "crisis", "mode": "word"}
cql_word = build_cql(params_word)
print(f"Word search: {cql_word}")

# Test lemma search
params_lemma = {"q": "casa", "mode": "lemma"}
cql_lemma = build_cql(params_lemma)
print(f"Lemma search: {cql_lemma}")
