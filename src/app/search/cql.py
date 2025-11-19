"""
CQL (Corpus Query Language) Builder for BlackLab searches.

Constructs CQL patterns from user input (form data) and builds
document filters for metadata-based filtering.
"""
import logging
import re
from typing import Dict, List, Optional
import re as _re

from .speaker_utils import get_speaker_codes_for_filters

logger = logging.getLogger(__name__)


def escape_cql(text: str) -> str:
    """
    Escape special CQL characters.
    
    Escapes: double quotes, backslashes, square brackets
    
    Args:
        text: Raw input string
        
    Returns:
        CQL-safe escaped string
    """
    # Order matters: backslash first, then quotes, then brackets
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    return text


def tokenize_query(query: str) -> List[str]:
    """
    Split query into tokens (whitespace-separated).
    
    Args:
        query: User input string
        
    Returns:
        List of tokens (stripped, non-empty)
    """
    return [t.strip() for t in query.split() if t.strip()]


def build_token_cql(
    token: str,
    mode: str,
    sensitive: bool,
    pos: Optional[str] = None
) -> str:
    """
    Build CQL for a single token.
    
    Args:
        token: Word/lemma to search
        mode: 'forma_exacta' | 'forma' | 'lemma' | 'cql' (raw CQL)
        sensitive: If False, use 'norm' field (case/diacritic insensitive)
        pos: POS tag constraint (optional)
        
    Returns:
        CQL string for this token, e.g., [word="México"] or [norm="mexico"]
    """
    # Defensive: ensure token is not None/empty
    if not token:
        raise ValueError("Token cannot be empty")
    
    # If mode is 'cql', return the token as-is (it's raw CQL already)
    if mode == "cql":
        return token
    
    escaped = escape_cql(token)
    
    # Field selection
    if mode == "forma_exacta":
        # Exact match: use 'word' field (case-sensitive, always)
        field = "word"
        value = escaped
    elif mode == "lemma":
        # Lemma search: use 'lemma' field
        field = "lemma"
        value = escaped.lower()  # Lemmas are normalized
    elif mode == "pos":
        # POS tag search
        field = "pos"
        value = escaped.upper()  # POS tags are uppercase
    else:  # mode == "forma"
        # forma: if sensitive=False, use 'norm', else use 'word'
        if sensitive:
            field = "word"
            value = escaped
        else:
            field = "norm"
            value = escaped.lower()
    
    # Base constraint
    # Determine operator (default = equality)
    operator = locals().get('operator', '=')
    constraints = [f'{field}{operator}"{value}"']
    
    # POS constraint (optional) - only add if not already a POS search
    if pos and mode != "pos":
        constraints.append(f'pos="{escape_cql(pos)}"')
    
    # Combine with &
    constraint_str = " & ".join(constraints)
    return f"[{constraint_str}]"


def build_speaker_code_constraint(filters: Dict) -> str:
    """
    Build CQL constraint for speaker_code from speaker attribute filters.
    
    Args:
        filters: Output from build_filters() containing speaker_type, sex, mode, discourse
        
    Returns:
        CQL constraint string like 'speaker_code="lib-pf"' or 'speaker_code="(lib-pf|lec-pf)"'
        Empty string if no speaker filters
    """
    # Defensive: handle None filters
    if not filters:
        return ""
    
    speaker_types = filters.get("speaker_type", [])
    sexes = filters.get("sex", [])
    modes = filters.get("mode", [])
    discourses = filters.get("discourse", [])
    
    # If no speaker filters, return empty
    if not any([speaker_types, sexes, modes, discourses]):
        return ""
    
    # Get matching speaker_codes
    matching_codes = get_speaker_codes_for_filters(
        speaker_types=speaker_types,
        sexes=sexes,
        modes=modes,
        discourses=discourses
    )
    
    if not matching_codes:
        # No matching codes → impossible filter (will return 0 results)
        logger.warning(f"No speaker_codes match filters: speaker_type={speaker_types}, sex={sexes}, mode={modes}, discourse={discourses}")
        return 'speaker_code="__IMPOSSIBLE__"'
    
    logger.info(f"Speaker filters → speaker_codes: {matching_codes}")
    
    # Build constraint
    if len(matching_codes) == 1:
        return f'speaker_code="{matching_codes[0]}"'
    else:
        # Multiple codes: use regex alternation
        codes_pattern = "|".join(matching_codes)
        return f'speaker_code="({codes_pattern})"'


