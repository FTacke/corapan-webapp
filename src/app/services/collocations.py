"""
Service for calculating collocations from BlackLab hits.
"""

import logging
from collections import Counter
from typing import Dict

import httpx

from ..extensions.http_client import get_http_client, BLS_BASE_URL

logger = logging.getLogger(__name__)


def get_collocations(
    cql: str, window_size: int = 5, subcorpus_filter: str = ""
) -> Dict:
    """
    Get collocations for a given CQL query.

    Args:
        cql: The CQL query to find collocations for.
        window_size: The number of words to the left and right of the hit to consider.
        subcorpus_filter: A filter to apply to the search.

    Returns:
        A dictionary containing collocation statistics.
    """
    client = get_http_client()
    colloc_params = {
        "patt": cql,
        "wordsaroundhit": window_size,
        "number": 1000,  # Get a good sample of hits
    }
    if subcorpus_filter:
        colloc_params["filter"] = subcorpus_filter

    try:
        # Use the /hits endpoint to get words around the hit
        response = client.get(
            f"{BLS_BASE_URL}/corpora/corapan/hits", params=colloc_params
        )
        response.raise_for_status()
        data = response.json()

        hits = data.get("hits", [])
        left_words = Counter()
        right_words = Counter()

        for hit in hits:
            left_context = hit.get("left", {}).get("word", [])
            right_context = hit.get("right", {}).get("word", [])

            left_words.update(left_context)
            right_words.update(right_context)

        total_left = sum(left_words.values())
        total_right = sum(right_words.values())

        return {
            "left": [
                {"word": word, "n": count, "p": count / total_left if total_left else 0}
                for word, count in left_words.most_common(20)
            ],
            "right": [
                {
                    "word": word,
                    "n": count,
                    "p": count / total_right if total_right else 0,
                }
                for word, count in right_words.most_common(20)
            ],
            "total_hits": data.get("summary", {})
            .get("resultsStats", {})
            .get("hits", 0),
        }

    except httpx.HTTPStatusError as e:
        logger.error(
            f"BlackLab error fetching collocations: {e.response.status_code} - {e.response.text}"
        )
        return {
            "error": "bls_error",
            "message": f"BlackLab error: {e.response.status_code}",
        }
    except Exception as e:
        logger.exception("Error fetching collocations")
        return {"error": "server_error", "message": str(e)}
