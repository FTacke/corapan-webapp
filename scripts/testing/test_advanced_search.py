"""
Smoke Tests for Advanced Search (BlackLab Integration)

Tests CQL-Builder, Filter-Builder, and basic endpoint functionality.
Run with: python -m pytest scripts/test_advanced_search.py -v
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from app.search.cql import (
    escape_cql,
    tokenize_query,
    build_token_cql,
    build_cql,
    build_filters,
    filters_to_blacklab_query,
)


class TestCQLEscaping:
    """Test CQL escaping functions"""
    
    def test_escape_backslash(self):
        assert escape_cql("test\\path") == "test\\\\path"
    
    def test_escape_quotes(self):
        assert escape_cql('test "quoted" text') == 'test \\"quoted\\" text'
    
    def test_escape_brackets(self):
        assert escape_cql("test [word] bracket") == "test \\[word\\] bracket"
    
    def test_escape_combined(self):
        text = 'México "2020" [test] \\'
        expected = 'México \\"2020\\" \\[test\\] \\\\'
        assert escape_cql(text) == expected


class TestTokenization:
    """Test query tokenization"""
    
    def test_single_word(self):
        assert tokenize_query("México") == ["México"]
    
    def test_multiple_words(self):
        assert tokenize_query("ir a casa") == ["ir", "a", "casa"]
    
    def test_extra_whitespace(self):
        assert tokenize_query("  ir   a  ") == ["ir", "a"]
    
    def test_empty_query(self):
        assert tokenize_query("") == []
        assert tokenize_query("   ") == []


class TestTokenCQL:
    """Test single-token CQL generation"""
    
    def test_forma_exacta(self):
        result = build_token_cql("México", "forma_exacta", False, False)
        assert result == '[word="México"]'
    
    def test_forma_normalized(self):
        result = build_token_cql("México", "forma", True, True)
        assert result == '[norm="méxico"]'
    
    def test_lemma(self):
        result = build_token_cql("ir", "lemma", False, False)
        assert result == '[lemma="ir"]'
    
    def test_with_pos(self):
        result = build_token_cql("ir", "lemma", False, False, "VERB")
        assert result == '[lemma="ir" & pos="VERB"]'
    
    def test_forma_ci_only(self):
        result = build_token_cql("México", "forma", True, False)
        assert result == '[norm="méxico"]'
    
    def test_forma_da_only(self):
        result = build_token_cql("México", "forma", False, True)
        assert result == '[norm="méxico"]'
    
    def test_forma_no_ci_no_da(self):
        result = build_token_cql("México", "forma", False, False)
        assert result == '[word="México"]'


class TestCQLBuilder:
    """Test full CQL pattern generation"""
    
    def test_single_word_forma(self):
        params = {"q": "méxico", "mode": "forma", "ci": True, "da": True}
        cql = build_cql(params)
        assert cql == '[norm="méxico"]'
    
    def test_single_word_exact(self):
        params = {"q": "México", "mode": "forma_exacta"}
        cql = build_cql(params)
        assert cql == '[word="México"]'
    
    def test_lemma_with_pos(self):
        params = {"q": "ir", "mode": "lemma", "pos": "VERB"}
        cql = build_cql(params)
        assert cql == '[lemma="ir" & pos="VERB"]'
    
    def test_sequence(self):
        params = {"q": "ir a", "mode": "lemma"}
        cql = build_cql(params)
        assert cql == '[lemma="ir"] [lemma="a"]'
    
    def test_sequence_with_pos(self):
        params = {"q": "ir a casa", "mode": "lemma", "pos": "VERB,ADP,NOUN"}
        cql = build_cql(params)
        assert cql == '[lemma="ir" & pos="VERB"] [lemma="a" & pos="ADP"] [lemma="casa" & pos="NOUN"]'
    
    def test_empty_query_raises(self):
        with pytest.raises(ValueError, match="Query cannot be empty"):
            build_cql({"q": ""})
    
    def test_whitespace_only_raises(self):
        # Whitespace gets stripped, so it's caught as "empty query"
        with pytest.raises(ValueError, match="Query cannot be empty"):
            build_cql({"q": "   "})
    
    def test_pos_fewer_than_tokens(self):
        # POS only for first token
        params = {"q": "ir a", "mode": "lemma", "pos": "VERB"}
        cql = build_cql(params)
        assert cql == '[lemma="ir" & pos="VERB"] [lemma="a"]'


class TestFilterBuilder:
    """Test metadata filter generation"""
    
    def test_country_filter(self):
        params = {"country_code": "ARG"}
        filters = build_filters(params)
        assert filters == {"country_code": "ARG"}
    
    def test_radio_filter(self):
        params = {"radio": "LRA1"}
        filters = build_filters(params)
        assert filters == {"radio": "LRA1"}
    
    def test_speaker_filter(self):
        params = {"speaker_code": "SPK001"}
        filters = build_filters(params)
        assert filters == {"speaker_code": "SPK001"}
    
    def test_date_range(self):
        params = {"date_from": "2020-01-01", "date_to": "2020-12-31"}
        filters = build_filters(params)
        assert filters == {
            "date_range": {"from": "2020-01-01", "to": "2020-12-31"}
        }
    
    def test_combined_filters(self):
        params = {
            "country_code": "ARG",
            "radio": "LRA1",
            "date_from": "2020-03-01"
        }
        filters = build_filters(params)
        assert filters["country_code"] == "ARG"
        assert filters["radio"] == "LRA1"
        assert filters["date_range"]["from"] == "2020-03-01"
    
    def test_empty_params(self):
        filters = build_filters({})
        assert filters == {}


class TestBlackLabFilterQuery:
    """Test BlackLab filter query string generation"""
    
    def test_country_filter(self):
        filters = {"country_code": "ARG"}
        query = filters_to_blacklab_query(filters)
        assert query == 'country_code:"ARG"'
    
    def test_date_range(self):
        filters = {"date_range": {"from": "2020-01-01", "to": "2020-12-31"}}
        query = filters_to_blacklab_query(filters)
        assert 'date >= "2020-01-01"' in query
        assert 'date <= "2020-12-31"' in query
        assert " AND " in query
    
    def test_combined_filters(self):
        filters = {
            "country_code": "ARG",
            "radio": "LRA1",
            "date_range": {"from": "2020-03-01"}
        }
        query = filters_to_blacklab_query(filters)
        assert 'country_code:"ARG"' in query
        assert 'radio:"LRA1"' in query
        assert 'date >= "2020-03-01"' in query
        assert query.count(" AND ") == 2
    
    def test_empty_filters(self):
        query = filters_to_blacklab_query({})
        assert query == ""


class TestEndToEnd:
    """End-to-end CQL + Filter generation"""
    
    def test_simple_search_arg(self):
        params = {
            "q": "covid",
            "mode": "forma",
            "ci": True,
            "country_code": "ARG"
        }
        cql = build_cql(params)
        filters = build_filters(params)
        filter_query = filters_to_blacklab_query(filters)
        
        assert cql == '[norm="covid"]'
        assert filter_query == 'country_code:"ARG"'
    
    def test_lemma_pos_sequence_with_date(self):
        params = {
            "q": "ir a",
            "mode": "lemma",
            "pos": "VERB,ADP",
            "date_from": "2020-01-01",
            "date_to": "2020-12-31"
        }
        cql = build_cql(params)
        filters = build_filters(params)
        filter_query = filters_to_blacklab_query(filters)
        
        assert cql == '[lemma="ir" & pos="VERB"] [lemma="a" & pos="ADP"]'
        assert 'date >= "2020-01-01"' in filter_query
        assert 'date <= "2020-12-31"' in filter_query


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