def build_cql(params: Dict) -> str:
    """
    Build full CQL pattern from form parameters.
    
    Deterministic handling of multiple CQL parameter names.
    
    Args:
        params: Request form data
            - q or query (str): Query string
            - mode (str): 'forma_exacta' | 'forma' | 'lemma' | 'cql'
            - sensitive (bool or str): '0'/'false' = case/diacritic insensitive
            - pos (str): Comma-separated POS tags (optional)
            
    Returns:
        Complete CQL pattern (e.g., '[lemma="ir"] [pos="VERB"]')
        
    Raises:
        ValueError: If query is empty or invalid
    """
    # Defensive: ensure params is not None
    if not params:
        raise ValueError("params cannot be None")
    
    # Query: try both 'q' and 'query'
    query = params.get("q") or params.get("query", "")
    query = query.strip() if query else ""
    
    # If query is empty, return a wildcard token that can be decorated with filters.
    if not query:
        return "[]"
    
    mode = params.get("mode", "forma")
    
    # Parse sensitive flag
    # sensitive can be string ('0', '1', 'true', 'false') or bool
    # Default to insensitive ('0') for forma mode, sensitive for others
    sensitive_raw = params.get("sensitive", "0" if mode == "forma" else "1")
    sensitive = sensitive_raw not in ("0", "false", False)
    
    # Parse POS tags
    pos_list = params.get("pos", "")
    pos_tags = [p.strip().upper() for p in pos_list.split(",") if p.strip()]
    
    # Tokenize query
    tokens = tokenize_query(query)
    if not tokens:
        raise ValueError("Query contains no valid tokens")
    
    # Build CQL for each token
    cql_parts = []
    for i, token in enumerate(tokens):
        # Apply POS constraint if available (one per token)
        pos_tag = pos_tags[i] if i < len(pos_tags) else None
        cql_token = build_token_cql(token, mode, sensitive, pos_tag)
        cql_parts.append(cql_token)
    
    # Join tokens sequentially (space = sequence in CQL)
    base_cql = " ".join(cql_parts)
    
    return base_cql


def build_cql_with_speaker_filter(params: Dict, filters: Dict) -> str:
    """
    Build CQL pattern with speaker_code and metadata constraints integrated.
    
    Combines base CQL pattern with:
    1. Speaker_code filter (added to each token)
    2. Document metadata filter (added to first token only)
    
    Args:
        params: Request parameters for base CQL (q, mode, sensitive, pos)
        filters: Filter dict from build_filters() (for speaker attributes and metadata)
        
    Returns:
        Complete CQL pattern with speaker + metadata constraints
        Example: '[lemma="casa" & speaker_code="lib-pf" & country_code="ven"]'
    """
    # Defensive: ensure params and filters are not None
    if not params:
        raise ValueError("params cannot be None")
    if filters is None:
        filters = {}
    
    # Build base CQL
    base_cql = build_cql(params)
    
    # Get speaker_code constraint
    speaker_constraint = build_speaker_code_constraint(filters)
    
    # Get metadata constraints (country, radio, city, date)
    metadata_constraint = build_metadata_cql_constraints(filters)
    
    # Use regex to find all [...] token patterns
    import re
    token_pattern = re.compile(r'\[([^\]]+)\]')
    
    # Track if this is the first token (for metadata constraint)
    is_first_token = [True]  # Mutable to modify in nested function
    
    def add_constraints(match):
        existing = match.group(1)
        constraints = [existing]
        
        # Add speaker constraint to every token
        if speaker_constraint:
            constraints.append(speaker_constraint)
        
        # Add metadata constraint to first token only
        if is_first_token[0] and metadata_constraint:
            constraints.append(metadata_constraint)
            is_first_token[0] = False
        
        return f'[{" & ".join(constraints)}]'
    
    modified_cql = token_pattern.sub(add_constraints, base_cql)
    
    logger.info(f"CQL with filters: {modified_cql}")
    return modified_cql


