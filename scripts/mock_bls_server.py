#!/usr/bin/env python3
"""
Mock BlackLab Server for testing proxy.
Provides realistic /blacklab-server/ endpoints.
"""
from flask import Flask, jsonify, request, send_file
from io import BytesIO
import json
import sys

app = Flask(__name__)

# Mock index data
INDEX_DATA = {
    "indexName": "corapan",
    "totalDocuments": 146,
    "totalTokens": 1487120,
    "luceneVersion": "8.11.1",
    "buildDate": "2025-11-10T15:22:47",
    "format": "tsv"
}

@app.route('/blacklab-server/', methods=['GET'])
def server_info():
    """BlackLab server info endpoint"""
    return jsonify({
        "blacklabVersion": "4.0.0",
        "buildDate": "2025-11-10",
        "juavaVersion": "11.0.0",
        "indexDir": "data/blacklab_index"
    }), 200

@app.route('/blacklab-server/corpus/<corpus_name>/', methods=['GET'])
def corpus_info(corpus_name):
    """Corpus info endpoint"""
    if corpus_name != "corapan":
        return jsonify({"error": f"Corpus {corpus_name} not found"}), 404
    
    return jsonify({
        "name": corpus_name,
        "totalDocuments": 146,
        "totalTokens": 1487120,
        "status": "ready",
        "buildDate": "2025-11-10T15:22:47"
    }), 200

@app.route('/blacklab-server/<corpus_name>/hits', methods=['GET'])
def search_hits(corpus_name):
    """CQL search endpoint with filter support"""
    if corpus_name != "corapan":
        return jsonify({"error": f"Corpus {corpus_name} not found"}), 404
    
    # Try multiple CQL parameter names (patt, cql, cql_query)
    cql_pattern = request.args.get('patt') or request.args.get('cql') or request.args.get('cql_query', '[word="test"]')
    
    # Extract pagination
    first = int(request.args.get('first', 0))
    number = int(request.args.get('number', 50))
    
    # Extract filter (if present)
    filter_query = request.args.get('filter', '')
    
    # Simulate filter effectiveness
    total_docs = 146
    total_hits = 1487
    
    # If filter is present, reduce counts (simulate filtering)
    if filter_query:
        total_docs = 42  # Filtered down
        total_hits = 324  # Fewer hits
        docs_retrieved = 42
    else:
        docs_retrieved = 146  # All docs
    
    # Mock search results
    hits = [
        {
            "docPid": "ARG_20200315_LRA1_NOTICIAS_010",
            "start": 142,
            "end": 143,
            "left": {"word": ["en", "el", "país"], "lemma": ["en", "el", "país"], "pos": ["ADP", "DET", "NOUN"]},
            "match": {"word": ["México"], "lemma": ["méxico"], "pos": ["PROPN"]},
            "right": {"word": ["y", "en", "otros"], "lemma": ["y", "en", "otro"], "pos": ["CCONJ", "ADP", "DET"]},
            "tokid": ["ARG_20200315_LRA1_NOTICIAS_010_142"],
            "start_ms": [15234],
            "end_ms": [15567],
            "sentence_id": ["s12"],
            "utterance_id": ["u5"]
        },
        {
            "docPid": "MEX_20200420_XEQK_CULTURA_045",
            "start": 89,
            "end": 90,
            "left": {"word": ["hacia", "el", "sur"], "lemma": ["hacia", "el", "sur"], "pos": ["ADP", "DET", "NOUN"]},
            "match": {"word": ["mexico"], "lemma": ["méxico"], "pos": ["PROPN"]},
            "right": {"word": ["para", "ver", "las"], "lemma": ["para", "ver", "el"], "pos": ["ADP", "VERB", "DET"]},
            "tokid": ["MEX_20200420_XEQK_CULTURA_045_89"],
            "start_ms": [23456],
            "end_ms": [23789],
            "sentence_id": ["s8"],
            "utterance_id": ["u3"]
        }
    ]
    
    # Pagination
    paginated_hits = hits[first:first+number]
    
    return jsonify({
        "summary": {
            "searchParam": {
                "patt": cql_pattern,
                "filter": filter_query,
                "first": first,
                "number": number
            },
            "searchTime": 234,
            "countTime": 45,
            "numberOfHits": total_hits,
            "numberOfDocs": total_docs,
            "docsRetrieved": docs_retrieved,  # Key for filter detection
            "numberOfHitsRetrieved": len(paginated_hits),
            "stoppedCountingHits": False,
            "stoppedRetrievingHits": False
        },
        "hits": paginated_hits,
        "docInfos": {
            "ARG_20200315_LRA1_NOTICIAS_010": {
                "lengthInTokens": 5432,
                "mayView": True
            },
            "MEX_20200420_XEQK_CULTURA_045": {
                "lengthInTokens": 6789,
                "mayView": True
            }
        }
    }), 200

@app.route('/blacklab-server/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def catch_all(subpath):
    """Catch remaining endpoints"""
    return jsonify({
        "status": "ok",
        "endpoint": f"/{subpath}",
        "method": request.method,
        "message": "BlackLab Server mock endpoint"
    }), 200

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    print(f"[MockBLS] Starting BlackLab Server mock on http://localhost:{port}")
    app.run(host='localhost', port=port, debug=False, threaded=True)
