"""
CQL Escaping & Validation - Punkt 3 Hardening (2025-11-10).

Provides:
- CQL string escaping (quote, escape special chars)
- Filter value escaping
- Rejection of suspicious sequences
- Unit tests

References:
- BlackLab CQL Syntax: https://inl.github.io/BlackLab/cql-syntax.html
"""

import re
import logging

logger = logging.getLogger(__name__)


class CQLValidationError(ValueError):
    """Raised when CQL contains invalid/suspicious syntax."""

    pass


def escape_cql_string(value: str) -> str:
    """
    Escape a string for use in CQL patterns.

    CQL strings must be enclosed in double quotes.
    Special characters inside strings must be escaped.

    Args:
        value: String to escape

    Returns:
        Escaped string ready for CQL (without outer quotes)

    Examples:
        >>> escape_cql_string('John "Jack" Doe')
        'John \\"Jack\\" Doe'

        >>> escape_cql_string('C:\\Users\\test')
        'C:\\\\Users\\\\test'
    """
    # Escape backslashes first (must be before other escapes)
    value = value.replace("\\", "\\\\")

    # Escape double quotes
    value = value.replace('"', '\\"')

    return value


def validate_cql_pattern(cql: str) -> str:
    """
    Validate CQL pattern for suspicious/malicious sequences.

    Args:
        cql: CQL pattern string

    Returns:
        cql (unchanged if valid)

    Raises:
        CQLValidationError: If pattern contains suspicious sequences
    """
    if not cql or not isinstance(cql, str):
        raise CQLValidationError("CQL pattern must be a non-empty string")

    # Strip whitespace
    cql = cql.strip()

    if not cql:
        raise CQLValidationError("CQL pattern is empty")

    # Suspicious patterns: reject attempts to break out of quotes or inject operators
    suspicious_patterns = [
        # Unmatched quotes
        (r'^"(?:[^"\\]|\\.)*$', "Unclosed quoted string"),
        # SQL injection-like patterns (shouldn't happen in CQL, but be safe)
        (r";\s*--", "SQL comment injection attempt"),
        (r";\s*DROP", "DROP statement injection attempt"),
        # CQL operator injection (try to close current pattern and add operators)
        (r'"\s*\)\s*\(', "Suspicious parenthesis pattern"),
        # Excessive whitespace or null bytes
        (r"\x00", "Null byte in pattern"),
        # Command injection (unlikely in CQL context, but check anyway)
        # Note: & is valid in CQL for combining constraints: [word="x" & pos="NOUN"]
        # Note: | is valid in CQL for regex alternation: speaker_code="(lib-pf|lec-pf)"
        (r"[;`$]", "Shell metacharacter in pattern"),
    ]

    for pattern, reason in suspicious_patterns:
        if re.search(pattern, cql, re.IGNORECASE):
            logger.warning(f"Rejected CQL pattern: {reason}")
            logger.debug(f"Pattern: {cql[:100]}")
            raise CQLValidationError(f"Invalid CQL pattern: {reason}")

    # Check balanced parentheses
    paren_count = 0
    bracket_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(cql):
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        # Only check brackets/parens outside quoted strings
        if not in_string:
            if char == "(":
                paren_count += 1
            elif char == ")":
                paren_count -= 1
            elif char == "[":
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1

            # Imbalance detected
            if paren_count < 0:
                raise CQLValidationError("Unmatched closing parenthesis ')'")
            if bracket_count < 0:
                raise CQLValidationError("Unmatched closing bracket ']'")

    # Final check: all brackets/parens closed
    if paren_count != 0:
        raise CQLValidationError(
            f"Unmatched opening parenthesis '(' (count: {paren_count})"
        )
    if bracket_count != 0:
        raise CQLValidationError(
            f"Unmatched opening bracket '[' (count: {bracket_count})"
        )

    # If in string at end, unclosed
    if in_string:
        raise CQLValidationError("Unclosed quoted string")

    return cql