def build_filters(params: Dict) -> Dict[str, any]:
    """
    Build document metadata filters from form parameters.
    
    Filter structure supports multiple values per facet (stored as lists).
    When converted to BlackLab query, facets are OR'd within themselves,
    and all facets are AND'd together.
    
    Args:
        params: Request form data (can have multi-value fields)
            - include_regional: Checkbox to include regional broadcasts (bool)
            - country_scope: 'national' | 'regional' | '' (all)
            - country_parent_code[]: List of parent country codes (e.g., ['ARG', 'ESP'])
            - country_region_code[]: List of region codes (e.g., ['CBA', 'SEV'])
            - country_code[]: LEGACY - List of country codes (e.g., ['ARG', 'CHL'])
            - speaker_type[]: List of speaker types (e.g., ['pro', 'otro'])
            - sex[]: List of sexes (e.g., ['m', 'f'])
            - speech_mode[] or mode[]: List of modes (e.g., ['pre', 'lectura'])
            - discourse[]: List of discourse types
            - city: City name
            - radio: Radio station name
            - date: Date (YYYY-MM-DD)
            
    Returns:
        Dictionary with filter criteria (lists for facets)
        {
            "country_scope": "regional",
            "country_parent_code": ["ARG", "ESP"],
            "country_region_code": ["CBA", "SEV"],
            "speaker_type": ["pro"],
            "sex": ["m", "f"],
            "mode": ["lectura"],
            "discourse": ["general"],
            "city": "Buenos Aires",
            "radio": "Radio Mitre",
            "date": "2023-08-12"
        }
    """
    filters = {}
    
    # Checkbox: Include regional broadcasts (also check "include_regionales" alias)
    include_regional = (
        params.get("include_regional") in ("1", "true", "on", True)
        or params.get("include_regionales") in ("1", "true", "on", True)
    )
    filters["include_regional"] = include_regional
    
    # Country codes: exact whitelist (can be national like ARG or regional like ARG-CBA)
    raw_codes = []
    if hasattr(params, "getlist"):
        raw_codes = params.getlist("country_code")
    else:
        val = params.get("country_code")
        if isinstance(val, list):
            raw_codes = val
        elif isinstance(val, str):
            raw_codes = [val]
    
    filters["country_code"] = [
        c.strip().upper() for c in raw_codes if c and c.strip()
    ]
    
    # Speaker types (multi-select) - no lowercasing
    speaker_types = params.getlist("speaker_type") if hasattr(params, "getlist") else (
        params.get("speaker_type", []) if isinstance(params.get("speaker_type"), list) else 
        ([params.get("speaker_type")] if params.get("speaker_type") else [])
    )
    speaker_types = [s.strip() for s in speaker_types if s and s.strip()]
    if speaker_types:
        filters["speaker_type"] = speaker_types
    
    # Sexes (multi-select) - no lowercasing
    sexes = params.getlist("sex") if hasattr(params, "getlist") else (
        params.get("sex", []) if isinstance(params.get("sex"), list) else 
        ([params.get("sex")] if params.get("sex") else [])
    )
    sexes = [s.strip() for s in sexes if s and s.strip()]
    if sexes:
        filters["sex"] = sexes
    
    # Speech modes: check both 'speech_mode' and 'mode' (UI uses both) - no lowercasing
    modes = params.getlist("speech_mode") if hasattr(params, "getlist") else (
        params.get("speech_mode", []) if isinstance(params.get("speech_mode"), list) else 
        ([params.get("speech_mode")] if params.get("speech_mode") else [])
    )
    # Fallback to 'mode' if speech_mode is empty (but exclude CQL search modes!)
    if not modes:
        mode_param = params.get("mode")
        # Skip if mode is a search mode (forma, lemma, cql, forma_exacta, pos)
        if mode_param and mode_param not in ["forma", "lemma", "cql", "forma_exacta", "pos"]:
            modes = params.getlist("mode") if hasattr(params, "getlist") else (
                [mode_param] if isinstance(mode_param, str) else (mode_param if isinstance(mode_param, list) else [])
            )
    modes = [m.strip() for m in modes if m and m.strip()]
    if modes:
        filters["mode"] = modes
    
    # Discourse types (multi-select) - no lowercasing
    discourses = params.getlist("discourse") if hasattr(params, "getlist") else (
        params.get("discourse", []) if isinstance(params.get("discourse"), list) else 
        ([params.get("discourse")] if params.get("discourse") else [])
    )
    discourses = [d.strip() for d in discourses if d and d.strip()]
    if discourses:
        filters["discourse"] = discourses
    
    # City filter (single value) - no lowercasing
    city = params.get("city", "").strip()
    if city:
        filters["city"] = city
    
    # Radio station filter (single value) - no lowercasing
    radio = params.get("radio", "").strip()
    if radio:
        filters["radio"] = radio
    
    # Date filter (single value)
    date = params.get("date", "").strip()
    if date:
        filters["date"] = date
    
    return filters


