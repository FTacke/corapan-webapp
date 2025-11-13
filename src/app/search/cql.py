"""
CQL (Corpus Query Language) Builder for BlackLab searches.

Constructs CQL patterns from user input (form data) and builds
document filters for metadata-based filtering.
"""
import re
from typing import Dict, List, Optional


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
    constraints = [f'{field}="{value}"']
    
    # POS constraint (optional) - only add if not already a POS search
    if pos and mode != "pos":
        constraints.append(f'pos="{escape_cql(pos)}"')
    
    # Combine with &
    constraint_str = " & ".join(constraints)
    return f"[{constraint_str}]"


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
    # Query: try both 'q' and 'query'
    query = params.get("q") or params.get("query", "")
    query = query.strip() if query else ""
    
    if not query:
        raise ValueError("Query cannot be empty")
    
    mode = params.get("mode", "forma")
    
    # Parse sensitive flag
    # sensitive can be string ('0', '1', 'true', 'false') or bool
    sensitive_raw = params.get("sensitive", "1")
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
    return " ".join(cql_parts)


def build_filters(params: Dict) -> Dict[str, any]:
    """
    Build document metadata filters from form parameters.
    
    Filter structure supports multiple values per facet (stored as lists).
    When converted to BlackLab query, facets are OR'd within themselves,
    and all facets are AND'd together.
    
    Args:
        params: Request form data (can have multi-value fields)
            - country_code[]: List of country codes (e.g., ['ARG', 'CHL'])
            - speaker_type[]: List of speaker types (e.g., ['pro', 'otro'])
            - sex[]: List of sexes (e.g., ['m', 'f'])
            - speech_mode[] or mode[]: List of modes (e.g., ['pre', 'lectura'])
            - discourse[]: List of discourse types
            - include_regional: bool, if False add radio:"national"
            
    Returns:
        Dictionary with filter criteria (lists for facets)
        {
            "country_code": ["ARG", "CHL"],
            "speaker_type": ["pro"],
            "sex": ["m", "f"],
            "mode": ["lectura"],
            "discourse": ["general"],
            "radio": "national"  # Only set if include_regional=False
        }
    """
    filters = {}
    
    # Country codes (multi-select)
    country_codes = params.getlist("country_code") if hasattr(params, "getlist") else (
        params.get("country_code", []) if isinstance(params.get("country_code"), list) else 
        ([params.get("country_code")] if params.get("country_code") else [])
    )
    country_codes = [c.strip().upper() for c in country_codes if c and c.strip()]
    if country_codes:
        filters["country_code"] = country_codes
    
    # Speaker types (multi-select)
    speaker_types = params.getlist("speaker_type") if hasattr(params, "getlist") else (
        params.get("speaker_type", []) if isinstance(params.get("speaker_type"), list) else 
        ([params.get("speaker_type")] if params.get("speaker_type") else [])
    )
    speaker_types = [s.strip() for s in speaker_types if s and s.strip()]
    if speaker_types:
        filters["speaker_type"] = speaker_types
    
    # Sexes (multi-select)
    sexes = params.getlist("sex") if hasattr(params, "getlist") else (
        params.get("sex", []) if isinstance(params.get("sex"), list) else 
        ([params.get("sex")] if params.get("sex") else [])
    )
    sexes = [s.strip() for s in sexes if s and s.strip()]
    if sexes:
        filters["sex"] = sexes
    
    # Speech modes: check both 'speech_mode' and 'mode' (UI uses both)
    modes = params.getlist("speech_mode") if hasattr(params, "getlist") else (
        params.get("speech_mode", []) if isinstance(params.get("speech_mode"), list) else 
        ([params.get("speech_mode")] if params.get("speech_mode") else [])
    )
    # Fallback to 'mode' if speech_mode is empty (but exclude CQL search mode!)
    if not modes:
        mode_param = params.get("mode")
        # Skip if mode is a search mode (forma, lemma, cql, forma_exacta)
        if mode_param and mode_param not in ["forma", "lemma", "cql", "forma_exacta"]:
            modes = params.getlist("mode") if hasattr(params, "getlist") else (
                [mode_param] if isinstance(mode_param, str) else (mode_param if isinstance(mode_param, list) else [])
            )
    modes = [m.strip() for m in modes if m and m.strip()]
    if modes:
        filters["mode"] = modes
    
    # Discourse types (multi-select)
    discourses = params.getlist("discourse") if hasattr(params, "getlist") else (
        params.get("discourse", []) if isinstance(params.get("discourse"), list) else 
        ([params.get("discourse")] if params.get("discourse") else [])
    )
    discourses = [d.strip() for d in discourses if d and d.strip()]
    if discourses:
        filters["discourse"] = discourses
    
    # Radio filter: set to "national" if include_regional is explicitly set to False
    # Default: include all (regional + national) if parameter is not provided
    include_regional = params.get("include_regional")
    if include_regional in ("0", "false", False):
        filters["radio"] = "national"
    
    return filters


def filters_to_blacklab_query(filters: Dict) -> str:
    """
    Convert filters dict to BlackLab filter query string.
    
    Logic:
    - Within a facet (e.g., country_code list): OR'd together
    - Between facets: AND'd together
    - radio:"national" is AND'd with other filters
    
    Example:
        filters = {
            "country_code": ["ARG", "CHL"],
            "speaker_type": ["pro"],
            "mode": ["lectura"],
            "radio": "national"
        }
    Produces:
        country_code:("ARG" OR "CHL") AND speaker_type:("pro") AND mode:("lectura") AND radio:"national"
    
    Args:
        filters: Output from build_filters()
        
    Returns:
        Filter string for BlackLab 'filter' parameter (empty if no filters)
    """
    if not filters:
        return ""
    
    parts = []
    
    # Country codes: OR'd within, quoted
    if "country_code" in filters:
        codes = filters["country_code"]
        if len(codes) == 1:
            parts.append(f'country_code:"{codes[0]}"')
        else:
            or_list = ' OR '.join(f'"{c}"' for c in codes)
            parts.append(f'country_code:({or_list})')
    
    # Speaker types: OR'd within
    if "speaker_type" in filters:
        types = filters["speaker_type"]
        if len(types) == 1:
            parts.append(f'speaker_type:"{types[0]}"')
        else:
            or_list = ' OR '.join(f'"{t}"' for t in types)
            parts.append(f'speaker_type:({or_list})')
    
    # Sex: OR'd within
    if "sex" in filters:
        sexes = filters["sex"]
        if len(sexes) == 1:
            parts.append(f'sex:"{sexes[0]}"')
        else:
            or_list = ' OR '.join(f'"{s}"' for s in sexes)
            parts.append(f'sex:({or_list})')
    
    # Mode (speech_mode): OR'd within
    if "mode" in filters:
        modes = filters["mode"]
        if len(modes) == 1:
            parts.append(f'mode:"{modes[0]}"')
        else:
            or_list = ' OR '.join(f'"{m}"' for m in modes)
            parts.append(f'mode:({or_list})')
    
    # Discourse: OR'd within
    if "discourse" in filters:
        discourses = filters["discourse"]
        if len(discourses) == 1:
            parts.append(f'discourse:"{discourses[0]}"')
        else:
            or_list = ' OR '.join(f'"{d}"' for d in discourses)
            parts.append(f'discourse:({or_list})')
    
    # Radio: special case (single value)
    if "radio" in filters:
        parts.append(f'radio:"{filters["radio"]}"')
    
    # Combine all parts with AND
    return " AND ".join(parts)
