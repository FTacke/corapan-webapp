"""Quick test for the local SQLite search_tokens() function.

This script is intended as a lightweight, reproducible check to ensure
the single-word (non-multiword) query path for `search_tokens()` works
correctly without SQL aliasing issues.

Run from project root with: python test_corpus_search_tokens.py
"""
from src.app.services.corpus_search import SearchParams, search_tokens


def run():
    params = SearchParams(query='casa', search_mode='text', sensitive=1, page=1, page_size=5)
    print('Searching for `casa` on local tokens DB...')
    result = search_tokens(params)
    print(f"Found {result['total']} total results; page size: {len(result['items'])}")
    for i, item in enumerate(result['items']):
        print(f"{i+1}. token_id={item.get('token_id')} text={item.get('text')} file={item.get('filename')}")


if __name__ == '__main__':
    run()
