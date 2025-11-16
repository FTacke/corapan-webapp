"""
Debug-Script: Analyse BlackLab Response und API-Mapping
Vergleicht BlackLab-Rohdaten mit Advanced-API und Corpus-API Ausgaben
"""
import json
import httpx
from pprint import pprint

BLS_URL = "http://localhost:8081/blacklab-server"
ADVANCED_API = "http://localhost:8000/search/advanced/data"
CORPUS_API = "http://localhost:8000/corpus/search/datatables"

def test_blacklab_raw():
    """Teste BlackLab direkt mit lemma=casa"""
    print("="*80)
    print("1. BLACKLAB RAW RESPONSE")
    print("="*80)
    
    params = {
        "patt": '[lemma="casa"]',
        "number": 2,
        "first": 0,
        "wordsaroundhit": 5,
        "listvalues": "word,tokid,start_ms,end_ms,utterance_id"
    }
    
    response = httpx.get(
        f"{BLS_URL}/corpora/corapan/hits",
        params=params,
        headers={"Accept": "application/json"},
        timeout=30.0
    )
    
    data = response.json()
    print(f"\nStatus: {response.status_code}")
    print(f"Total hits: {data.get('summary', {}).get('resultsStats', {}).get('hits', 0)}")
    
    if data.get('hits'):
        print("\nFirst hit structure:")
        hit = data['hits'][0]
        print("\nKeys in hit:", list(hit.keys()))
        print("\nKeys in match:", list(hit.get('match', {}).keys()))
        print("\nMatch values:")
        for k, v in hit.get('match', {}).items():
            print(f"  {k}: {v if not isinstance(v, list) else v[:3]}...")
        
        print("\nBefore values:")
        for k, v in hit.get('before', {}).items():
            print(f"  {k}: {v if not isinstance(v, list) else v[:3]}...")
            
        print("\nMetadata:", hit.get('metadata'))
        
        return hit
    
    return None

def test_advanced_api():
    """Teste Advanced API"""
    print("\n" + "="*80)
    print("2. ADVANCED API RESPONSE")
    print("="*80)
    
    params = {
        "q": "casa",
        "mode": "lemma",
        "length": 2,
        "start": 0,
        "draw": 1
    }
    
    response = httpx.get(ADVANCED_API, params=params, timeout=30.0)
    data = response.json()
    
    print(f"\nStatus: {response.status_code}")
    print(f"Records Total: {data.get('recordsTotal', 0)}")
    
    if data.get('data'):
        print("\nFirst row fields:")
        row = data['data'][0]
        for key, value in row.items():
            if isinstance(value, str) and len(value) > 50:
                print(f"  {key}: {value[:50]}...")
            else:
                print(f"  {key}: {value}")
        
        return row
    
    return None

def test_corpus_api():
    """Teste Corpus/Simple API"""
    print("\n" + "="*80)
    print("3. CORPUS API RESPONSE")
    print("="*80)
    
    params = {
        "query": "casa",
        "search_mode": "lemma_exact",
        "length": 2,
        "start": 0,
        "draw": 1
    }
    
    response = httpx.get(CORPUS_API, params=params, timeout=30.0)
    data = response.json()
    
    print(f"\nStatus: {response.status_code}")
    print(f"Records Total: {data.get('recordsTotal', 0)}")
    
    if data.get('data'):
        print("\nFirst row fields:")
        row = data['data'][0]
        for key, value in row.items():
            if isinstance(value, str) and len(value) > 50:
                print(f"  {key}: {value[:50]}...")
            else:
                print(f"  {key}: {value}")
        
        return row
    
    return None

def compare_schemas(bls_hit, advanced_row, corpus_row):
    """Vergleiche die drei Schemas"""
    print("\n" + "="*80)
    print("4. SCHEMA COMPARISON")
    print("="*80)
    
    print("\n### KANONISCHES ZIELSCHEMA (für Advanced API):")
    print("""
    {
        # KWIC
        "left": str,           # Wortformen aus before['word'], als String
        "match": str,          # Wortformen aus match['word'], als String
        "right": str,          # Wortformen aus after['word'], als String
        
        # Token-Metadaten (aus BlackLab)
        "tokid": str,          # match['tokid'][0]
        "start_ms": int,       # match['start_ms'][0]
        "end_ms": int,         # match['end_ms'][0]
        
        # Dokument-Metadaten (aus docmeta.jsonl lookup via utterance_id)
        "filename": str,       # file_id aus docmeta (z.B. "2022-01-18_VEN_RCR")
        "country": str,        # country_code aus docmeta
        "radio": str,          # radio aus docmeta
        "city": str,           # city aus docmeta
        "date": str,           # date aus docmeta (YYYY-MM-DD)
        
        # Speaker-Metadaten (aktuell nicht in docmeta, später ergänzen)
        "speaker_type": str,   # "" (leer bis Export erweitert wird)
        "sex": str,            # "" (leer bis Export erweitert wird)
        "mode": str,           # "" (leer bis Export erweitert wird)
        "discourse": str,      # "" (leer bis Export erweitert wird)
    }
    """)
    
    print("\n### Corpus API Schema (für Vergleich):")
    if corpus_row:
        print("Feldnamen:")
        for key in corpus_row.keys():
            print(f"  - {key}")
    
    print("\n### Feldmapping-Unterschiede:")
    print("""
    Advanced API              Corpus API               Quelle
    -------------------------------------------------------------------------
    filename                  filename                 docmeta.jsonl: file_id
    country                   country_code             docmeta.jsonl: country_code
    left/match/right          context_left/text/...    BlackLab: before/match/after['word']
    tokid                     token_id                 BlackLab: match['tokid']
    start_ms/end_ms           start/end                BlackLab: match['start_ms']
    """)

if __name__ == "__main__":
    try:
        bls_hit = test_blacklab_raw()
        advanced_row = test_advanced_api()
        corpus_row = test_corpus_api()
        
        compare_schemas(bls_hit, advanced_row, corpus_row)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