def escape_filter_value(value: str, field: str = None) -> str:
    """
    Escape a value for use in BlackLab filter expressions.

    BlackLab filters use different syntax depending on field type:
    - String fields: may need quoting
    - Regex fields: may need escaping

    Args:
        value: Value to escape
        field: Field name (optional, for context-specific escaping)

    Returns:
        Escaped value

    Examples:
        >>> escape_filter_value('New York')
        '\"New York\"'

        >>> escape_filter_value('C.S.I.')  # Periods safe in filter values
        '\"C.S.I.\"'
    """
    # Quote the value (required for multi-word values)
    return f'"{escape_cql_string(value)}"'


def validate_filter_values(filters: dict) -> None:
    """
    Validate filter parameter values for suspicious content.

    Args:
        filters: Filter dict {field: [values]}

    Raises:
        CQLValidationError: If any value is suspicious
    """
    if not isinstance(filters, dict):
        return

    for field, values in filters.items():
        if not isinstance(values, (list, tuple)):
            values = [values]

        for value in values:
            if not isinstance(value, str):
                continue

            # Filter values: just check for null bytes and basic injection
            if "\x00" in value:
                raise CQLValidationError(f"Null byte in filter value: {field}={value}")

            # Values with special chars should be handled gracefully
            # (Punkt 3: reject only truly suspicious sequences)
            if re.search(r"[;&|`]", value):
                logger.warning(
                    f"Suspicious characters in filter value: {field}={value}"
                )
                # Note: We log but don't necessarily reject, as field values may legitimately
                # contain some special characters. CQL escaping will handle them.


def build_escaped_cql_query(q: str, mode: str = "forma") -> str:
    """
    Build an escaped CQL query from a user-supplied search string.

    Args:
        q: Search string (from user input)
        mode: Search mode ('forma', 'forma_exacta', 'lemma', 'cql')

    Returns:
        Properly escaped CQL pattern

    Raises:
        CQLValidationError: If query is invalid
    """
    if not q:
        raise CQLValidationError("Search query is empty")

    if mode == "cql":
        # User provided raw CQL - validate but don't escape
        return validate_cql_pattern(q)
    else:
        # User provided a word/lemma - quote and escape it
        escaped = escape_cql_string(q.strip())
        return f'"{escaped}"'


# ============================================================================
# Unit Tests (for manual verification)
# ============================================================================


def _test_escape_cql_string():
    """Test CQL string escaping."""
    assert escape_cql_string("hello") == "hello"
    assert escape_cql_string('John "Jack" Doe') == 'John \\"Jack\\" Doe'
    assert escape_cql_string("C:\\Users") == "C:\\\\Users"
    assert escape_cql_string('mix "quote" and \\path') == 'mix \\"quote\\" and \\\\path'
    print("✅ escape_cql_string tests passed")


def _test_validate_cql_pattern():
    """Test CQL pattern validation."""
    # Valid patterns
    assert validate_cql_pattern('"hello"') == '"hello"'
    assert validate_cql_pattern('[pos="NN"]') == '[pos="NN"]'
    assert validate_cql_pattern('"hello" | "world"') == '"hello" | "world"'

    # Invalid patterns - should raise
    try:
        validate_cql_pattern('"\\"unclosed')
        assert False, "Should have raised"
    except CQLValidationError:
        pass

    try:
        validate_cql_pattern("(unmatched")
        assert False, "Should have raised"
    except CQLValidationError:
        pass

    try:
        validate_cql_pattern("drop table hits; --")
        assert False, "Should have raised"
    except CQLValidationError:
        pass

    print("✅ validate_cql_pattern tests passed")


def _test_escape_filter_value():
    """Test filter value escaping."""
    assert escape_filter_value("hello") == '"hello"'
    assert escape_filter_value("New York") == '"New York"'
    assert escape_filter_value("C.S.I.") == '"C.S.I."'
    print("✅ escape_filter_value tests passed")


if __name__ == "__main__":
    _test_escape_cql_string()
    _test_validate_cql_pattern()
    _test_escape_filter_value()
    print("\n🎯 All CQL validation tests passed!")