def build_metadata_cql_constraints(filters: Dict) -> str:
    """
    Build CQL token constraints for document metadata annotations.
    
    Since metadata is stored as token annotations (repeated on every token),
    we can filter by adding constraints like: country_code="arg" & country_scope="national"
    
    Args:
        filters: Output from build_filters()
        
    Returns:
        CQL constraint string to add to first token pattern
        Example: 'country_scope="regional" & country_parent_code="arg" & country_region_code="cba"'
    """
    if not filters:
        return ""
    
    parts = []
    
    # Country scope (national / regional) - no lowercasing, field is case-insensitive
    country_scope = filters.get("country_scope")
    if country_scope:
        parts.append(f'country_scope="{country_scope}"')
    
    # Country parent codes (multi-select, OR within) - no lowercasing
    country_parent_codes = filters.get("country_parent_code", [])
    if country_parent_codes:
        country_parent_codes = [c for c in country_parent_codes if c and c.strip()]
        if country_parent_codes:
            if len(country_parent_codes) == 1:
                parts.append(f'country_parent_code="{country_parent_codes[0]}"')
            else:
                or_list = '|'.join(country_parent_codes)
                parts.append(f'country_parent_code="({or_list})"')
    
    # Country region codes (multi-select, OR within) - no lowercasing
    country_region_codes = filters.get("country_region_code", [])
    if country_region_codes:
        country_region_codes = [c for c in country_region_codes if c and c.strip()]
        if country_region_codes:
            if len(country_region_codes) == 1:
                parts.append(f'country_region_code="{country_region_codes[0]}"')
            else:
                or_list = '|'.join(country_region_codes)
                parts.append(f'country_region_code="({or_list})"')
    
    # LEGACY: Country codes (for backward compatibility) - no lowercasing
    # This is the full code including region (e.g., 'ARG-CBA')
    country_codes = filters.get("country_code", [])
    if country_codes:
        country_codes = [c for c in country_codes if c and c.strip()]
        if country_codes:
            if len(country_codes) == 1:
                parts.append(f'country_code="{country_codes[0]}"')
            else:
                or_list = '|'.join(country_codes)
                parts.append(f'country_code="({or_list})"')
    
    # Radio filter - no lowercasing (field is case-insensitive in BlackLab)
    radio = filters.get("radio")
    if radio and str(radio).strip():
        # Escape quotes in radio name
        radio_escaped = str(radio).replace('"', '\\"')
        parts.append(f'radio="{radio_escaped}"')
    
    # City filter - no lowercasing (field is case-insensitive in BlackLab)
    city = filters.get("city")
    if city and str(city).strip():
        # Escape quotes in city name
        city_escaped = str(city).replace('"', '\\"')
        parts.append(f'city="{city_escaped}"')
    
    # Date filter
    date = filters.get("date")
    if date and str(date).strip():
        parts.append(f'date="{str(date)}"')
    
    # Join with &
    constraint = " & ".join(parts)
    
    if constraint:
        logger.info(f"Metadata CQL constraints: {constraint}")
    
    return constraint


def filters_to_blacklab_query(filters: Dict) -> str:
    """
    Convert filters dict to BlackLab document filter query string.
    
    NOTE: As of Option A implementation (Nov 2025), document metadata is stored
    as token annotations, not document metadata fields. This function is deprecated
    in favor of build_metadata_cql_constraints() which adds metadata constraints
    directly to the CQL pattern.
    
    Kept for backwards compatibility but returns empty string.
    
    Args:
        filters: Output from build_filters()
        
    Returns:
        Empty string (metadata filtering now handled via CQL annotations)
    """
    # Metadata filtering is now handled via CQL constraints
    # See build_cql_with_metadata_filter() and build_metadata_cql_constraints()
    return ""


def resolve_countries_for_include_regional(countries: Optional[list], include_regional: bool) -> list:
    """
    Resolve countries list by applying include_regional semantics.
    If no countries given: selects national_codes or national+regional based on include_regional.
    If countries given and include_regional=False: excludes regional codes from selection.
    """
    regional_codes = ['ARG-CHU', 'ARG-CBA', 'ARG-SDE', 'ESP-CAN', 'ESP-SEV']
    national_codes = ['ARG', 'BOL', 'CHL', 'COL', 'CRI', 'CUB', 'ECU', 'ESP', 'GTM', 
                      'HND', 'MEX', 'NIC', 'PAN', 'PRY', 'PER', 'DOM', 'SLV', 'URY', 'USA', 'VEN']

    if not countries:
        return national_codes + regional_codes if include_regional else national_codes
    if not include_regional:
        return [c for c in countries if c not in regional_codes]
    return countries



