"""
ARCHIVED: Legacy Corpus Search Tests

This file is an archive copy of the legacy corpus SQL search tests that
were used prior to the BlackLab migration. These tests were intentionally
retired during the migration to advanced search.
"""

from src.app.services.corpus_search import SearchParams, search_tokens


def legacy_test_search_tokens():
    params = SearchParams(query='casa', search_mode='text', sensitive=1, page=1, page_size=5)
    result = search_tokens(params)
    # Just ensure no exception is thrown and we get a dict response
    assert isinstance(result, dict)
