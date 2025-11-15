"""
Speaker Attribute Mapping - Shared utility for consistent speaker_code decoding.

This module provides the canonical mapping from speaker_code (e.g. 'lib-pm', 'lec-pf')
to speaker attributes (speaker_type, sex, mode, discourse).

The mapping is shared across:
- BlackLab index creation (src/scripts/blacklab_index_creation.py)
- Advanced Search API (src/app/search/advanced_api.py)
- CQL Filter building (src/app/search/cql.py)

This ensures consistency across the entire application.
"""
from typing import List


def map_speaker_attributes(code: str) -> tuple[str, str, str, str]:
    """
    Map speaker_code to (speaker_type, sex, mode, discourse) tuple.
    
    Args:
        code: Standardized speaker code (e.g. 'lib-pm', 'foreign', 'none')
    
    Returns:
        Tuple of (speaker_type, sex, mode, discourse)
        
    Speaker codes follow pattern: {role}-{person}{sex}
    - role: lib, lec, pre, tie, traf, foreign
    - person: p (politician/pro), o (other/otro)
    - sex: m (masculino), f (femenino)
    
    Examples:
        >>> map_speaker_attributes('lib-pm')
        ('pro', 'm', 'libre', 'general')
        >>> map_speaker_attributes('lec-pf')
        ('pro', 'f', 'lectura', 'general')
        >>> map_speaker_attributes('foreign')
        ('n/a', 'n/a', 'n/a', 'foreign')
        >>> map_speaker_attributes('unknown')
        ('', '', '', '')
    """
    mapping = {
        'lib-pm':  ('pro', 'm', 'libre', 'general'),
        'lib-pf':  ('pro', 'f', 'libre', 'general'),
        'lib-om':  ('otro', 'm', 'libre', 'general'),
        'lib-of':  ('otro', 'f', 'libre', 'general'),
        'lec-pm':  ('pro', 'm', 'lectura', 'general'),
        'lec-pf':  ('pro', 'f', 'lectura', 'general'),
        'lec-om':  ('otro', 'm', 'lectura', 'general'),
        'lec-of':  ('otro', 'f', 'lectura', 'general'),
        'pre-pm':  ('pro', 'm', 'pre', 'general'),
        'pre-pf':  ('pro', 'f', 'pre', 'general'),
        'tie-pm':  ('pro', 'm', 'n/a', 'tiempo'),
        'tie-pf':  ('pro', 'f', 'n/a', 'tiempo'),
        'traf-pm': ('pro', 'm', 'n/a', 'tránsito'),
        'traf-pf': ('pro', 'f', 'n/a', 'tránsito'),
        'foreign': ('n/a', 'n/a', 'n/a', 'foreign'),
        'none':    ('', '', '', ''),
    }
    return mapping.get(code, ('', '', '', ''))


def get_speaker_codes_for_filters(
    speaker_types: List[str] = None,
    sexes: List[str] = None,
    modes: List[str] = None,
    discourses: List[str] = None
) -> List[str]:
    """
    Reverse mapping: Given speaker attribute filters, return matching speaker_codes.
    
    This is used to convert UI filters (e.g., speaker_type='pro', sex='f')
    into BlackLab speaker_code filters (e.g., 'lib-pf', 'lec-pf', 'pre-pf').
    
    Args:
        speaker_types: List of speaker types (e.g., ['pro', 'otro'])
        sexes: List of sexes (e.g., ['m', 'f'])
        modes: List of modes (e.g., ['libre', 'lectura', 'pre'])
        discourses: List of discourse types (e.g., ['general', 'tiempo'])
    
    Returns:
        List of matching speaker_codes
        
    Example:
        >>> get_speaker_codes_for_filters(speaker_types=['pro'], sexes=['f'])
        ['lib-pf', 'lec-pf', 'pre-pf', 'tie-pf', 'traf-pf']
        >>> get_speaker_codes_for_filters(modes=['libre'], sexes=['m'])
        ['lib-pm', 'lib-om']
    """
    # All possible speaker codes with their attributes
    all_codes = {
        'lib-pm':  ('pro', 'm', 'libre', 'general'),
        'lib-pf':  ('pro', 'f', 'libre', 'general'),
        'lib-om':  ('otro', 'm', 'libre', 'general'),
        'lib-of':  ('otro', 'f', 'libre', 'general'),
        'lec-pm':  ('pro', 'm', 'lectura', 'general'),
        'lec-pf':  ('pro', 'f', 'lectura', 'general'),
        'lec-om':  ('otro', 'm', 'lectura', 'general'),
        'lec-of':  ('otro', 'f', 'lectura', 'general'),
        'pre-pm':  ('pro', 'm', 'pre', 'general'),
        'pre-pf':  ('pro', 'f', 'pre', 'general'),
        'tie-pm':  ('pro', 'm', 'n/a', 'tiempo'),
        'tie-pf':  ('pro', 'f', 'n/a', 'tiempo'),
        'traf-pm': ('pro', 'm', 'n/a', 'tránsito'),
        'traf-pf': ('pro', 'f', 'n/a', 'tránsito'),
        'foreign': ('n/a', 'n/a', 'n/a', 'foreign'),
    }
    
    # Convert None to empty lists
    speaker_types = speaker_types or []
    sexes = sexes or []
    modes = modes or []
    discourses = discourses or []
    
    # If no filters provided, return empty list (no filtering)
    if not any([speaker_types, sexes, modes, discourses]):
        return []
    
    # Filter codes that match ALL provided criteria
    matching_codes = []
    for code, (spk_type, sex, mode, discourse) in all_codes.items():
        # Check each filter (if provided)
        if speaker_types and spk_type not in speaker_types:
            continue
        if sexes and sex not in sexes:
            continue
        if modes and mode not in modes:
            continue
        if discourses and discourse not in discourses:
            continue
        
        # If we get here, all criteria match
        matching_codes.append(code)
    
    return matching_codes
