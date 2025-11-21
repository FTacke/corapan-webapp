"""
Deprecated test: `test_corpus_search_tokens.py`

This test was specifically for the legacy corpus SQL-based search service.
The project has migrated to BlackLab-powered advanced search and the legacy
corpus tests were removed as part of the cleanup process.
"""


def test_noop():
    # No-op test preserved for history. Tests for corpus functionality have been
    # moved/replaced by advanced search tests. Remove this file if full deletion is desired.
    assert True
